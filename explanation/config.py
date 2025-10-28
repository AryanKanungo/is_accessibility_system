# config.py
"""
Stores all static configuration variables, thresholds,
and application paths for the assistant.
"""

# ===== Mouse Control Settings =====
SMOOTHING = 0.2              # Controls cursor smoothing (0.0 to 1.0, lower is smoother)
SENS_X, SENS_Y = 0.6, 0.6    # Mouse sensitivity (less than 1.0 is less sensitive)
BLINK_THRESH = 5.5           # Eye Aspect Ratio (EAR) threshold for detecting a blink
BLINK_LIMIT = 2              # Number of consecutive frames to count as a click
TRIPLE_BLINK_WINDOW = 2.0    # Seconds window to detect 3 blink events for voice toggle

# ===== Camera Settings =====
CAM_INDEX = 0                # Default camera index (0 is usually built-in)
CAM_WIN_W, CAM_WIN_H = 320, 240 # Pinned camera window size (small)

# ===== MediaPipe Landmark Indices =====
# Indices for the specific landmarks we track
nose_idx = [1, 2, 4]
left_eye = [33, 160, 158, 133, 153, 144]
right_eye = [362, 385, 387, 263, 373, 380]

# ===== Application Database =====
# Paths to applications for the voice assistant
# Use 'r' for raw strings to handle backslashes in paths
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "settings": "start ms-settings:",
    "calculator": "calc.exe" # Added calculator here
}