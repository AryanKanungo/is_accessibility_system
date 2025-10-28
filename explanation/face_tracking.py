# face_tracking.py
"""
Encapsulates all the MediaPipe FaceMesh logic into a clean, reusable class.
Its only job is to find the 478 face landmarks in a given video frame.
This keeps the complex MediaPipe setup code out of main.py.
"""

import cv2
import mediapipe as mp

class FaceTracker:
    """
    This class wraps the MediaPipe FaceMesh model.
    We create one instance of this class in main.py, which loads the
    machine learning model into memory once.
    """
    
    def __init__(self, refine_landmarks=True):
        """
        Initializes the FaceMesh model when a FaceTracker object is created.
        """
        # Get the FaceMesh solution from MediaPipe's library
        mp_face = mp.solutions.face_mesh
        
        # Initialize the FaceMesh model.
        # refine_landmarks=True: This is CRITICAL. It tells MediaPipe to
        # return the full 478 landmarks (including eyes, lips, and eyebrows).
        # If False, it only returns 5 points, which is not enough for us.
        self.face_mesh = mp_face.FaceMesh(refine_landmarks=refine_landmarks)
        
        # A variable to store the latest landmarks found
        self.landmarks = None

    def process_frame(self, frame):
        """
        Processes a single video frame (from OpenCV) to find face landmarks.
        
        Args:
            frame: A BGR video frame from the OpenCV camera feed.
            
        Returns:
            A list of MediaPipe landmarks if a face is detected, otherwise None.
        """
        
        # --- Step 1: Convert Color Space ---
        # OpenCV reads video in BGR (Blue, Green, Red) format.
        # MediaPipe's model was trained on and expects RGB (Red, Green, Blue).
        # We must convert the color space for the model to work correctly.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # --- Step 2: Optimization ---
        # To improve performance, we tell Python that this 'rgb_frame'
        # is now "read-only". This allows MediaPipe to process it
        # more efficiently without trying to copy it.
        rgb_frame.flags.writeable = False
        
        # --- Step 3: Process the Frame ---
        # This is the main ML inference step. We "pass" the RGB frame
        # to the face_mesh model, and it returns all the data it found.
        results = self.face_mesh.process(rgb_frame)
        
        # --- Step 4: Revert Optimization ---
        # (This isn't strictly necessary for this app, but it's good practice)
        # We set the frame back to "writeable" in case we wanted
        # to draw on it later (which we do in main.py on the *original* frame).
        rgb_frame.flags.writeable = True

        # --- Step 5: Extract Landmarks ---
        # Check if the 'results' object actually found any faces
        if results.multi_face_landmarks:
            # results.multi_face_landmarks is a list of all faces found.
            # We assume we only care about the *first* face (index [0]).
            self.landmarks = results.multi_face_landmarks[0].landmark
            
            # Return the list of landmarks for this face
            return self.landmarks
        
        # If no face was found, return None
        self.landmarks = None
        return None