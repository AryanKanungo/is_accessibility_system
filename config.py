# config.py
"""
Stores all static configuration variables, thresholds,
and application paths for the assistant.
"""

# ===== Mouse Control Settings =====
# --- Tunable values for cursor feel, sensitivity, and blink detection.
SMOOTHING = 0.2
SENS_X, SENS_Y = 0.6, 0.6
BLINK_THRESH = 5.5
BLINK_LIMIT = 2
TRIPLE_BLINK_WINDOW = 2.0

# ===== Camera Settings =====
# --- Hardware settings for which camera to use and the preview window size.
CAM_INDEX = 0
CAM_WIN_W, CAM_WIN_H = 320, 240

# ===== MediaPipe Landmark Indices =====
# --- Specific landmark IDs from the MediaPipe model for tracking features.
nose_idx = [1, 2, 4]
left_eye = [33, 160, 158, 133, 153, 144]
right_eye = [362, 385, 387, 263, 373, 380]

# ===== Application Database =====
# --- Maps spoken app names to their executable file paths on the system.
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "settings": "start ms-settings:",
    "calculator": "calc.exe"
}