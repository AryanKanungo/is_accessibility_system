# face_tracking.py
"""
Encapsulates the MediaPipe FaceMesh logic for initializing the model
and processing video frames to find facial landmarks.
"""

import cv2
import mediapipe as mp

class FaceTracker:
    """Wraps the MediaPipe FaceMesh model into a simple class."""

    def __init__(self, refine_landmarks=True):
        """Initializes and loads the FaceMesh machine learning model."""
        mp_face = mp.solutions.face_mesh
        # --- We set refine_landmarks=True to get all 478 face points (needed for eyes).
        self.face_mesh = mp_face.FaceMesh(refine_landmarks=refine_landmarks)
        self.landmarks = None

    def process_frame(self, frame):
        """Processes a single video frame to find face landmarks."""
        
        # --- Convert BGR (OpenCV) to RGB (MediaPipe) for the model.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # --- Performance optimization: pass the frame by reference.
        rgb_frame.flags.writeable = False
        
        # --- Run the actual face landmark detection.
        results = self.face_mesh.process(rgb_frame)
        
        # --- Revert the optimization (good practice).
        rgb_frame.flags.writeable = True

        # --- If a face is found, get the landmarks for the first face.
        if results.multi_face_landmarks:
            self.landmarks = results.multi_face_landmarks[0].landmark
            return self.landmarks
        
        # --- Return None if no face was detected.
        self.landmarks = None
        return None