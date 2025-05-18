from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
import subprocess
import uuid
from fpdf import FPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
CROPPED_FOLDER = 'cropped_violations'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPPED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video uploaded'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    video_file.save(filepath)

    result = subprocess.run(
        ['python', 'violationrun.py', filepath],
        capture_output=True, text=True
    )

    output = result.stdout
    for line in output.splitlines():
        if line.startswith("RESULT::"):
            parts = line.strip().split("::")
            if len(parts) == 6:
                _, plate_number, image_filename, violation_type, timestamp, vehicle_type = parts
                return jsonify({
                    'plate_number': plate_number,
                    'image_path': image_filename,  # only filename now
                    'violation_type': violation_type,
                    'timestamp': timestamp,
                    'vehicle_type': vehicle_type
                })

    return jsonify({'error': 'No violation detected.'}), 200

@app.route('/cropped_violations/<path:filename>')
def serve_image(filename):
    return send_from_directory(CROPPED_FOLDER, filename)

@app.route('/download-pdf')
def download_pdf():
    plate_number = request.args.get("plate")
    image_filename = request.args.get("image")
    violation_type = request.args.get("violation")
    timestamp = request.args.get("time")
    vehicle_type = request.args.get("vehicle")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Vehicle Violation Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Plate Number: {plate_number}", ln=True)
    pdf.cell(0, 10, f"Violation: {violation_type}", ln=True)
    pdf.cell(0, 10, f"Time: {timestamp}", ln=True)
    pdf.cell(0, 10, f"Vehicle Type: {vehicle_type}", ln=True)
    pdf.cell(0, 10, f"Email Sent: Yes", ln=True)

    image_path = os.path.join(CROPPED_FOLDER, image_filename)
    if os.path.exists(image_path):
        pdf.image(image_path, w=150)

    pdf_path = os.path.join(UPLOAD_FOLDER, f"report_{plate_number}.pdf")
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
