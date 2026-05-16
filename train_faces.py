import cv2
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Initialize the face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Directory where the face data will be stored
data_dir = 'face_data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def capture_faces(name):
    cap = cv2.VideoCapture(0)  # Change this index if needed
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break
        
        if frame is None:
            print("Error: Empty frame captured.")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        nikfaces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in nikfaces:
            count += 1
            face = gray[y:y + h, x:x + w]
            file_name_path = os.path.join(data_dir, f'{name}_{count}.jpg')
            cv2.imwrite(file_name_path, face)
            cv2.putText(frame, str(count), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('Face Capture', frame)

        if cv2.waitKey(1) == 27 or count >= 200:  # Escape key or 100 samples
            break

    cap.release()
    cv2.destroyAllWindows()

def send_alert_email(unknown_face_image):
    sender_email = "youremail@example.com"
    owner_email = "owneremail@example.com"
    password = "yourpassword"

    # Set up the server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = owner_email
    msg['Subject'] = 'Intruder Alert!'

    # Add guest mode link
    guest_mode_link = 'http://localhost:5000/guest_mode'
    body = f"An unknown face has been detected.\n\nPlease click the link to enable guest mode: {guest_mode_link}"
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    server.send_message(msg)
    server.quit()

name = input("Enter your name: ")
capture_faces(name)
