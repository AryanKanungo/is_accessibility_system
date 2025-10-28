# config.py
import pyautogui

# General
SMOOTHING = 0.2
SENS_X, SENS_Y = 0.6, 0.6
BLINK_THRESH, BLINK_LIMIT = 5.5, 2
CAM_INDEX = 0
CAM_WIN_W, CAM_WIN_H = 320, 240
TRIPLE_BLINK_WINDOW = 2.0

# Screen
SCREEN_W, SCREEN_H = pyautogui.size()

# Calibration
CALIB_LABELS = ["CENTER", "TL", "TR", "BL", "BR"]

# Voice Assistant
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "settings": "start ms-settings:"
}
