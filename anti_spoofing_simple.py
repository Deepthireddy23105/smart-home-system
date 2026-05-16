import cv2
import numpy as np
import time

class AntiSpoofingDetector:
    def __init__(self):
        self.frame_buffer = []
        self.buffer_size = 10  # Number of frames to analyze
        self.variance_threshold = 2000  # High threshold to detect spoof

    def is_spoof(self, face_img, gray_frame):
        """
        Detect spoofing using frame motion analysis.
        If the entire frame shows little variation, it's likely a static image (spoof).
        """
        # Resize frame to fixed size
        frame_resized = cv2.resize(gray_frame, (200, 200))
        
        # Add current frame to buffer
        self.frame_buffer.append(frame_resized.copy())
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)

        # Need at least a few frames to analyze
        if len(self.frame_buffer) < 5:
            print(f"Buffer size: {len(self.frame_buffer)}")
            return False  # Assume real until we have enough data

        # Calculate variance across frames
        variances = []
        for i in range(1, len(self.frame_buffer)):
            diff = cv2.absdiff(self.frame_buffer[i-1], self.frame_buffer[i])
            variance = np.var(diff)
            variances.append(variance)

        avg_variance = np.mean(variances)

        print(f"Average variance: {avg_variance}")

        # If average variance is low, scene is not moving (likely spoof)
        if avg_variance < self.variance_threshold:
            print("Spoof detected!")
            return True  # Spoof detected
        else:
            print("Real scene")
            return False  # Real scene

    def reset(self):
        """Reset the frame buffer for new detection"""
        self.frame_buffer = []