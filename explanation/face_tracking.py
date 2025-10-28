# face_tracking.py
"""
Encapsulates the MediaPipe FaceMesh logic for initializing the model
and processing video frames to find facial landmarks.
"""

import cv2
import mediapipe as mp

class FaceTracker:
    def __init__(self, refine_landmarks=True):
        """
        Initializes the MediaPipe FaceMesh model.
        """
        mp_face = mp.solutions.face_mesh
        self.face_mesh = mp_face.FaceMesh(refine_landmarks=refine_landmarks)
        self.landmarks = None

    def process_frame(self, frame):
        """
        Processes a single video frame to find face landmarks.
        
        Args:
            frame: A BGR video frame from OpenCV.
            
        Returns:
            A list of MediaPipe landmarks if a face is detected, otherwise None.
        """
        # Convert BGR (OpenCV) to RGB (MediaPipe)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False # Optimize
        
        results = self.face_mesh.process(rgb_frame)
        
        rgb_frame.flags.writeable = True # Revert

        if results.multi_face_landmarks:
            # Assume only one face
            self.landmarks = results.multi_face_landmarks[0].landmark
            return self.landmarks
        
        self.landmarks = None
        return None