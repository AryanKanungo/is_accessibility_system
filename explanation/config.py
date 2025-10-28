# config.py
"""
Stores all static configuration variables, thresholds,
and application paths for the assistant.

This file acts as the main "settings" panel for the application.
"""

# ===== Mouse Control Settings =====

# SMOOTHING: Controls how "laggy" vs. "jittery" the cursor is.
# It's a weighted average: (new_pos * SMOOTHING) + (old_pos * (1 - SMOOTHING))
# A low value (e.g., 0.2) gives a very smooth, "gliding" feel.
# A high value (e.g., 0.8) is very responsive but can be jittery.
SMOOTHING = 0.2

# SENS_X, SENS_Y: Controls mouse sensitivity.
# A value of 1.0 would be 1-to-1 movement.
# A value < 1.0 (e.g., 0.6) makes the mouse *less* sensitive,
# meaning you have to move your head *more* to move the cursor,
# which gives you finer control for clicking small buttons.
SENS_X, SENS_Y = 0.6, 0.6

# BLINK_THRESH: The "closed-ness" threshold for your eye.
# This is the (width / height) ratio of your eye.
# An open eye has a low ratio (e.g., 2-4).
# A closed eye has a very high ratio (e.g., 8+).
# 5.5 is the trigger. If your blinks don't register, lower this (e.g., 5.0).
# If it clicks too easily, raise this (e.g., 6.0).
BLINK_THRESH = 5.5

# BLINK_LIMIT: The number of consecutive frames your eye must
# be "closed" (past the BLINK_THRESH) to register as a click.
# A value of 1 might be too sensitive (catching natural blinks).
# A value of 2 is perfect to distinguish an intentional "click-blink".
BLINK_LIMIT = 2

# TRIPLE_BLINK_WINDOW: The time (in seconds) you have to
# perform three blinks to toggle the voice assistant.
# 2.0 seconds is a comfortable window for a "blink-blink-blink" gesture.
TRIPLE_BLINK_WINDOW = 2.0

# ===== Camera Settings =====

# CAM_INDEX: The index of your camera.
# 0 is almost always the default built-in webcam.
# If you have multiple cameras, try 1, 2, etc.
CAM_INDEX = 0
# The size of the small, pinned camera preview window.
CAM_WIN_W, CAM_WIN_H = 320, 240

# ===== MediaPipe Landmark Indices =====
# These are the *specific landmark numbers* from the MediaPipe
# face model that correspond to these features.
# 

# We average these 3 nose points for a stable tracking anchor.
nose_idx = [1, 2, 4]
# The 6 points that outline the left eye.
left_eye = [33, 160, 158, 133, 153, 144]
# The 6 points that outline the right eye.
right_eye = [362, 385, 387, 263, 373, 380]

# ===== Application Database =====
# This dictionary maps the "spoken name" of an app
# to its actual file path or command on your system.
# The 'r' before the string (e.g., r"C:\...") is important
# as it tells Python to treat backslashes as literal characters.
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    # "start ms-settings:" is a special command to open Windows settings.
    "settings": "start ms-settings:",
    "calculator": "calc.exe"
}