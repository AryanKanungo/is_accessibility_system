# calibration.py
"""
Manages the calibration process, storing calibration points
and handling the mapping from camera coordinates to screen coordinates.
"""

import config
import utils

class Calibration:
    """Holds the calibration state and all related logic."""
    
    def __init__(self):
        """Initializes the calibration state variables."""
        self.cam_pts = {}
        self.labels = ["CENTER", "TL", "TR", "BL", "BR"]
        self.stage = -1  # -1 = inactive, 0-4 = calibrating
        self.calibrated = False

    def start(self):
        """Resets and starts the calibration process when 'c' is pressed."""
        self.stage = 0
        self.calibrated = False
        self.cam_pts.clear()
        print("Calibration started.")
        return "Calibration started. Look at center then corners and press 1 to 5."

    def add_point(self, point_coords):
        """Adds a calibration point for the current stage (1-5)."""
        # --- Do nothing if not in calibration mode.
        if not (0 <= self.stage < 5):
            return None

        # --- Get the label (e.g., "TL") and store the nose coordinates.
        label = self.labels[self.stage]
        self.cam_pts[label] = point_coords
        print(f"✓ {label} point captured: {point_coords}")
        
        # --- Advance to the next stage.
        self.stage += 1
        
        # --- If all 5 points are set, mark as calibrated and return.
        if self.stage == 5:
            self.calibrated = True
            print("✓ Calibration complete.")
            return "Calibration complete."
        else:
            # --- Otherwise, return feedback for the next step.
            return f"{label} captured. Look at {self.labels[self.stage]} and press {self.stage+1}."

    def get_overlay_text(self):
        """Returns the appropriate instructional text for the camera overlay."""
        # --- Show calibration step instructions.
        if 0 <= self.stage < 5:
            return f"Look {self.labels[self.stage]} & press {self.stage+1}"
        # --- Show prompt to start calibration.
        if not self.calibrated:
            return "Press 'c' to calibrate"
        return None

    def map_to_screen(self, x, y):
        """Maps a camera coordinate (x, y) to a screen coordinate."""
        # --- Don't move the mouse if not calibrated.
        if not self.calibrated or len(self.cam_pts) < 5:
            return None

        # --- Get the calibrated boundaries of head movement.
        left = self.cam_pts["TL"][0]
        right = self.cam_pts["TR"][0]
        top = self.cam_pts["TL"][1]
        bottom = self.cam_pts["BL"][1]

        # --- Prevent division by zero if calibration is bad.
        if right == left or bottom == top:
            return None

        # --- Normalize coordinates to a 0.0-1.0 range.
        nx = (x - left) / (right - left)
        ny = (y - top) / (bottom - top)

        # --- Apply sensitivity from the config file.
        nx = 0.5 + (nx - 0.5) * config.SENS_X
        ny = 0.5 + (ny - 0.5) * config.SENS_Y

        # --- Clamp values to prevent going off-screen.
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        # --- Scale the 0.0-1.0 value to the full screen resolution.
        return int(nx * utils.SCREEN_W), int(ny * utils.SCREEN_H)