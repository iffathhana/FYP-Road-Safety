import hydra
import torch
import easyocr
import cv2
import sys
import mysql.connector
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from ultralytics.yolo.engine.predictor import BasePredictor
from ultralytics.yolo.utils import DEFAULT_CONFIG, ops
from ultralytics.yolo.utils.checks import check_imgsz
from ultralytics.yolo.utils.plotting import Annotator, colors, save_one_box

# Global variable to pass source from CLI
custom_source = None
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg.startswith("source="):
            custom_source = arg.split("=", 1)[1]


def get_violation_type():
    try:
        with open("violation_type.txt", "r") as f:
            return f.read().strip()
    except:
        return "General Violation"

def get_fine_amount(violation_type):
    fines = {
        "No Parking": 2000,
        "Accident Violation": 1000,
        "One Way Violation": 1500,
        "General Violation": 500
    }
    return fines.get(violation_type, 500)


#mail sending part
detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def send_email(to_email, plate_number, violation_type, detection_time, fine_amount):
    try:
        sender_email = "info.trafficgovsl@gmail.com"
        sender_password = "ggdg qula nzwx njka"

        subject = "[TEST]Vehicle Number Plate Detection."
        body = f"""Vehicle Owner,
        
            Your vehicle with number plate://{plate_number} // has been found involved in a violation:
           // Violation Type: {violation_type} 
           // Fine Amount: Rs. {fine_amount}
           // location: Colombo-11
           // Detection Time: {detection_time}
           
           Please pay the fine [USE REVO] within 14 days to avoid further penalties.
  
           Regards,
                            -- Srilanka, Government Traffic Authority--
        """

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
    except Exception as e:
        print("Email sending error:", e)

# Insert into database and send email
def insert_to_database(plate):
    violation_type = get_violation_type()
    fine_amount = get_fine_amount(violation_type)
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            port=3306,
            password="16471",
            database="dev"
        )
        cursor = conn.cursor()
        image = "No image"
        sql = "INSERT INTO number_plates (plate_number, image_path, violation_type, fine) VALUES (%s,%s,%s,%s)"
        cursor.execute(sql, (plate,image, violation_type, fine_amount))
        conn.commit()

        # Fetch associated email
        email_query = """
            SELECT u.Email
            FROM vehicle v
            JOIN user u ON v.user_id = u.user_id
            WHERE v.Vehicle_no = %s
        """
        cursor.execute(email_query, (plate,))
        result = cursor.fetchone()

        if result:
            email = result[0]
            detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_email(email, plate,violation_type,detection_time,fine_amount)

        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print("MySQL Error:", err)


def getOCR(im, coors):
    x, y, w, h = int(coors[0]), int(coors[1]), int(coors[2]), int(coors[3])
    im = im[y:h, x:w]
    conf = 0.2

    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    results = reader.readtext(gray)
    ocr = ""

    for result in results:
        if len(results) == 1:
            ocr = result[1]
        if len(results) > 1 and len(result[1]) > 6 and result[2] > conf:
            ocr = result[1]

    return str(ocr)


class DetectionPredictor(BasePredictor):
    def get_annotator(self, img):
        return Annotator(img, line_width=self.args.line_thickness, example=str(self.model.names))

    def preprocess(self, img):
        img = torch.from_numpy(img).to(self.model.device)
        img = img.half() if self.model.fp16 else img.float()
        img /= 255
        return img

    def postprocess(self, preds, img, orig_img):
        preds = ops.non_max_suppression(preds,
                                        self.args.conf,
                                        self.args.iou,
                                        agnostic=self.args.agnostic_nms,
                                        max_det=self.args.max_det)

        for i, pred in enumerate(preds):
            shape = orig_img[i].shape if self.webcam else orig_img.shape
            pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], shape).round()

        return preds

    def write_results(self, idx, preds, batch):
        p, im, im0 = batch
        log_string = ""
        if len(im.shape) == 3:
            im = im[None]
        self.seen += 1
        im0 = im0.copy()
        if self.webcam:
            log_string += f'{idx}: '
            frame = self.dataset.count
        else:
            frame = getattr(self.dataset, 'frame', 0)

        self.data_path = p
        self.txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')
        log_string += '%gx%g ' % im.shape[2:]
        self.annotator = self.get_annotator(im0)

        det = preds[idx]
        self.all_outputs.append(det)
        if len(det) == 0:
            return log_string
        for c in det[:, 5].unique():
            n = (det[:, 5] == c).sum()
            log_string += f"{n} {self.model.names[int(c)]}{'s' * (n > 1)}, "
        gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
        for *xyxy, conf, cls in reversed(det):
            if self.args.save_txt:
                xywh = (ops.xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()
                line = (cls, *xywh, conf) if self.args.save_conf else (cls, *xywh)
                with open(f'{self.txt_path}.txt', 'a') as f:
                    f.write(('%g ' * len(line)).rstrip() % line + '\n')

            if self.args.save or self.args.save_crop or self.args.show:
                c = int(cls)
                label = None if self.args.hide_labels else (
                    self.model.names[c] if self.args.hide_conf else f'{self.model.names[c]} {conf:.2f}')
                ocr = getOCR(im0, xyxy)
                if ocr != "":
                    label = ocr
                    with open("ocr_output.txt", "a") as f:
                        f.write(ocr + "\n")
                    insert_to_database(ocr)
                self.annotator.box_label(xyxy, label, color=colors(c, True))
            if self.args.save_crop:
                imc = im0.copy()
                save_one_box(xyxy,
                             imc,
                             file=self.save_dir / 'crops' / self.model.model.names[c] / f'{self.data_path.stem}.jpg',
                             BGR=True)

        return log_string


@hydra.main(version_base=None, config_path=str(DEFAULT_CONFIG.parent), config_name=DEFAULT_CONFIG.name)
def predict(cfg):
    open("ocr_output.txt", "w").close()
    cfg.model = cfg.model or "yolov8n.pt"
    cfg.imgsz = check_imgsz(cfg.imgsz, min_dim=2)

    if custom_source:  # apply dynamic file input
        cfg.source = custom_source

    predictor = DetectionPredictor(cfg)
    predictor()


if __name__ == "__main__":
    reader = easyocr.Reader(['en'])
    predict()