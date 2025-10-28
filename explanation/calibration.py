# calibration.py
"""
Manages the calibration process, storing calibration points
and handling the mapping from camera coordinates to screen coordinates.
"""

import config
import utils

class Calibration:
    def __init__(self):
        self.cam_pts = {}
        self.labels = ["CENTER", "TL", "TR", "BL", "BR"]
        self.stage = -1  # -1 = inactive, 0-4 = calibrating
        self.calibrated = False

    def start(self):
        """Resets and starts the calibration process."""
        self.stage = 0
        self.calibrated = False
        self.cam_pts.clear()
        print("Calibration started.")
        return "Calibration started. Look at center then corners and press 1 to 5."

    def add_point(self, point_coords):
        """
        Adds a calibration point for the current stage.
        Returns a string for the voice assistant to speak.
        """
        if not (0 <= self.stage < 5):
            return None

        label = self.labels[self.stage]
        self.cam_pts[label] = point_coords
        print(f"✓ {label} point captured: {point_coords}")
        
        self.stage += 1
        
        if self.stage == 5:
            self.calibrated = True
            print("✓ Calibration complete.")
            return "Calibration complete."
        else:
            return f"{label} captured. Look at {self.labels[self.stage]} and press {self.stage+1}."

    def get_overlay_text(self):
        """Returns the appropriate instructional text for the camera overlay."""
        if 0 <= self.stage < 5:
            return f"Look {self.labels[self.stage]} & press {self.stage+1}"
        if not self.calibrated:
            return "Press 'c' to calibrate"
        return None

    def map_to_screen(self, x, y):
        """
        Maps a camera coordinate (x, y) to a screen coordinate
        based on the stored calibration points.
        """
        if not self.calibrated or len(self.cam_pts) < 5:
            return None

        # Get corner points
        left = self.cam_pts["TL"][0]
        right = self.cam_pts["TR"][0]
        top = self.cam_pts["TL"][1]
        bottom = self.cam_pts["BL"][1]

        # Prevent division by zero
        if right == left or bottom == top:
            return None

        # Normalize x, y coordinates (0.0 to 1.0)
        nx = (x - left) / (right - left)
        ny = (y - top) / (bottom - top)

        # Apply sensitivity (scales movement around the center)
        nx = 0.5 + (nx - 0.5) * config.SENS_X
        ny = 0.5 + (ny - 0.5) * config.SENS_Y

        # Clamp values between 0.0 and 1.0
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        return int(nx * utils.SCREEN_W), int(ny * utils.SCREEN_H)