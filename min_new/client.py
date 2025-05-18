import socket
import pickle
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
import subprocess
import os
import sys
import threading
from flask import redirect
import smtplib
import random
from email.mime.text import MIMEText

otp_storage = {}

# Server connection setup
host = '127.0.0.1'
port = 2022
sock = socket.socket()
sock.connect((host, port))

# Flask app setup
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = '74849hfjkL34352678GHHFe'


def send_otp_email(to_email, otp):
    sender_email = "info.trafficgovsl@gmail.com"
    sender_password = "ggdg qula nzwx njka"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEText(f"Your OTP for login is: {otp}")
    msg['Subject'] = "Your OTP Code"
    msg['From'] = sender_email
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)



UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
VIOLATION_SCRIPT = r"F:\fyp final project files all\los\violation_detector.py"
NUMBER_SCRIPT = r"F:\fyp final project files all\numberplate detection sltc project\Number_plate_detectionusing-Yolov8-main\interface.py"
NUMBER_PLATE_FOLDER = os.path.dirname(NUMBER_SCRIPT)
LOS_FOLDER = os.path.dirname(VIOLATION_SCRIPT)

gui_running = False


#violation detection sys
@app.route('/start_violation')
def start_violation():
    global gui_running
    gui_running = True

    def run_gui():
        global gui_running
        try:
            python_exec = sys.executable
            subprocess.run([python_exec, VIOLATION_SCRIPT], cwd=LOS_FOLDER)
        except Exception as e:
            print(f"Error: {e}")
        gui_running = False

    threading.Thread(target=run_gui).start()

    return render_template("wait_for_gui.html")

#plate detection
@app.route('/start_plate')
def start_plate():
    global gui_running
    gui_running = True

    def run_gui():
        global gui_running
        try:
            python_exec = sys.executable
            subprocess.run([python_exec, NUMBER_SCRIPT], cwd=NUMBER_PLATE_FOLDER)
        except Exception as e:
            print(f"Error: {e}")
        gui_running = False

    threading.Thread(target=run_gui).start()

    return render_template("wait_for_gui.html")


@app.route('/check_status')
def check_status():
    return jsonify({'running': gui_running})


@app.route("/pay_portal", methods=["GET"])
def pay_portal():
    return render_template("pay.html")

@app.route("/faq", methods=["GET"])
def faq():
    return render_template("faq.html")


@app.route("/log_in", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('Sign_Up') == 'Sign_Up':
            # Handle Sign Up
            Name = request.form.get('Name')
            Email = request.form.get('Email')
            Nic = request.form.get('Nic')
            Lic = request.form.get('Lic')
            Datetime = request.form.get('Datetime')
            Address = request.form.get('Address')
            Phone = request.form.get('Phone')
            Password = request.form.get('Password')


            User_SignUp_arr = {"type": "Sign_Up", 'Name': Name, 'Email': Email, 'Nic':Nic, 'Lic':Lic, 'Datetime': Datetime,  'Address': Address, 'Phone': Phone, 'Password': Password}
            User_SignUp_Dump = pickle.dumps(User_SignUp_arr)
            sock.send(User_SignUp_Dump)

            recv_data = sock.recv(1024)
            recv_data_item = pickle.loads(recv_data)
            flash(recv_data_item["data"])
            return redirect("/log_in")

        if request.form.get('Sign_In') == 'Sign_In':
            # Handle Sign In
            Ename = request.form.get('Ename')
            password = request.form.get('password')

            SignIn_arr = {"type": "Sign_In", 'Ename': Ename, 'password': password}
            SignIn_Dump = pickle.dumps(SignIn_arr)
            sock.send(SignIn_Dump)

            User_details_recv = sock.recv(1024)
            User_Data = pickle.loads(User_details_recv)

            type = User_Data["Type"]

            if type == "User":
                session['user_id'] = User_Data["Data"][0][0]
                session['user_Name'] = User_Data["Data"][0][1]
                session['user_Phone_Number'] = User_Data["Data"][0][2]
                session['user_Email'] = User_Data["Data"][0][3]
                session['User_Address'] = User_Data["Data"][0][4]
                session['User_Nic'] = User_Data["Data"][0][5]
                session['User_Datetime'] = User_Data["Data"][0][6]
                session['User_Lic'] = User_Data["Data"][0][7]
                flash("Login successful")
                # return render_template("homepage_2.html")

                # Fetch vehicle data for this user after successful login
                vehicle_request = {"type": "Show_Vehicles", "user_id": session['user_id']}
                vehicle_request_dump = pickle.dumps(vehicle_request)
                sock.send(vehicle_request_dump)

                # Receive vehicle data from server
                recv_data = sock.recv(1024)
                vehicle_data = pickle.loads(recv_data)

                # If the server responds with valid vehicle data
                if vehicle_data["Type"] == "Vehicles":
                    vehicles = vehicle_data["Data"]
                    user_data = User_Data["Data"][0]  # Profile data of the user
                    return render_template("homepage_2.html", user_data=user_data, vehicles=vehicles)

                else:
                    # If no vehicles, proceed with the profile data
                    user_data = User_Data["Data"][0]
                    flash("No vehicles found for your account.")
                    return render_template("homepage_2.html", user_data=user_data, vehicles=[])


            if type == "Error":
                session['user_id'] = None
                session['user_Name'] = None
                session['user_Phone_Number'] = None
                session['user_Email'] = None
                session['User_Address'] = None
                session['User_Nic'] = None
                session['User_Datetime'] = None
                session['User_Lic'] = None
                flash("Login unsuccessful. Try Again")
                return redirect("/log_in")

    return render_template("form.html")

#government site login
@app.route("/govlog", methods=['GET', 'POST'])
def govlog():
    if request.method == 'POST':
        if request.form.get('Sign') == 'Sign':
            # Handle Government Sign In
            Empid = request.form.get('Empid')  # Get Employee ID
            Ename = request.form.get('Ename')  # Get Email
            password = request.form.get('password')  # Get Password

            SignIn_arr = {"type": "gov_sign_in", 'Empid': Empid, 'Ename': Ename, 'password': password}
            SignIn_Dump = pickle.dumps(SignIn_arr)
            sock.send(SignIn_Dump)

            User_details_recv = sock.recv(1024)
            User_Data = pickle.loads(User_details_recv)

            type = User_Data["Type"]
            if type == "User":
                session['user_id_gov'] = User_Data["Data"][0][0]
                session['user_gov_Name'] = User_Data["Data"][0][1]
                session['user_gov_Emp_id'] = User_Data["Data"][0][2]
                session['user_gov_Email'] = User_Data["Data"][0][3]
                session['user_gov_Nic'] = User_Data["Data"][0][4]
                flash("Government Login successful")
                return render_template("homepage_1.html")

            if type == "Error":
                session['user_id_gov'] = None
                session['user_gov_Name'] = None
                session['user_gov_Emp_id'] = None
                session['user_gov_Email'] = None
                session['user_gov_Nic'] = None
                flash("Login unsuccessful. Try Again")
                return redirect("/govlog")

    return render_template("govform.html")



@app.route("/anlog", methods=['GET', 'POST'])
def anlog():
    if request.method == 'POST':
        if request.form.get('Sign') == 'Sign':
            Empid = request.form.get('Empid')
            Ename = request.form.get('Ename')
            password = request.form.get('password')

            SignIn_arr = {"type": "an_sign_in", 'Empid': Empid, 'Ename': Ename, 'password': password}
            SignIn_Dump = pickle.dumps(SignIn_arr)
            sock.send(SignIn_Dump)

            User_details_recv = sock.recv(1024)
            User_Data = pickle.loads(User_details_recv)

            type = User_Data["Type"]
            if type == "an":
                # Store temporary user data in session
                session['pending_user'] = {
                    "id": User_Data["Data"][0][0],
                    "name": User_Data["Data"][0][1],
                    "empid": User_Data["Data"][0][2],
                    "nic": User_Data["Data"][0][3],
                    "email": User_Data["Data"][0][4],
                }

                # Generate OTP
                otp = str(random.randint(100000, 999999))
                session['otp'] = otp

                # Send OTP via email
                send_otp_email(User_Data["Data"][0][4], otp)

                return redirect(url_for('verify_otp'))

            if type == "Error":
                flash("Login unsuccessful. Try Again")
                return redirect("/anlog")

    return render_template("anform.html")



@app.route("/verify_otp", methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session.get('otp'):
            # Move data to main session
            pending_user = session.pop('pending_user')
            session['an_id'] = pending_user["id"]
            session['an_Name'] = pending_user["name"]
            session['an_EMP_ID'] = pending_user["empid"]
            session['an_Nic'] = pending_user["nic"]
            session['an_Email'] = pending_user["email"]
            session.pop('otp', None)
            flash("Login successful via OTP.")
            return render_template("homepage_3.html")
        else:
            flash("Invalid OTP. Try again.")
            return redirect(url_for('verify_otp'))

    return render_template("otp_form.html")



# insert payment
@app.route("/payment", methods=["POST"])
def payment():
    try:
        submit_type = request.form.get("submit_type")  # Get which button was clicked
        nic = request.form.get("Nic")
        lic_number = request.form.get("Lic")
        email = request.form.get("Email")
        name = request.form.get("Name")
        amount = request.form.get("Payment")

        if submit_type == "payment":
            if not nic or not lic_number or not email or not name or not amount:
                return jsonify(success=False, message="Missing required pay fields.")

            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            court_data = {
                "type": "Payment_Entered",
                "Nic": nic,
                "LIC": lic_number,
                "Email": email,
                "Name": name,
                "Payment": amount,
                "Date_Time": date_time

            }
            sock.send(pickle.dumps(court_data))
            response = pickle.loads(sock.recv(1024))

            if response.get("Type") == "Success":
                flash("Payment & Email submitted successfully!", "success")
                return jsonify(success=True, message="Payment & Email submitted successfully!")
            else:
                return jsonify(success=False, message=response.get("Data", "Unknown error"))

    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}")



# insert coordinates
@app.route("/submit_coordinates", methods=["GET", "POST"])
def coordinates_register():
    if request.method == "POST":
        # Get the road block details from the form
        road_name = request.form.get("Road_name")
        latitude = request.form.get("Latitude")
        longitude = request.form.get("Longitude")
        description = request.form.get("Description")
        start_lat = request.form.get("Start_lat")
        start_lon = request.form.get("Start_lon")
        end_lat = request.form.get("End_lat")
        end_lon = request.form.get("End_lon")

        # Validate form data
        if not road_name or not latitude or not longitude or not start_lat or not start_lon or not end_lat or not end_lon:
            flash("All fields are required!", category='error')
            return redirect(request.url)

        # Check if the user is logged in (session contains user_id)
        user_id_gov = session.get("user_id_gov")
        if not user_id_gov:
            flash("Please log in first to enter coordinates.", category='warning')
            return redirect("/anlog")

        # Prepare the coordinate data for sending to the server
        coordinate_data = {
            "type": "Coordinates_Register",
            "Road_name": road_name,
            "Latitude": latitude,
            "Longitude": longitude,
            "Description": description,
            "Start_lat": start_lat,
            "Start_lon": start_lon,
            "End_lat": end_lat,
            "End_lon": end_lon
        }

        try:
            # Send the coordinate data to the server
            sock.sendall(pickle.dumps(coordinate_data))
            response = sock.recv(1024)
            response_data = pickle.loads(response)
            # Check server response and show the appropriate flash message
            if response_data.get("Type") == "Success":
                flash("Coordinates inserted successfully!", category='success')
            else:
                flash(f"Failed to insert coordinates: {response_data.get('Data', 'Unknown error')}", category='error')
        except (socket.error, pickle.PickleError) as e:
            flash(f"Error communicating with the server: {e}")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}")

        return redirect("/submit_coordinates")
    return render_template("homepage_3.html")


#system detected vehicle show table
@app.route('/detect_table', methods=['GET'])
def detect_table():
    detect_table_request = {"type": "Detect"}
    sock.send(pickle.dumps(detect_table_request))
    # Receive the response from the server
    recv_data = sock.recv(1024)
    response = pickle.loads(recv_data)

    if response["Type"] == "Detect_Fine_Show":
        return jsonify(response["Data"])
    else:
        return jsonify({"error": response["data"]})


#show table court and lic_fine
@app.route('/court_table', methods=['GET'])
def court_table():
    court_table_request = {"type": "Court_Fine"}
    sock.send(pickle.dumps(court_table_request))
    # Receive the response from the server
    recv_data = sock.recv(1024)
    response = pickle.loads(recv_data)

    if response["Type"] == "Court_Fine_Show":
        return jsonify(response["Data"])
    else:
        return jsonify({"error": response["data"]})


@app.route('/fine_table', methods=['GET'])
def fine_table():
    fine_table_request = {"type": "License_Fine"}
    sock.send(pickle.dumps(fine_table_request))
    recv_data = sock.recv(1024)
    response = pickle.loads(recv_data)

    if response["Type"] == "License_Fine_Show":
        return jsonify(response["Data"])
    else:
        return jsonify({"error": response["data"]})


@app.route('/pay_table', methods=['GET'])
def pay_table():
    pay_table_request = {"type": "Pay_Fine"}
    sock.send(pickle.dumps(pay_table_request))
    recv_data = sock.recv(1024)
    response = pickle.loads(recv_data)

    print('Response from server:', response)

    if response["Type"] == "Pay_Fine_Show":
        return jsonify(response["Data"])
    else:
        return jsonify({"error": response["data"]})



#show details name,nic by lic in hompage1
@app.route("/get_details", methods=["GET"])
def get_details():
    lic_number = request.args.get("qr-result")

    if not lic_number:
        flash("LIC number is required", "error")
        return jsonify(success=False, message="LIC number is required")

    try:
        get_details_request = {"type": "Get_User_Details_By_LIC", "Lic": lic_number}
        sock.send(pickle.dumps(get_details_request))
        recv_data = sock.recv(1024)

        if not recv_data:
            return jsonify(success=False, message="No data received from server")

        response = pickle.loads(recv_data)

        if response.get("Type") == "User_Details":
            flash("User details retrieved successfully", "success")
            return jsonify(success=True, user=response["User"])
        else:
            flash(response.get("data", "Unknown error"), "error")
            return jsonify(success=False, message=response.get("data", "Unknown error"))

    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}")



# insert court data and license fine data to two tables submission
@app.route("/handle_form_submission", methods=["POST"])
def handle_form_submission():
    try:
        submit_type = request.form.get("submit_type")  # Get which button was clicked
        nic = request.form.get("Nic")
        violation = request.form.get("Report")
        lic_number = request.form.get("LIC")
        email = request.form.get("Email")
        name = request.form.get("Name")
        phone_number = request.form.get("Phone")
        fine = request.form.get("Pay")
        vehicle = request.form.get("VEH")

        user_gov_Emp_id = session.get("user_gov_Emp_id")
        if not user_gov_Emp_id:
            flash("Please log in first to scan license.")
            return redirect("/govlog")  # Redirect to login page

        if submit_type == "court":
            if not nic or not violation or not lic_number or not email or not name or not phone_number or not vehicle:
                return jsonify(success=False, message="Missing required court fields.")

            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            court_data = {
                "type": "Court_Entered",
                "user_gov_Emp_id": user_gov_Emp_id,
                "Nic": nic,
                "Report": violation,
                "LIC": lic_number,
                "Email": email,
                "Name": name,
                "Phone": phone_number,
                "Date_Time": date_time,
                "VEH": vehicle
            }
            sock.send(pickle.dumps(court_data))
            response = pickle.loads(sock.recv(1024))

            if response.get("Type") == "Success":
                flash("Court data & Email submitted successfully!", "success")
                return jsonify(success=True, message="Court data submitted successfully!")
            else:
                return jsonify(success=False, message=response.get("Data", "Unknown error"))


        elif submit_type == "fine":
            if not all([nic, violation, lic_number, email, name, fine, vehicle]):
                return jsonify(success=False, message="Missing required fields.")
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            fine_data = {
                "type": "License_Fine_Entered",
                "user_gov_Emp_id": user_gov_Emp_id,
                "Nic": nic,
                "Report": violation,
                "LIC": lic_number,
                "Email": email,
                "Name": name,
                "Pay": fine,
                "Date_Time": date_time,
                "VEH": vehicle
            }

            sock.send(pickle.dumps(fine_data))
            response = pickle.loads(sock.recv(1024))

            if response.get("Type") == "Success":
                flash("Fine data & Email submitted successfully!", "success")
                return jsonify(success=True, message="Fine data submitted successfully!")
            else:
                return jsonify(success=False, message=response.get("Data", "Unknown error"))

        else:
            return jsonify(success=False, message="Invalid submission type.")

    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}")



#hompage_2 find safe route map view
@app.route('/blocked_roads', methods=['GET'])
def get_blocked_roads():
    # Send the request to the server to fetch blocked roads data
    blocked_roads_request = {"type": "Get_Blocked_Roads"}
    sock.send(pickle.dumps(blocked_roads_request))

    # Receive the response from the server
    recv_data = sock.recv(1024)
    response = pickle.loads(recv_data)

    if response["Type"] == "Blocked_Roads":
        return jsonify(response["Data"])

    else:
        return jsonify({"error": response["data"]})



#qr code scan in login form and govpage lic scanss
@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    scanned_data = data.get('qr_data', '')
    print(f"Scanned Data: {scanned_data}")
    return jsonify({"message": "QR Code Scanned Successfully!", "data": scanned_data})



#register vehicle name and number site
@app.route("/submit", methods=["GET", "POST"])
def register_vehicle():
    if request.method == "POST":
        # Get the vehicle details from the form
        vehicle_name = request.form.get("VehicleName")
        vehicle_number = request.form.get("VehicleNumber")

        # Validate form data
        if not vehicle_name or not vehicle_number:
            flash("Both Vehicle Name and Vehicle Number are required!")
            return redirect(request.url)  # Reload the page

        # Check if the user is logged in (session contains user_id)
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in first to register a vehicle.")
            return redirect("/log_in")  # Redirect to login page

        # Prepare the vehicle data for sending to the server
        vehicle_data = {
            "type": "Register_Vehicle",
            "user_id": user_id,
            "VehicleName": vehicle_name,
            "VehicleNumber": vehicle_number
        }

        try:
            # Send the vehicle data to the server
            sock.sendall(pickle.dumps(vehicle_data))

            # Receive the response from the server
            response = sock.recv(1024)
            response_data = pickle.loads(response)

            # Check server response and show the appropriate flash message
            if response_data.get("Type") == "Success":
                flash("Vehicle registered successfully!")
            else:
                flash(f"Failed to register vehicle: {response_data.get('Data', 'Unknown error')}")
        except (socket.error, pickle.PickleError) as e:
            flash(f"Error communicating with the server: {e}")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}")

        # Redirect back to the form
        return redirect("/log_in")

    # Handle GET request: show the vehicle registration form
    return render_template("homepage_2.html")


######################################################
@app.route("/enter_lic", methods=["GET", "POST"])
def enter_lic():
    if request.method == "POST":
        lic_number = request.form.get("LIC")  # Get LIC number from form
        print(f"Received LIC Number: {lic_number}")  # Debugging

        try:
            # Create request payload for server
            request_data = {"type": "Get_User_Vehicles_By_LIC", "LIC": lic_number}
            sock.send(pickle.dumps(request_data))  # Send request

            # Receive response from server
            response_data = sock.recv(4096)
            response = pickle.loads(response_data)

            # Debugging logs
            print("Server Response:", response)

            if response["Type"] == "User_Vehicles":
                user_data = response["User"]
                vehicles = response["Vehicles"]
                print("User Data:", user_data)
                print("Vehicles:", vehicles)
                return render_template("homepage_1.html", user_data=user_data, vehicles=vehicles)

            else:
                flash("No user or vehicles found for the given LIC number.")

        except Exception as e:
            print(f"Error in processing LIC number: {e}")
            flash("An error occurred while fetching data. Please try again.")

    return render_template("homepage_1.html")  # Default render
###################################################


@app.route("/vehicles", methods=["GET"])
def vehicles():
    user_id = session.get('user_id')  # Retrieve the user_id from the session

    if user_id:
        # Send the request to the server to fetch vehicle details for the logged-in user
        vehicle_request = {"type": "Show_Vehicles", "user_id": user_id}
        vehicle_request_dump = pickle.dumps(vehicle_request)
        sock.send(vehicle_request_dump)

        # Receive the response from the server
        recv_data = sock.recv(1024)
        vehicle_data = pickle.loads(recv_data)

        # If the server responds with valid vehicle data
        if vehicle_data["Type"] == "Vehicles":
            vehicles = vehicle_data["Data"]  # List of vehicles
            return render_template("vehicles.html", vehicles=vehicles)
        else:
            flash(vehicle_data["data"])  # Show error if no vehicles found
            return redirect("/")

    else:
        flash("Please log in to view your vehicles.")
        return redirect("/log_in")


@app.route("/logout", methods=["GET"])
def logout():
    user_id = session.get('user_id')  # Retrieve the user_id from the session

    if user_id:
        logout_request = {"type": "logout", "user_id": user_id}
        logout_request_dump = pickle.dumps(logout_request)
        sock.send(logout_request_dump)

        # Receive response from the server
        recv_data = sock.recv(1024)
        response = pickle.loads(recv_data)

        if response["Type"] == "Success":
            flash(response["data"])
        else:
            flash(response["data"])

    # Clear session on the client side
    session.clear()
    return redirect("/log_in")


@app.route("/govlogout", methods=["GET"])
def govlogout():
    # Retrieve the government user ID from the session
    user_id_gov = session.get('user_id_gov')

    if user_id_gov:
        # Send logout request to the server
        logout_request = {"type": "gov_logout", "user_id_gov": user_id_gov}
        logout_request_dump = pickle.dumps(logout_request)
        sock.send(logout_request_dump)

        # Receive response from the server
        recv_data = sock.recv(1024)
        response = pickle.loads(recv_data)

        if response["Type"] == "Success":
            flash(response["data"])
        else:
            flash(response["data"])

    # Clear session data for the government user
    session.clear()
    return redirect("/govlog")


@app.route("/anlogout", methods=["GET"])
def anlogout():
    # Retrieve the government user ID from the session
    an_id = session.get('an_id')

    if an_id:
        # Send logout request to the server
        logout_request = {"type": "an_logout", "an_id": an_id}
        logout_request_dump = pickle.dumps(logout_request)
        sock.send(logout_request_dump)

        # Receive response from the server
        recv_data = sock.recv(1024)
        response = pickle.loads(recv_data)

        if response["Type"] == "Success":
            flash(response["data"])
        else:
            flash(response["data"])

    # Clear session data for the government user
    session.clear()
    return redirect("/anlog")


@app.route("/", methods=['GET'])
def index():
    user_id = session.get('user_id')
    #user_id_gov = session.get('user_id_gov')
    home_details_arr = {"type": "F_page"}
    home_details_Dump = pickle.dumps(home_details_arr)
    sock.send(home_details_Dump)

    recv_data = sock.recv(4048)
    if not recv_data:
        return redirect("/")
    recv_data_string = pickle.loads(recv_data)
    return render_template("index.html", co_data=recv_data_string, user_id=user_id)#user_id_gov=user_id_gov


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1335)
