from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    violation_type = request.form.get("violation_type", "General Violation")

    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Remove old OCR results
        if os.path.exists("ocr_output.txt"):
            os.remove("ocr_output.txt")

        with open("violation_type.txt", "w") as f:
            f.write(violation_type)

        # Run detection
        subprocess.run(["python", "predictWithOCR.py", f"source={filepath}"])

        # Read results
        result_text = ""
        if os.path.exists("ocr_output.txt"):
            with open("ocr_output.txt", "r") as f:
                result_text = f.read()

        return jsonify({"output": result_text})
    return jsonify({"error": "No file uploaded"}), 400

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5008, debug=False)

