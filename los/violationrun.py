import cv2
from ultralytics import YOLO
import os
import easyocr
import pymysql
from datetime import datetime
import re
import numpy as np
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

VIDEO_PATH = 'F:/fyp final project files all/Untitled video - Made with Clipchamp.mp4'
if len(sys.argv) > 1:
    VIDEO_PATH = sys.argv[1]

VIOLATION_MODEL_PATH = 'F:/fyp final project files all/training datasets/yolo_new_training-20250417T182034Z-001/yolo_new_training/road_violation_yolov8/weights/best.pt'
PLATE_MODEL_PATH = 'F:/projects extra/numberplatedetect/numberplatedetect/numberplate/YOLOv8/runs/detect/train/weights/best.pt'
SAVE_DIR = 'cropped_violations'
DEBUG_DIR = 'debug_frames'

THREEWHEEL_CLASS_ID = 7
VIOLATION_CLASS_ID = 9
CONFIDENCE_THRESHOLD = 0.3
MAX_FRAMES = 15000


try:
    db = pymysql.connect(
        host="localhost",
        user="root",
        port=3306,
        password="16471",
        database="dev"
    )
    cursor = db.cursor()
    print(" Connected to MySQL.")
except pymysql.MySQLError as err:
    print(f" DB Error: {err}")
    exit(1)


violation_model = YOLO(VIOLATION_MODEL_PATH)
plate_model = YOLO(PLATE_MODEL_PATH)
ocr_reader = easyocr.Reader(['en'], gpu=False)

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_PATH)
frame_count = 0
violation_saved = False
plate_number = None
crop_path = None

detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def crop_and_ocr(plate_img, crop_path_):
    global plate_number
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

    height = 100
    scale_ratio = height / gray.shape[0]
    gray = cv2.resize(gray, (int(gray.shape[1] * scale_ratio), height))

    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    sharpen_kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
    sharpened = cv2.filter2D(filtered, -1, sharpen_kernel)
    thresh = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    ocr_result = ocr_reader.readtext(thresh, detail=0, decoder='greedy')
    print(f"5:OCR Raw Result: {ocr_result}")

    full_text = "".join([text.strip().upper() for text in ocr_result if text.strip()])
    plate_pattern = re.compile(r'[A-Z]{2,3}[A-Z]{2,3}[0-9]{3,5}')
    match = plate_pattern.search(full_text)

    if match:
        plate_number = match.group()[-7:].upper()
        print(f"6:Plate Detected: {plate_number}")
        try:
            fine_amount = 1500
            violation_type = "Double Line Violation"
            cursor.execute(
                "INSERT INTO number_plates (plate_number, image_path, violation_type, fine) VALUES (%s, %s, %s, %s)",
                (plate_number, crop_path_, violation_type, fine_amount)
            )
            db.commit()
            print("7:Inserted into DB.")
            email_query = """
                            SELECT u.Email
                            FROM vehicle v
                            JOIN user u ON v.user_id = u.user_id
                            WHERE v.Vehicle_no = %s
                        """
            cursor.execute(email_query, (plate_number,))
            result = cursor.fetchone()
            if result:
                owner_email = result[0]
                print(f"8:Owner's email found: {owner_email}")
                send_email_to_owner(owner_email, plate_number, crop_path_, detection_time, violation_type, fine_amount)

        except Exception as e:
            print(f" DB Insert Error: {e}")
        return True
    else:
         print(" No OCR match.")
         return False


def send_email_to_owner(owner_email, plate_number, crop_path_, detection_time, violation_type, fine_amount):
    sender_email = "info.trafficgovsl@gmail.com"
    sender_password = "ggdg qula nzwx njka"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "[TEST] Violation Detected: Traffic Rule Violation Notification"
    body = f"""Vehicle Owner,

            Your vehicle with license plate number // {plate_number}// has been detected violating a traffic rule.
            Please find the violation details and the corresponding image attached.
            
           // Detection Time: {detection_time}
           // Violation Type: {violation_type}
           // Fine Amount: {fine_amount}/=
           // Violation Image: {crop_path_}
           
           ***Please pay the fine [USE REVO] within 14 days to avoid further penalties.***
           
           Regards,
           -- Srilanka, Government Traffic Authority-- 
        """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = owner_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with open(crop_path_, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(crop_path_)}",
            )
            msg.attach(part)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, owner_email, msg.as_string())
        server.quit()
        print(f"9:Email sent to {owner_email}")
    except Exception as e:
        print(f"Email sending failed: {e}")

while cap.isOpened() and frame_count < MAX_FRAMES:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    print(f"\n Frame {frame_count}: Running detection...")
    results = violation_model(frame)[0]
    boxes = results.boxes

    threewheels = [box for box in boxes if int(box.cls.item()) == THREEWHEEL_CLASS_ID and float(box.conf.item()) > CONFIDENCE_THRESHOLD]
    violations = [box for box in boxes if int(box.cls.item()) == VIOLATION_CLASS_ID and float(box.conf.item()) > CONFIDENCE_THRESHOLD]

    if not threewheels or not violations:
        continue

    for tw_box in threewheels:
        x1, y1, x2, y2 = map(int, tw_box.xyxy[0])
        tw_crop = frame[y1:y2, x1:x2]

        for v_box in violations:
            vx1, vy1, vx2, vy2 = map(int, v_box.xyxy[0])
            inter_x1 = max(x1, vx1)
            inter_y1 = max(y1, vy1)
            inter_x2 = min(x2, vx2)
            inter_y2 = min(y2, vy2)

            if inter_x1 < inter_x2 and inter_y1 < inter_y2:
                plate_results = plate_model(tw_crop)[0]
                plate_boxes = [b for b in plate_results.boxes if float(b.conf.item()) > 0.3]

                if plate_boxes:
                    px1, py1, px2, py2 = map(int, plate_boxes[0].xyxy[0])
                    plate_crop = tw_crop[py1:py2, px1:px2]
                else:
                    plate_crop = tw_crop

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                crop_filename = f"frame{frame_count}_{timestamp}_threewheel.jpg"
                crop_path = os.path.join(SAVE_DIR, crop_filename)
                cv2.imwrite(crop_path, plate_crop)

                if crop_and_ocr(plate_crop, crop_path):
                    violation_saved = True
                    break

        if violation_saved:
            break

    if violation_saved:
        break

cap.release()
cursor.close()
db.close()

if violation_saved and plate_number and crop_path:
    violation_type = "Double Line Violation"
    vehicle_type = "Three-wheeler"
    detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"RESULT::{plate_number}::{os.path.basename(crop_path)}::{violation_type}::{detection_time}::{vehicle_type}")

print(" Done: Violation processed and database saved.")
