import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from PIL import Image, ImageTk
import subprocess
import sys
import os

def save_violation_type():
    violation_type = violation_type_var.get()
    with open("violation_type.txt", "w") as f:
        f.write(violation_type)

def run_detection(file_path):
    # Clear previous results
    if os.path.exists("ocr_output.txt"):
        os.remove("ocr_output.txt")

    save_violation_type()

    # Run YOLO + OCR subprocess
    command = [sys.executable, "predictWithOCR.py", f"source={file_path}"]
    subprocess.run(command, check=True)

    # Read OCR results and show in GUI
    if os.path.exists("ocr_output.txt"):
        with open("ocr_output.txt", "r") as f:
            content = f.read().strip()

        result_box.config(state='normal')
        result_box.delete("1.0", tk.END)
        if content:
            result_box.insert(tk.END, content)
        else:
            result_box.insert(tk.END, "No number plates detected.")
        result_box.config(state='disabled')

def open_file():
    filetypes = (
        ("Video files", "*.mp4 *.avi"),
        ("Image files", "*.jpg *.jpeg *.png"),
        ("All files", "*.*")
    )
    file_path = filedialog.askopenfilename(title="Select image or video", filetypes=filetypes)
    if file_path:
        run_detection(file_path)

# GUI Setup
root = tk.Tk()
root.title("[REVO] SYSTEM")
root.geometry("800x600")
root.config(bg="#1E1E1E")

# Load background image
background_image = Image.open("Background.png")
background_image = background_image.resize((800, 600))
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=background_photo)
background_label.place(relwidth=1, relheight=1)

# Topic
topic_label = tk.Label(root, text="Vehicle & Violation Detection",
                       font=("Helvetica", 24, "bold"), bg="#1E1E1E", fg="white")
topic_label.place(relx=0.5, rely=0.08, anchor="center")

# Upload button
upload_button = tk.Button(root, text="Upload Image or Video",
                          command=open_file, font=("Helvetica", 16, "bold"),
                          bg="black", fg="white", relief="raised", bd=5, width=25)
upload_button.place(relx=0.5, rely=0.22, anchor="center")

# Violation Type Dropdown
violation_type_var = tk.StringVar()
violation_type_dropdown = ttk.Combobox(root, textvariable=violation_type_var, state="readonly",
                                       font=("Helvetica", 14), width=30)
violation_type_dropdown['values'] = ("No Parking", "Accident Violation", "One Way Violation", "General Violation")
violation_type_dropdown.current(3)  # Default to "General Violation"
violation_type_dropdown.place(relx=0.5, rely=0.32, anchor="center")

# Label
results_label = tk.Label(root, text="Detected Number Plates:",
                         font=("Helvetica", 16), bg="#1E1E1E", fg="white")
results_label.place(relx=0.5, rely=0.41, anchor="center")

# Scrollable Text Box
result_box = scrolledtext.ScrolledText(root, width=60, height=10,
                                       font=("Courier", 15), wrap=tk.WORD,
                                       bg="black", fg="lime", insertbackground='white')
result_box.place(relx=0.5, rely=0.63, anchor="center")
result_box.config(state='disabled')

# Footer
footer_label = tk.Label(root, text="Group-46",
                        font=("Helvetica", 10, "italic"),
                        bg="#1E1E1E", fg="white")
footer_label.pack(side=tk.BOTTOM, pady=10)

root.mainloop()
