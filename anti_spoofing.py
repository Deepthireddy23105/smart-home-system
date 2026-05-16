import cv2
import numpy as np
import time
import dlib
import os

class AntiSpoofingDetector:
    def __init__(self):
        # Download shape predictor if not exists
        predictor_path = 'shape_predictor_68_face_landmarks.dat'
        if not os.path.exists(predictor_path):
            print("Downloading facial landmarks model...")
            import urllib.request
            url = "https://github.com/italojs/facial-landmarks-recognition/raw/master/shape_predictor_68_face_landmarks.dat"
            urllib.request.urlretrieve(url, predictor_path)
            print("Model downloaded.")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # Blink detection variables
        self.blink_counter = 0
        self.total_blinks = 0
        self.eye_closed_frames = 0
        self.blink_threshold = 0.25  # EAR threshold for closed eye
        self.consecutive_frames = 3  # Frames eye must be closed to count as blink
        
    def eye_aspect_ratio(self, eye):
        # Compute the euclidean distances between the two sets of vertical eye landmarks
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        # Compute the euclidean distance between the horizontal eye landmarks
        C = np.linalg.norm(eye[0] - eye[3])
        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink(self, gray, face_rect):
        # Detect facial landmarks
        shape = self.predictor(gray, face_rect)
        shape = np.array([[p.x, p.y] for p in shape.parts()])
        
        # Extract left and right eye coordinates
        left_eye = shape[36:42]
        right_eye = shape[42:48]
        
        # Calculate EAR for both eyes
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        # Check if eyes are closed
        if ear < self.blink_threshold:
            self.eye_closed_frames += 1
        else:
            if self.eye_closed_frames >= self.consecutive_frames:
                self.blink_counter += 1
                self.total_blinks += 1
            self.eye_closed_frames = 0
            
        return ear < self.blink_threshold  # Return if eyes currently closed
    
    def is_spoof(self, face_img, gray_frame):
        """
        Detect spoofing using eye blink detection.
        If no blinks detected within a time window, consider it spoof.
        """
        # Detect faces in the frame
        faces = self.detector(gray_frame)
        if len(faces) == 0:
            return False  # No face detected
        
        face_rect = faces[0]  # Use first face
        
        # Detect blink
        eyes_closed = self.detect_blink(gray_frame, face_rect)
        
        # Simple spoof detection: if no blinks in last 10 seconds and eyes not closed, might be spoof
        # For demo, if total_blinks is 0 after some time, flag as spoof
        # But to make it work, let's check if eyes are detected and blinking
        
        # Actually, for spoof detection, if it's a photo/screen, landmarks might still work
        # Better: check if EAR varies over time
        
        # For now, if no blinks detected in reasonable time, flag as spoof
        if self.total_blinks == 0 and time.time() - getattr(self, 'start_time', time.time()) > 5:
            return True
        
        if not hasattr(self, 'start_time'):
            self.start_time = time.time()
            
        return False  # Assume real if blinks detected or within time

    def reset(self):
        """Reset blink counters for new detection"""
        self.blink_counter = 0
        self.total_blinks = 0
        self.eye_closed_frames = 0
        if hasattr(self, 'start_time'):
            delattr(self, 'start_time')