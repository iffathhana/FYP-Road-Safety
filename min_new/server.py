import socket
import pickle
import mysql.connector
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Database
data_base = mysql.connector.connect(
    host='localhost',
    port='3306',
    user='root',
    passwd='16471',
    database='dev'
)

db_con = data_base.cursor()

# Server settings
host = '127.0.0.1'
port = 2022

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind((host, port))
soc.listen()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "info.trafficgovsl@gmail.com"
SENDER_PASSWORD = "ggdg qula nzwx njka"


def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")



def handle_client(client):
    while True:
        try:
            recv_data = client.recv(4048)
            if not recv_data:
                break
            recv_data_string = pickle.loads(recv_data)
            req_type = recv_data_string["type"]

            if req_type == "Sign_Up":
                # Sign Up Handling
                Name = recv_data_string['Name']
                Phone_Number = recv_data_string['Phone']
                Email = recv_data_string['Email']
                Password = recv_data_string['Password']
                User_Address = recv_data_string['Address']
                Nic_no = recv_data_string['Nic']
                Lic_id = recv_data_string['Lic']
                Datebr = recv_data_string['Datetime']

                try:
                    query = """
                        INSERT INTO user (Name, Phone_Number, Email, Password, User_Address,Lic_id, Nic_no, Datebr)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (Name, Phone_Number, Email, Password, User_Address,Lic_id, Nic_no, Datebr)
                    db_con.execute(query, values)
                    data_base.commit()

                    response = {'Type': "Successful", 'data': 'Successfully Signed Up'}
                except mysql.connector.Error as err:
                    response = {'Type': "Error", 'data': f'Sign-Up failed: {err}'}

                client.sendall(pickle.dumps(response))


            elif req_type == "Sign_In":
                # Sign In Handling
                Ename = recv_data_string['Ename']
                password = recv_data_string['password']

                query = """
                    SELECT user_id, Name, Phone_Number, Email, User_Address,Lic_id, Nic_no, Datebr
                    FROM user WHERE Email = %s AND Password = %s
                """
                db_con.execute(query, (Ename, password))
                user_details = db_con.fetchone()

                if user_details:
                    response = {"Type": "User", "Data": [user_details]}
                else:
                    response = {"Type": "Error", "data": "Invalid credentials"}

                client.sendall(pickle.dumps(response))


            elif req_type == "Show_Profile":
                # Show Profile Handling
                user_id = recv_data_string['user_id']
                query = """
                    SELECT user_id, Name, Phone_Number, Email, User_Address, Nic_no, Datebr
                    FROM user WHERE user_id = %s
                """
                db_con.execute(query, (user_id,))
                user_details = db_con.fetchone()

                if user_details:
                    response = {"Type": "User", "Data": [user_details]}
                else:
                    response = {"Type": "Error", "data": "User not found"}

                client.sendall(pickle.dumps(response))


            elif req_type == "gov_sign_in":
                # Government Sign In Handling
                Empid = recv_data_string['Empid']
                Ename = recv_data_string['Ename']
                password = recv_data_string['password']
                query = """SELECT user_id_gov, Name, Emp_id, Email, Nic FROM user_gov WHERE Emp_id = %s AND Email = %s AND Password = %s"""
                db_con.execute(query, (Empid, Ename, password))
                user_details = db_con.fetchone()

                if user_details:
                    response = {"Type": "User", "Data": [user_details]}
                else:
                    response = {"Type": "Error", "data": "Invalid government credentials"}
                client.sendall(pickle.dumps(response))

            elif req_type == "an_sign_in":
                # analytical Sign In Handling
                Empid = recv_data_string['Empid']
                Ename = recv_data_string['Ename']
                password = recv_data_string['password']
                query = """SELECT an_id, Name, EMP_ID, Nic, Email FROM an_user WHERE EMP_ID = %s AND Email = %s AND Password = %s"""
                db_con.execute(query, (Empid, Ename, password))
                user_details = db_con.fetchone()

                if user_details:
                    response = {"Type": "an", "Data": [user_details]}
                else:
                    response = {"Type": "Error", "data": "Invalid analytical credentials"}
                client.sendall(pickle.dumps(response))




            elif req_type == "F_page":
                # Index Page Handling
                query = "SELECT item_id, image, name, item_category, status, base_price, expiry_date FROM item"
                db_con.execute(query)
                items = db_con.fetchall()

                client.sendall(pickle.dumps(items))



            elif req_type == "Detect":
                try:
                    query = "SELECT * FROM number_plates"
                    db_con.execute(query)
                    detect_cases = db_con.fetchall()

                    if detect_cases:
                        Dtable_data = [
                            {
                                "id": case[0],
                                "plate_number": case[1],
                                "image_path": case[2],
                                "detected_at": case[3],
                                "violation_type": case[4],
                                "fine": case[5]
                            }
                            for case in detect_cases
                        ]
                        response = {"Type": "Detect_Fine_Show", "Data": Dtable_data if detect_cases else []}
                    else:
                        response = {"Type": "Error", "data": "No system cases found"}
                except mysql.connector.Error as err:
                    response = {"Type": "Error", "data": f"Database error: {err}"}

                print('Sending response to client:', response)  # Debugging line
                client.sendall(pickle.dumps(response))



            #table court and fine show function
            elif req_type == "Court_Fine":
                try:
                    query = "SELECT * FROM court"
                    db_con.execute(query)
                    court_cases = db_con.fetchall()

                    if court_cases:
                        Ctable_data = [
                            {
                                "Ct_id": case[0],
                                "Nic": case[1],
                                "Violation": case[2],
                                "Lic_number": case[3],
                                "Email": case[4],
                                "Name": case[5],
                                "Phone_Number": case[6],
                                "Date_Time": case[7],
                                "vehicle_no": case[8],
                                "Emp_id": case[9]
                            }
                            for case in court_cases
                        ]
                        response = {"Type": "Court_Fine_Show", "Data": Ctable_data if court_cases else []}
                    else:
                        response = {"Type": "Error", "data": "No court cases found"}
                except mysql.connector.Error as err:
                    response = {"Type": "Error", "data": f"Database error: {err}"}

                print('Sending response to client:', response)  # Debugging line
                client.sendall(pickle.dumps(response))


            elif req_type == "License_Fine":
                try:
                    query = "SELECT * FROM license_violation"
                    db_con.execute(query)
                    fines = db_con.fetchall()

                    if fines:
                        Ftable_data = [
                            {
                                "lic_id": fine[0],
                                "Nic": fine[1],
                                "Lic_no": fine[2],
                                "Veh_no": fine[3],
                                "Name": fine[4],
                                "Violation": fine[5],
                                "Fine": fine[6],
                                "Date": fine[7],
                                "Email": fine[8],
                                "Emp_id": fine[9]
                            }
                            for fine in fines
                        ]
                        response = {"Type": "License_Fine_Show", "Data": Ftable_data if fines else []}
                    else:
                        response = {"Type": "Error", "data": "No fine list found"}
                except mysql.connector.Error as err:
                    response = {"Type": "Error", "data": f"Database error: {err}"}

                client.sendall(pickle.dumps(response))


            elif req_type == "Pay_Fine":
                try:
                    query = "SELECT * FROM payment"
                    db_con.execute(query)
                    pays = db_con.fetchall()

                    if pays:
                        Ptable_data = [
                            {
                                "p_id": pay[0],
                                "Nic": pay[1],
                                "Lic": pay[2],
                                "Email": pay[3],
                                "Name": pay[4],
                                "Amount": pay[5],
                                "Date": pay[6]
                            }
                            for pay in pays
                        ]
                        response = {"Type": "Pay_Fine_Show", "Data": Ptable_data if pays else []}
                    else:
                        response = {"Type": "Error", "data": "No payments found"}
                except mysql.connector.Error as err:
                    response = {"Type": "Error", "data": f"Database error: {err}"}

                client.sendall(pickle.dumps(response))



            #this is for map view details and table using also to script attach
            elif req_type == "Get_Blocked_Roads":
                query = "SELECT * FROM blocked_roads"
                db_con.execute(query)
                blocked_roads = db_con.fetchall()

                if blocked_roads:
                    roads_data = [
                        {
                            "id": road[0],
                            "road_name": road[1],
                            "latitude": road[2],
                            "longitude": road[3],
                            "description": road[4],
                            "start_lat": road[5],
                            "start_lon": road[6],
                            "end_lat": road[7],
                            "end_lon": road[8]
                        }
                        for road in blocked_roads
                    ]
                    response = {"Type": "Blocked_Roads", "Data": roads_data}
                else:
                    response = {"Type": "Error", "data": "No blocked roads found"}

                print("Response:", response)
                client.sendall(pickle.dumps(response))


              #insert lic fine amount
            elif recv_data_string.get("type") == "License_Fine_Entered":
                try:
                    user_gov_Emp_id = recv_data_string.get("user_gov_Emp_id")
                    nic = recv_data_string.get("Nic")
                    violation = recv_data_string.get("Report")
                    lic_number = recv_data_string.get("LIC")
                    email = recv_data_string.get("Email")
                    name = recv_data_string.get("Name")
                    fine = recv_data_string.get("Pay")
                    date_time = recv_data_string.get("Date_Time")
                    vehicle = recv_data_string.get("VEH")

                    if not all([user_gov_Emp_id, nic, violation, lic_number, email, name, fine, date_time, vehicle]):
                        response = {"Type": "Error", "Data": "Missing required fields."}
                        client.sendall(pickle.dumps(response))
                        return

                    # Correct the column name "Violation" to "Violation"
                    query = """
                          INSERT INTO license_violation (Nic, Lic_no, Veh_no, Name, Violation, Fine, Date, Email, Emp_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                      """

                    # Execute the query
                    db_con.execute(query, (nic, lic_number,vehicle, name, violation, fine, date_time, email, user_gov_Emp_id))
                    data_base.commit()

                    subject = "[TEST]License Fine Details"
                    message = \
            f"""
            {name},
            ---TESTING---

            You have received a fine for the following violation:
            Violation: {violation}
            Fine Amount: RS:{fine}
            License Number: {lic_number}
            Vehicle Number: {vehicle}
            Date & Time: {date_time}
                            
            Please Pay the Fine Amount Within 14 Days... Check the Revo page for PAYMENTS...
                            
            Regards,
            -- Srilanka, Government Traffic Authority--
            """
                    send_email(email, subject, message)

                    # Send success response
                    response = {"Type": "Success", "Data": "License fine inserted successfully!"}

                except mysql.connector.Error as db_error:
                    response = {"Type": "Error", "Data": f"Database error occurred: {db_error}"}

                except Exception as e:
                    response = {"Type": "Error", "Data": f"An unexpected error occurred: {str(e)}"}

                client.sendall(pickle.dumps(response))



        # insert court details
            elif recv_data_string.get("type") == "Court_Entered":
                try:
                    user_gov_Emp_id = recv_data_string.get("user_gov_Emp_id")
                    nic = recv_data_string.get("Nic")
                    violation = recv_data_string.get("Report")
                    lic_number = recv_data_string.get("LIC")
                    email = recv_data_string.get("Email")
                    name = recv_data_string.get("Name")
                    phone_number = recv_data_string.get("Phone")
                    date_time = recv_data_string.get("Date_Time")  # Already generated in client.py
                    vehicle = recv_data_string.get("VEH")

                    if not user_gov_Emp_id or not nic or not violation or not lic_number or not email or not name or not phone_number or not vehicle:
                        response = {"Type": "Error", "Data": "Missing required court fields."}
                        client.sendall(pickle.dumps(response))

                        continue

                    query = """
                        INSERT INTO court (Nic, Violation, Lic_number, Email, Name, Phone_number, Date_Time, vehicle_no, Emp_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    db_con.execute(query, (nic, violation, lic_number, email, name, phone_number, date_time, vehicle, user_gov_Emp_id))
                    data_base.commit()

                    subject = "[TEST]Court Appearance Details"
                    message = \
            f"""
            {name},
            ---TESTING---

            You have been scheduled for a court appearance due to the following violation:

            Violation: {violation}
            License Number: {lic_number}
            Vehicle Number: {vehicle}
            Date & Time: {date_time}

            Please check your Revo page user account for further details.
            Within 5 Days Report to the nearest police station.

            Regards,
            -- Srilanka, Government Traffic Authority--
            """
                    send_email(email, subject, message)
                    response = {"Type": "Success", "Data": "Court data inserted successfully!"}

                except mysql.connector.Error as db_error:
                    response = {"Type": "Error", "Data": f"Database error occurred: {db_error}"}

                except Exception as e:
                    response = {"Type": "Error", "Data": "An unexpected error occurred while inserting court data."}

                client.sendall(pickle.dumps(response))



                # insert payment
            elif recv_data_string.get("type") == "Payment_Entered":
                try:

                    nic = recv_data_string.get("Nic")
                    lic_number = recv_data_string.get("LIC")
                    email = recv_data_string.get("Email")
                    name = recv_data_string.get("Name")
                    amount = recv_data_string.get("Payment")
                    date_time = recv_data_string.get("Date_Time")

                    if  not nic or not lic_number or not email or not name or not amount:
                        response = {"Type": "Error", "Data": "Missing required payment fields."}
                        client.sendall(pickle.dumps(response))

                        continue

                    query = """
                                   INSERT INTO payment (Nic, Lic, Email, Name, Amount, Date)
                                   VALUES (%s, %s, %s, %s, %s, %s)
                            """

                    db_con.execute(query, (nic, lic_number, email, name, amount, date_time))
                    data_base.commit()

                    subject = "[TEST]Payment Received Details"
                    message = \
            f"""
            {name},
            ---TESTING---

            Your payment received:

            Paid Amount: {amount}
            Nic number: {nic}
            License Number: {lic_number}
            Date & Time: {date_time}

            Thank you!

            Regards,
            -- Srilanka, Government Traffic Authority--
            """
                    send_email(email, subject, message)
                    response = {"Type": "Success", "Data": "payment inserted successfully!"}

                except mysql.connector.Error as db_error:
                    response = {"Type": "Error", "Data": f"Database error occurred: {db_error}"}

                except Exception as e:
                    response = {"Type": "Error", "Data": "An unexpected error occurred while inserting payment."}

                client.sendall(pickle.dumps(response))


            # coordinates register for map show
            elif recv_data_string.get("type") == "Coordinates_Register":
                try:
                    # Extract coordinate details from the client request
                    road_name = recv_data_string.get("Road_name")
                    latitude = recv_data_string.get("Latitude")
                    longitude = recv_data_string.get("Longitude")
                    description = recv_data_string.get("Description")
                    start_lat = recv_data_string.get("Start_lat")
                    start_lon = recv_data_string.get("Start_lon")
                    end_lat = recv_data_string.get("End_lat")
                    end_lon = recv_data_string.get("End_lon")
                    # Ensure that all required data is provided

                    if not road_name or not latitude or not longitude or not start_lat or not start_lon or not end_lat or not end_lon:
                        response = {"Type": "Error", "Data": "Missing required coordinate fields."}
                        client.sendall(pickle.dumps(response))
                        return

                    # Prepare the SQL query to insert coordinates into the database
                    query = """
                                    INSERT INTO blocked_roads (road_name, latitude, longitude, description, start_lat, start_lon, end_lat, end_lon)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """

                    # Execute the query to insert the data
                    db_con.execute(query, (
                        road_name, latitude, longitude, description, start_lat, start_lon, end_lat, end_lon))
                    data_base.commit()

                    # Respond to the client with success
                    response = {"Type": "Success", "Data": "coordinates insert successfully!"}
                    client.sendall(pickle.dumps(response))

                except mysql.connector.Error as db_error:
                    # Handle database-specific exceptions
                    response = {"Type": "Error", "Data": f"Database error occurred: {db_error}"}
                    client.sendall(pickle.dumps(response))

                except Exception as e:
                    # Catch any other exceptions
                    print(f"Error handling Coordinates_Register request: {e}")  # Log the error for debugging
                    response = {"Type": "Error", "Data": "An unexpected error occurred while inserting coordinates."}
                    client.sendall(pickle.dumps(response))


            #analytical portal logout
            elif req_type == "an_logout":
                an_id = recv_data_string.get("an_id")

                try:
                    # Perform any necessary server-side cleanup if required
                    response = {"Type": "Success", "data": "Analytical logout successful"}
                    print(f"Analyse user {an_id} logged out.")
                except Exception as e:
                    response = {"Type": "Error", "data": f"Analyse logout failed: {e}"}

                # Send the response back to the client
                client.sendall(pickle.dumps(response))


             #government site logout function
            elif req_type == "gov_logout":
                user_id_gov = recv_data_string.get("user_id_gov")

                try:
                    # Perform any necessary server-side cleanup if required
                    response = {"Type": "Success", "data": "Government logout successful"}
                    print(f"Government user {user_id_gov} logged out.")
                except Exception as e:
                    response = {"Type": "Error", "data": f"Government logout failed: {e}"}

                # Send the response back to the client
                client.sendall(pickle.dumps(response))


             # public site logout
            elif req_type == "logout":
                user_id = recv_data_string.get("user_id")

                try:
                    # Perform any server-side cleanup if needed
                    response = {"Type": "Success", "data": "Logout successful"}
                    print(f"User {user_id} logged out.")
                except Exception as e:
                    response = {"Type": "Error", "data": f"Logout failed: {e}"}

                client.sendall(pickle.dumps(response))


            #register vehicle name and number in homepage2
            elif recv_data_string.get("type") == "Register_Vehicle":
                try:
                    user_id = recv_data_string.get("user_id")
                    vehicle_name = recv_data_string.get("VehicleName")
                    vehicle_number = recv_data_string.get("VehicleNumber")


                    if not user_id or not vehicle_name or not vehicle_number:
                        response = {"Type": "Error", "Data": "Missing required vehicle registration fields."}
                        client.sendall(pickle.dumps(response))
                        return

                    # Prepare the SQL query and insert vehicle into the database
                    query = """
                        INSERT INTO vehicle (user_id, Vehicle_name, Vehicle_no)
                        VALUES (%s, %s, %s)
                    """

                    db_con.execute(query, (user_id, vehicle_name, vehicle_number))
                    data_base.commit()

                    # Respond to the client with success
                    response = {"Type": "Success", "Data": "Vehicle registered successfully!"}
                    client.sendall(pickle.dumps(response))

                except mysql.connector.Error as db_error:
                    # Handle database-specific exceptions
                    response = {"Type": "Error", "Data": f"Database error occurred: {db_error}"}
                    client.sendall(pickle.dumps(response))

                except Exception as e:
                    # Catch any other exceptions
                    print(f"Error handling Register_Vehicle request: {e}")  # Log the error for debugging
                    response = {"Type": "Error", "Data": "An unexpected error occurred during vehicle registration."}
                    client.sendall(pickle.dumps(response))


             # show details by lic in homepage_1
            elif req_type == "Get_User_Details_By_LIC":
                Lic_id = recv_data_string.get('Lic')

                if not Lic_id:
                    response = {"Type": "Error", "data": "LIC number is required"}
                    client.sendall(pickle.dumps(response))
                    return

                try:
                    # Query to fetch user details based on LIC number
                    query = "SELECT Name, Phone_Number, Nic_no, Email FROM user WHERE Lic_id = %s"
                    # Execute the query
                    db_con.execute(query, (Lic_id,))
                    user = db_con.fetchone()

                    if user:
                        # Prepare the user details in the required format
                        user_data = {
                            "Name": user[0],
                            "Phone_Number": user[1],
                            "Nic_no": user[2],
                            "Email": user[3]

                        }
                        response = {
                            "Type": "User_Details",
                            "User": user_data
                        }
                    else:
                        response = {"Type": "Error", "data": "No user found for the given LIC number."}

                except mysql.connector.Error as db_error:
                    response = {"Type": "Error", "data": f"Database error: {str(db_error)}"}

                except Exception as e:
                    response = {"Type": "Error", "data": f"Error fetching user details: {str(e)}"}

                # Send the response back to the client
                print("Response:", response)
                client.sendall(pickle.dumps(response))




             #show vehicles in user page2
            elif req_type == "Show_Vehicles":
                # Get the user_id from the request
                user_id = recv_data_string["user_id"]

                # Query to get vehicle details for the given user_id
                query = """
                    SELECT vehicle_id, Vehicle_name, Vehicle_no, Fine, violation
                    FROM vehicle WHERE user_id = %s
                """
                db_con.execute(query, (user_id,))
                vehicle_data = db_con.fetchall()

                # If vehicles are found, send them back to the client
                if vehicle_data:
                    response = {"Type": "Vehicles", "Data": vehicle_data}
                else:
                    response = {"Type": "Error", "data": "No vehicles found for this user"}

                client.sendall(pickle.dumps(response))



            elif req_type == "Get_User_Vehicles_By_LIC":
                # Get LIC number from client request
                lic_number = recv_data_string["LIC"]

                # Query to get user details based on LIC number
                user_query = "SELECT user_id, Name, Phone_Number, Email, User_Address, Lic_id, Nic_no, Datebr FROM user WHERE Lic_id = %s"
                db_con.execute(user_query, (lic_number,))
                user = db_con.fetchone()

                if not user:
                    response = {"Type": "Error", "data": "No user found with this LIC number"}
                else:
                    user_id = user[0]  # Extract user_id

                    # Query to get vehicle details associated with this user
                    vehicle_query = "SELECT vehicle_id, Vehicle_name, Vehicle_no, Fine, violation FROM vehicle WHERE user_id = %s"
                    db_con.execute(vehicle_query, (user_id,))
                    vehicles = db_con.fetchall()

                    # Formatting the response
                    user_data = {
                        "user_id": user[0],
                        "name": user[1],
                        "phone": user[2],
                        "email": user[3],
                        "address": user[4],
                        "lic_id": user[5],
                        "nic_no": user[6],
                        "datebr": user[7]
                    }

                    vehicles_data = [
                        {
                            "vehicle_id": v[0],
                            "vehicle_name": v[1],
                            "vehicle_no": v[2],
                            "fine": v[3],
                            "violation": v[4]
                        }
                        for v in vehicles
                    ]

                    response = {"Type": "User_Vehicles", "User": user_data, "Vehicles": vehicles_data}

                client.sendall(pickle.dumps(response))




        except Exception as e:
            print(f"Error: {e}")
            break

    client.close()

# Start Server
def start_server():
    while True:
        client, addr = soc.accept()
        print(f"Connection from {addr}")
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    start_server()
