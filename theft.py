


import cv2
import numpy as np
import os
from datetime import datetime
import pyttsx3

# Email configuration (user must fill in)
import smtplib
import time
from email.message import EmailMessage
import imghdr
EMAIL_ADDRESS = 'd23050523@gmail.com'  # <-- CHANGE THIS
EMAIL_PASSWORD = 'zvxl posu alrx webv'        # <-- CHANGE THIS
TO_EMAIL = 'd23050523@gmail.com'  # <-- CHANGE THIS

# Import extension modules
from mode_manager import ModeManager
from guest_mode import guest_manager
from alert_system import AlertSystem
from advanced_cover_detection import AdvancedCoveredFaceDetector
from database import DatabaseManager
from anti_spoofing_simple import AntiSpoofingDetector
from otp_service import generate_otp, verify_otp

# Directory to save unknown faces
UNKNOWN_DIR = 'unknown'
if not os.path.exists(UNKNOWN_DIR):
    os.makedirs(UNKNOWN_DIR)

# Track unknown face detections
unknown_counter = 0
unknown_threshold = 3  # Send email after 3 unknown detections
otp_sent = False

# Initialize extension modules
db = DatabaseManager()
mode_manager = ModeManager(db)
alert_system = AlertSystem()
cover_detector = AdvancedCoveredFaceDetector()
spoof_detector = AntiSpoofingDetector()

# Initialize text-to-speech engine
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Load the face recognizer and face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Directory where the face data is stored
data_dir = 'face_data'

def train_model():
    images = []
    labels = []
    label_dict = {}
    target_size = (200, 200)  # Resize all images to this size

    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        print("No training images found. System will treat all faces as unknown.")
        return {}

    for i, file in enumerate(os.listdir(data_dir)):
        image_path = os.path.join(data_dir, file)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        image = cv2.resize(image, target_size)  # Resize the image
        label = file.split('_')[0]
        
        if label not in label_dict:
            label_dict[label] = len(label_dict)
        
        images.append(image)
        labels.append(label_dict[label])

    if not images:
        print("No valid training images found. System will treat all faces as unknown.")
        return {}

    images = np.array(images)
    labels = np.array(labels)
    recognizer.train(images, labels)
    return label_dict

def recognize_face():
    cap = cv2.VideoCapture(0)
    label_dict = train_model()

    global unknown_counter
    global otp_sent
    current_mode = mode_manager.get_current_mode()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = frame[y:y + h, x:x + w].copy()
            face_gray = gray[y:y + h, x:x + w]

            # Anti-spoofing check (liveness detection)
            if spoof_detector.is_spoof(face_gray, gray):
                cv2.putText(frame, 'Spoofing Detected - Access Blocked', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                speak("Spoofing detected. Access blocked.")
                # Send spoof alert email
                filename = save_unknown(face_img)
                send_spoof_alert(filename)
                spoof_detector.reset()  # Reset for next detection
                continue

            # Check if face is covered
            is_covered, cover_type, confidence = cover_detector.detect_covered_face(face_img)
            
            if is_covered and confidence > 0.7:
                cv2.putText(frame, 'Covered Face', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                speak("Please uncover your face for recognition.")
                # Send alert to owner about covered face
                filename = save_unknown(face_img)
                send_covered_alert(filename, cover_type)
                continue

            if label_dict:
                label, confidence = recognizer.predict(face_gray)

                person_name = None
                for name, id in label_dict.items():
                    if id == label:
                        person_name = name
                        break

                if confidence < 50 and person_name is not None:
                    record_face(person_name)
                    cv2.putText(frame, f'{person_name}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if mode_manager.should_provide_voice_feedback():
                        speak(f"Hi {person_name}, welcome back!")
                    unknown_counter = 0  # Reset counter if recognized
                else:
                    cv2.putText(frame, 'Unknown', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    if mode_manager.should_provide_voice_feedback():
                        speak("Unauthorized user detected.")
                    unknown_counter += 1
                    if unknown_counter >= unknown_threshold and not guest_manager.is_guest_mode_active():
                        # Save unknown face
                        filename = save_unknown(face_img)
                        # Generate OTP
                        otp = generate_otp()
                        # Send email with OTP and guest mode options
                        send_unknown_alert(filename, otp)
                        # Prompt for OTP input
                        user_input = input("Enter OTP to grant guest access (or use email buttons): ")
                        if verify_otp(user_input):
                            speak("OTP verified. Enabling guest mode for 30 minutes.")
                            print("Guest mode enabled for 30 minutes")
                            guest_manager.enable_guest_mode(30)
                        else:
                            speak("OTP incorrect. Access blocked.")
                        unknown_counter = 0  # Reset after alert
            else:
                # No training data, treat all as unknown
                cv2.putText(frame, 'Unknown', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if mode_manager.should_provide_voice_feedback():
                    speak("Unauthorized user detected.")
                unknown_counter += 1
                if unknown_counter >= unknown_threshold and not guest_manager.is_guest_mode_active():
                    # Save unknown face
                    filename = save_unknown(face_img)
                    # Generate OTP
                    otp = generate_otp()
                    # Send email with OTP and guest mode options
                    send_unknown_alert(filename, otp)
                    # Prompt for OTP input
                    user_input = input("Enter OTP to grant guest access (or use email buttons): ")
                    if verify_otp(user_input):
                        speak("OTP verified. Enabling guest mode for 30 minutes.")
                        print("Guest mode enabled for 30 minutes")
                        guest_manager.enable_guest_mode(30)
                    else:
                        speak("OTP incorrect. Access blocked.")
                    unknown_counter = 0  # Reset after alert

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display current mode
        cv2.putText(frame, f'Mode: {current_mode}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.imshow('Face Recognition', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Escape key
            break
        elif key == ord('h'):  # Home mode
            mode_manager.set_mode('Home')
            current_mode = 'Home'
            alert_system.alert_mode_change('Home')
        elif key == ord('n'):  # Night mode
            mode_manager.set_mode('Night')
            current_mode = 'Night'
            alert_system.alert_mode_change('Night')
        elif key == ord('v'):  # Vacation mode
            mode_manager.set_mode('Vacation')
            current_mode = 'Vacation'
            alert_system.alert_mode_change('Vacation')
        elif key == ord('e'):  # Helper mode
            mode_manager.set_mode('Helper')
            current_mode = 'Helper'
            alert_system.alert_mode_change('Helper')
        elif key == ord('g'):  # Start guest mode
            if mode_manager.is_guest_allowed():
                otp = guest_manager.generate_otp()
                speak(f"Guest OTP is {otp}. Please enter it on the web interface.")
                print(f"Guest OTP: {otp}")

    cap.release()
    cv2.destroyAllWindows()


def record_face(name):
    with open('face.txt', 'a') as f:
        now = datetime.now()
        dt_string = now.strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'{name},{dt_string}\n')
        print(f'face recorded for {name} at {dt_string}')

def save_unknown(face_img):
    filename = os.path.join(UNKNOWN_DIR, f"unknown_{int(time.time())}.jpg")
    cv2.imwrite(filename, face_img)
    return filename


def send_unknown_alert(image_path, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Alert! Unknown Person Detected - Action Required'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    
    html_content = f"""
    <html>
    <body>
    <p>An unknown person was detected. Please review the attached photo and decide whether to allow access.</p>
    <p><strong>OTP for verification: {otp}</strong></p>
    <p>You can either enter the OTP in the console or enable guest mode using the buttons below:</p>
    <a href="http://localhost:5000/enable_guest?duration=30" style="background-color: #4CAF50; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Enable Guest Mode (30 mins)</a>
    <a href="http://localhost:5000/enable_guest?duration=120" style="background-color: #008CBA; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Enable Guest Mode (2 hours)</a>
    <a href="http://localhost:5000/enable_guest?duration=1440" style="background-color: #f44336; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Enable Guest Mode (1 day)</a>
    </body>
    </html>
    """
    
    msg.set_content(html_content, subtype='html')

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_type = imghdr.what(img_file.name)
        img_name = os.path.basename(img_file.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=img_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print('Unknown person alert email sent!')
    except Exception as e:
        print(f'Failed to send email: {e}')

def send_spoof_alert(image_path):
    msg = EmailMessage()
    msg['Subject'] = 'Alert! Spoofing Attempt Detected - Security Breach'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    
    html_content = f"""
    <html>
    <body>
    <p><strong>SECURITY ALERT - SPOOFING DETECTED:</strong></p>
    <p style="color: red; font-weight: bold;">SPOOFED IMAGE DETECTED - Photo from phone or static display identified!</p>
    <p>A spoofing attempt has been detected! The system identified a static image (likely a photo or screen display) that lacks natural facial movement.</p>
    <p>The attached image shows the detected spoof attempt.</p>
    <p>Access has been blocked for security reasons.</p>
    </body>
    </html>
    """
    
    msg.set_content(html_content, subtype='html')

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_type = imghdr.what(img_file.name)
        img_name = os.path.basename(img_file.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=img_name)

def send_otp_alert(image_path, otp):
    msg = EmailMessage()
    msg['Subject'] = 'OTP for Access Verification'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    
    html_content = f"""
    <html>
    <body>
    <p>An unknown person was detected. Please verify with the OTP below.</p>
    <p><strong>OTP: {otp}</strong></p>
    <p>Enter this OTP to grant access.</p>
    </body>
    </html>
    """
    
    msg.set_content(html_content, subtype='html')

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_type = imghdr.what(img_file.name)
        img_name = os.path.basename(img_file.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=img_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print('OTP alert email sent!')
    except Exception as e:
        print(f'Failed to send OTP email: {e}')

def send_otp_failed_alert(image_path):
    msg = EmailMessage()
    msg['Subject'] = 'OTP Verification Failed'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    
    html_content = """
    <html>
    <body>
    <p>OTP verification failed for an unknown person.</p>
    <p>Access was blocked.</p>
    </body>
    </html>
    """
    
    msg.set_content(html_content, subtype='html')

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_type = imghdr.what(img_file.name)
        img_name = os.path.basename(img_file.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=img_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print('OTP failed alert email sent!')
    except Exception as e:
        print(f'Failed to send OTP failed email: {e}')

def send_covered_alert(image_path, cover_type):
    msg = EmailMessage()
    msg['Subject'] = f'Alert! Covered Face Detected - {cover_type}'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    
    html_content = f"""
    <html>
    <body>
    <p><strong>SECURITY ALERT - COVERED FACE DETECTED:</strong></p>
    <p style="color: orange; font-weight: bold;">Face covering detected: {cover_type}</p>
    <p>A person with a covered face has been detected. The system requires an uncovered face for recognition.</p>
    <p>The attached image shows the detected covered face.</p>
    <p>Please ensure the person uncovers their face for proper identification.</p>
    </body>
    </html>
    """
    
    msg.set_content(html_content, subtype='html')

    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_type = imghdr.what(img_file.name)
        img_name = os.path.basename(img_file.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=img_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print('Covered face alert email sent!')
    except Exception as e:
        print(f'Failed to send covered face email: {e}')

recognize_face()