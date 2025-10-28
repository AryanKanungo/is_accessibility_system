# calibration.py
"""
Manages the calibration process by acting as a "state machine".
It stores the 5 camera calibration points (e.g., "Top Left")
and contains the core math function 'map_to_screen' to translate
head position to cursor position.
"""

import config
import utils

class Calibration:
    """
    Holds the calibration state and all related logic.
    We create one instance of this class in main.py.
    """

    def __init__(self):
        """
        Initializes the state variables for the calibration process.
        """
        # This dictionary will store the (x, y) nose coordinates for each label.
        # e.g., self.cam_pts["TL"] = (210, 150)
        self.cam_pts = {}
        # The 5 labels for the 5 points we need to capture, in order.
        self.labels = ["CENTER", "TL", "TR", "BL", "BR"]
        # 'stage' tracks our progress:
        # -1 = Inactive
        #  0 = "Look CENTER, press 1"
        #  1 = "Look TL, press 2"
        # ...
        #  5 = Finished
        self.stage = -1
        # This boolean flag tells the main loop if it should start moving the mouse.
        self.calibrated = False

    def start(self):
        """
        Resets and starts the calibration process.
        This is called when the user presses 'c'.
        """
        # Set the stage to 0 (the first step: "CENTER")
        self.stage = 0
        # We are no longer calibrated
        self.calibrated = False
        # Clear any old points from the last calibration
        self.cam_pts.clear()
        print("Calibration started.")
        # Return the first voice prompt for the assistant to speak
        return "Calibration started. Look at center then corners and press 1 to 5."

    def add_point(self, point_coords):
        """
        Records a new calibration point when the user presses a key (1-5).
        
        Args:
            point_coords (tuple): The (x, y) coordinates of the nose to store.
            
        Returns:
            A string for the voice assistant to speak as feedback.
        """
        # Guard clause: If we are not in calibration mode (stage 0-4), do nothing.
        if not (0 <= self.stage < 5):
            return None

        # Get the correct label for the current stage (e.g., stage 1 = "TL")
        label = self.labels[self.stage]
        # Store the (x, y) coordinates in our dictionary
        self.cam_pts[label] = point_coords
        print(f"✓ {label} point captured: {point_coords}")
        
        # Advance to the next stage
        self.stage += 1
        
        # Check if calibration is finished
        if self.stage == 5:
            # All 5 points are captured. Mark as calibrated.
            self.calibrated = True
            print("✓ Calibration complete.")
            return "Calibration complete."
        else:
            # Provide feedback for the *next* step.
            return f"{label} captured. Look at {self.labels[self.stage]} and press {self.stage+1}."

    def get_overlay_text(self):
        """
        Returns the appropriate instructional text for the camera window.
        This is called every frame by main.py.
        """
        # If we are in the middle of calibrating (stages 0-4)
        if 0 <= self.stage < 5:
            return f"Look {self.labels[self.stage]} & press {self.stage+1}"
        # If we are not calibrated *and* not in the middle of calibrating
        if not self.calibrated:
            return "Press 'c' to calibrate"
        # If we are calibrated, return nothing
        return None

    def map_to_screen(self, x, y):
        """
        The core math function.
        Maps a camera coordinate (x, y) to a screen coordinate (x_screen, y_screen).
        
        Args:
            x (int): The current x-coordinate of the nose from the camera.
            y (int): The current y-coordinate of the nose from the camera.
        """
        # Guard clause: If we're not calibrated, don't move the mouse.
        if not self.calibrated or len(self.cam_pts) < 5:
            return None

        # --- Step 1: Get the "bounding box" of head movement ---
        # These are the min/max (x, y) values from our calibration.
        left = self.cam_pts["TL"][0]
        right = self.cam_pts["TR"][0]
        top = self.cam_pts["TL"][1]
        bottom = self.cam_pts["BL"][1]

        # Safety check to prevent dividing by zero if calibration is bad
        if right == left or bottom == top:
            return None

        # --- Step 2: Normalize the coordinates (0.0 to 1.0) ---
        # This converts the camera coordinate (e.g., 200-400)
        # into a standard 0.0 to 1.0 range.
        # Formula: (current_value - min_value) / (max_value - min_value)
        nx = (x - left) / (right - left)
        ny = (y - top) / (bottom - top)

        # --- Step 3: Apply Sensitivity ---
        # This scales the movement relative to the center (0.5).
        # A SENS_X of 0.6 makes the cursor 60% as sensitive,
        # giving you finer control.
        nx = 0.5 + (nx - 0.5) * config.SENS_X
        ny = 0.5 + (ny - 0.5) * config.SENS_Y

        # --- Step 4: Clamp the values (0.0 to 1.0) ---
        # This stops the cursor from flying off the screen
        # if you move your head *outside* the calibrated bounding box.
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        # --- Step 5: Scale to Screen Resolution ---
        # This converts the final 0.0-1.0 value to a pixel coordinate
        # (e.g., 0.5 * 1920 = 960).
        return int(nx * utils.SCREEN_W), int(ny * utils.SCREEN_H)