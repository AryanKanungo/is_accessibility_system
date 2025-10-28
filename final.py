# head_voice_mouse.py
import cv2, mediapipe as mp, pyautogui, numpy as np, time, threading, webbrowser, os, psutil
import speech_recognition as sr, pyttsx3
from datetime import datetime

# ===== Settings =====
SMOOTHING = 0.2
SENS_X, SENS_Y = 0.6, 0.6   # less sensitive
BLINK_THRESH, BLINK_LIMIT = 5.5, 2   # blink threshold and frames for click
CAM_INDEX = 0
CAM_WIN_W, CAM_WIN_H = 320, 240      # pinned camera window size (small)
TRIPLE_BLINK_WINDOW = 2.0            # seconds window to detect 3 blink events

# ===== Init =====
screen_w, screen_h = pyautogui.size()
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(CAM_INDEX)

nose_idx = [1, 2, 4]
left_eye = [33,160,158,133,153,144]
right_eye = [362,385,387,263,373,380]

cam_pts = {}            # calibration points dictionary
calib_labels = ["CENTER", "TL", "TR", "BL", "BR"]
stage = -1
calibrated = False

# Voice assistant resources (from user's code)
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# App database (user provided)
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "settings": "start ms-settings:"
}

# Shared state
smooth = [None, None]
voice_active = False             # toggled by 3-blink
voice_lock = threading.Lock()
listening_thread = None

# Blink tracking
blink_frame_count = 0            # frames with eyes closed (for click)
last_blink_event_times = []      # timestamps of distinct blink events (for triple-blink toggle)

# ===== Helper functions (simpler math) =====
def speak(text):
    # speak in a thread-safe way
    with voice_lock:
        print("Assistant:", text)
        engine.say(text)
        engine.runAndWait()

def listen_once(timeout=4, phrase_time_limit=5):
    """Listen once and return command string (or empty string)"""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(" Listening for command...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        command = recognizer.recognize_google(audio, language="en-in").lower()
        print(f" You said: {command}")
        return command
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("Voice error:", e)
        return ""

def avg_pt(lm, idx, w, h):
    x = sum(lm[i].x * w for i in idx) / len(idx)
    y = sum(lm[i].y * h for i in idx) / len(idx)
    return int(x), int(y)

def blink_ratio(lm, idx, w, h):
    p = [(lm[i].x*w, lm[i].y*h) for i in idx]
    horizontal = abs(p[0][0] - p[3][0])
    vertical = abs(p[1][1] - p[5][1]) + 1e-6
    return horizontal / vertical

def smooth_val(prev, new, a):
    if prev is None: return new
    return prev + (new - prev) * a

def map_to_screen(x, y):
    if len(cam_pts) < 5:
        return None
    left = cam_pts["TL"][0]
    right = cam_pts["TR"][0]
    top = cam_pts["TL"][1]
    bottom = cam_pts["BL"][1]
    nx = (x - left) / (right - left + 1e-6)
    ny = (y - top) / (bottom - top + 1e-6)
    nx = 0.5 + (nx - 0.5) * SENS_X
    ny = 0.5 + (ny - 0.5) * SENS_Y
    return int(nx * screen_w), int(ny * screen_h)

# ===== Voice assistant commands (extended) =====
def open_app(app_name):
    path = APPS.get(app_name)
    if path:
        speak(f"Opening {app_name}")
        try:
            os.startfile(path)
        except Exception as e:
            speak(f"Failed to open {app_name}")
            print("Open error:", e)
    else:
        speak(f"I don’t know how to open {app_name}")

def close_app(app_name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app_name.lower() in (proc.info['name'] or "").lower():
                speak(f"Closing {app_name}")
                proc.kill()
                return
        except Exception:
            continue
    speak(f"{app_name} is not running.")

def system_action(command):
    if "close window" in command:
        pyautogui.hotkey("alt", "f4")
        speak("Window closed.")
    elif "lock" in command:
        speak("Locking the system.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif "shutdown" in command:
        speak("Shutting down.")
        os.system("shutdown /s /t 1")
    elif "restart" in command:
        speak("Restarting system.")
        os.system("shutdown /r /t 1")
    elif "screenshot" in command:
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot saved.")
    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak("Volume up.")
    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak("Volume down.")
    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("Volume muted.")
    elif "show desktop" in command or "minimize all" in command:
        pyautogui.hotkey("win", "d")
        speak("Showing desktop.")

def execute_command(command):
    if not command:
        return
    # direct keywords
    if "open" in command:
        # search for app name
        for app in APPS:
            if app in command:
                open_app(app)
                return
        if "calculator" in command or "calc" in command:
            try:
                speak("Opening calculator")
                os.system("start calc")
            except Exception:
                speak("Cannot open calculator.")
                return
        # fallback to search
        if "search google for" in command:
            query = command.split("search google for", 1)[1].strip()
            if query:
                speak(f"Searching Google for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return
    elif "close" in command:
        for app in APPS:
            if app in command:
                close_app(app)
                return
        system_action(command)
        return

    # special commands
    if "search google for" in command:
        query = command.split("search google for", 1)[1].strip()
        if query:
            speak(f"Searching Google for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return

    if "youtube" in command and "open" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
        return

    if "what time" in command or "time is it" in command:
        now = datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
        return

    # mouse/scroll commands
    if "click" in command and "double" not in command:
        pyautogui.click()
        speak("Clicked.")
        return
    if "double click" in command or "double-click" in command:
        pyautogui.doubleClick()
        speak("Double clicked.")
        return
    if "scroll up" in command:
        pyautogui.scroll(500)
        speak("Scrolled up.")
        return
    if "scroll down" in command:
        pyautogui.scroll(-500)
        speak("Scrolled down.")
        return

    # fallback
    system_action(command)

# ===== Voice listener thread (only active when voice_active True) =====
def voice_listener_loop():
    global voice_active
    speak("Voice assistant thread started.")
    while True:
        with voice_lock:
            active = voice_active
        if not active:
            # sleep briefly if not active
            time.sleep(0.2)
            continue
        # If active, listen and execute
        command = listen_once(timeout=6, phrase_time_limit=6)
        if command:
            cmd = command.lower()
            if "exit voice" in cmd or "stop listening" in cmd:
                with voice_lock:
                    voice_active = False
                speak("Voice mode deactivated.")
            elif "quit assistant" in cmd or "shutdown assistant" in cmd:
                speak("Shutting down assistant.")
                os._exit(0)
            else:
                execute_command(cmd)
        else:
            # no command heard
            # short sleep to avoid busy loop (still active and listening repeatedly)
            time.sleep(0.2)

# Start voice listener thread (daemon)
t = threading.Thread(target=voice_listener_loop, daemon=True)
t.start()

# ===== Main Camera & Control Loop =====
print("Press 'c' to calibrate (look at center/corners, press 1–5). Press 'q' to quit.")
cv2.namedWindow("Head + Voice Mouse", cv2.WINDOW_NORMAL)
# move window to right side (top-right)
cv2.resizeWindow("Head + Voice Mouse", CAM_WIN_W, CAM_WIN_H)
win_x = screen_w - CAM_WIN_W - 10
win_y = 10
cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

while True:
    ok, frame = cap.read()
    if not ok:
        print("Camera read failed.")
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    # Process face landmarks
    res = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0].landmark
        x, y = avg_pt(lm, nose_idx, w, h)
        # Draw nose marker
        cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)

        # Blink detection (ratio average of both eyes)
        r = (blink_ratio(lm, left_eye, w, h) + blink_ratio(lm, right_eye, w, h)) / 2.0

        # For click: if eyes closed for BLINK_LIMIT consecutive frames -> click
        if r > BLINK_THRESH:
            blink_frame_count += 1
            cv2.putText(frame, "BLINK", (10, 40), 0, 1, (0, 0, 255), 2)
            if blink_frame_count >= BLINK_LIMIT:
                # Perform click action
                pyautogui.click()
                # Register a distinct blink event (timestamp)
                now_t = time.time()
                last_blink_event_times.append(now_t)
                # purge old events outside the triple-blink window
                last_blink_event_times = [t for t in last_blink_event_times if now_t - t <= TRIPLE_BLINK_WINDOW]
                # Check for 3 blink events
                if len(last_blink_event_times) >= 3:
                    # toggle voice activation
                    with voice_lock:
                        voice_active = not voice_active
                        active = voice_active
                    if active:
                        speak("Voice mode activated.")
                    else:
                        speak("Voice mode deactivated.")
                    last_blink_event_times.clear()
                # avoid repeated clicks while eyes still closed
                blink_frame_count = 0
        else:
            blink_frame_count = 0

        # Cursor movement when calibrated
        if calibrated:
            mapped = map_to_screen(x, y)
            if mapped:
                smooth[0] = smooth_val(smooth[0], mapped[0], SMOOTHING)
                smooth[1] = smooth_val(smooth[1], mapped[1], SMOOTHING)
                try:
                    pyautogui.moveTo(int(smooth[0]), int(smooth[1]), duration=0.02)
                except Exception as e:
                    print("pyautogui move error:", e)
        else:
            cv2.putText(frame, "Press 'c' to calibrate", (10, h - 20), 0, 0.6, (0, 0, 255), 1)

    # Calibration overlay
    if 0 <= stage < 5:
        cv2.putText(frame, f"Look {calib_labels[stage]} & press {stage+1}", (10, 20), 0, 0.6, (0, 255, 255), 2)

    # Resize small camera preview (so window is small and pinned)
    preview = cv2.resize(frame, (CAM_WIN_W, CAM_WIN_H))
    cv2.imshow("Head + Voice Mouse", preview)
    # ensure window stays pinned
    cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

    # Keys
    key = cv2.waitKey(1) & 0xFF
    if key == ord('c'):
        stage = 0
        calibrated = False
        cam_pts.clear()
        speak("Calibration started. Look at center then corners and press 1 to 5.")
        print("Calibration started.")
    if 0 <= stage < 5 and key == ord(str(stage + 1)) and res.multi_face_landmarks:
        cam_pts[calib_labels[stage]] = avg_pt(res.multi_face_landmarks[0].landmark, nose_idx, w, h)
        stage += 1
        time.sleep(0.2)
        if stage == 5:
            calibrated = True
            speak("Calibration complete.")
            print("✓ Calibrated")
    if key == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("Exiting.")
