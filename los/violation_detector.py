import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import subprocess
import os
import cv2
from fpdf import FPDF

DETECTION_SCRIPT_PATH = os.path.abspath("violationrun.py")

class DetectionThread(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(str, str, str, str, str)
    error = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            result = subprocess.run(
                [sys.executable, DETECTION_SCRIPT_PATH, self.video_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self.error.emit(result.stderr)
                return
            for line in result.stdout.splitlines():
                if line.startswith("RESULT::"):
                    parts = line.strip().split("::")
                    if len(parts) == 6:
                        _, plate_number, image_path, violation_type, timestamp, vehicle_type = parts
                        self.done.emit(plate_number, image_path, violation_type, timestamp, vehicle_type)
                        return
            self.error.emit("No plate number found in detection output.")
        except Exception as e:
            self.error.emit(str(e))


class ViolationGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("[REVO] Srilanka Vehicle Violation Detector")
        self.setFixedSize(550, 700)
        self.setStyleSheet("background-color: #f9f9f9; font-size: 16px;")

        self.layout = QVBoxLayout()

        self.info_label = QLabel("Choose a video to start violation detection:")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        self.choose_button = QPushButton("📂 Choose Video")
        self.choose_button.clicked.connect(self.choose_video)
        self.choose_button.setStyleSheet("padding: 8px; font-weight: bold;")
        self.layout.addWidget(self.choose_button)

        self.detect_button = QPushButton("🚦 Run Violation Detection")
        self.detect_button.clicked.connect(self.run_detection)
        self.choose_button.setStyleSheet("padding: 8px; font-weight: bold;")
        self.detect_button.setEnabled(False)
        self.layout.addWidget(self.detect_button)

        self.progress_label = QLabel("")
        self.layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.layout.addWidget(self.result_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        self.pdf_button = QPushButton("📄 Download PDF Summary")
        self.choose_button.setStyleSheet("padding: 9px; font-weight: bold;")
        self.pdf_button.clicked.connect(self.generate_pdf)
        self.pdf_button.setEnabled(False)
        self.layout.addWidget(self.pdf_button)

        self.setLayout(self.layout)
        self.video_path = None
        self.detection_data = None

    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi)")
        if file_path:
            self.video_path = file_path
            self.detect_button.setEnabled(True)
            self.pdf_button.setEnabled(False)
            self.result_label.clear()
            self.image_label.clear()
            self.progress_bar.setValue(0)
            self.progress_label.setText("Video Uploaded / Run Violation Detection.")

    def run_detection(self):
        if self.video_path:
            self.progress_label.setText("Detection Progress....")
            self.progress_bar.setRange(0, 0)
            self.thread = DetectionThread(self.video_path)
            self.thread.progress.connect(self.update_progress)
            self.thread.done.connect(self.show_result)
            self.thread.error.connect(self.show_error)
            self.thread.start()

    def update_progress(self, message):
        self.progress_label.setText(message)

    def show_result(self, plate_number, image_path, violation_type, timestamp, vehicle_type):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.progress_label.setText("Detection complete.")

        self.detection_data = (plate_number, image_path, violation_type, timestamp, vehicle_type)
        self.pdf_button.setEnabled(True)

        result_html = f"""
        <b>🚔 Plate Number:</b> {plate_number}<br>
        <b>🚨 Violation:</b> {violation_type}<br>
        <b>⏱️ Time:</b> {timestamp}<br>
        <b>🚗 Vehicle Type:</b> {vehicle_type}<br>
        <b>📧 Email Status:</b> Sent to Owner!
        """
        self.result_label.setText(result_html)
        self.result_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #222;")

        pixmap = QPixmap(image_path).scaled(300, 200, Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def show_error(self, error_msg):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Error occurred.")
        QMessageBox.critical(self, "Error", error_msg)

    def generate_pdf(self):
        if not self.detection_data:
            return

        plate_number, image_path, violation_type, timestamp, vehicle_type = self.detection_data
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

        if os.path.exists(image_path):
            pdf.image(image_path, w=150)

        save_path = QFileDialog.getSaveFileName(self, "Save PDF", f"violation_report_{plate_number}.pdf", "PDF Files (*.pdf)")[0]
        if save_path:
            pdf.output(save_path)
            QMessageBox.information(self, "PDF Saved", "Report Saved Successfully!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ViolationGUI()
    window.show()
    sys.exit(app.exec_())
