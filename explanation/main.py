# main.py
"""
Main application file for the Head + Voice Mouse.

Initializes all modules (FaceTracker, Calibration, VoiceController)
and runs the main OpenCV loop to process camera input, handle gestures
(blinks, triple-blinks), and manage user input.
"""

import cv2
import pyautogui
import numpy as np
import time
import threading
import os

# Import custom modules
import config
import utils
from face_tracking import FaceTracker
from calibration import Calibration
from voice_assistant import VoiceController

def main():
    # ===== 1. Initialization =====
    
    # Shared state for communication between main thread and voice thread
    shared_state = {
        'voice_active': False,
        'lock': threading.Lock()
    }
    
    # Initialize modules
    tracker = FaceTracker()
    calib = Calibration()
    voice_control = VoiceController(shared_state)
    
    # Start the voice listener thread in the background
    voice_control.start_listener_thread()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    # ===== ADDED CAMERA CHECK =====
    if not cap.isOpened():
        print(f"--- FATAL ERROR ---")
        print(f"Could not open camera index .")
        print(f"Please check if the camera is connected or in use by another app.")
        print(f"If it is, try changing 'CAM_INDEX = 0' in config.py to 1 (or 2).")
        print(f"---------------------")
        return
    else:
        print(f"Camera {config.CAM_INDEX} opened successfully.")
        
    # ===== 2. Setup Camera Window =====
    cv2.namedWindow("Head + Voice Mouse", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Head + Voice Mouse", config.CAM_WIN_W, config.CAM_WIN_H)
    
    # Position window in top-right corner
    win_x = utils.SCREEN_W - config.CAM_WIN_W - 10
    win_y = 10
    cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

    # ===== 3. Main Loop State Variables =====
    smooth_pos = [None, None]
    blink_frame_count = 0
    last_blink_event_times = [] # For triple-blink detection

    print("Press 'c' to calibrate. Press 'q' to quit.")
    voice_control.speak("Assistant ready.")

    # ===== 4. Main Application Loop =====
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed.")
            time.sleep(0.5) # Wait a bit if cam fails
            continue

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # Process the frame to find landmarks
        landmarks = tracker.process_frame(frame)

        if landmarks:
            # Get nose position (our tracking point)
            nose_x, nose_y = utils.avg_pt(landmarks, config.nose_idx, w, h)
            cv2.circle(frame, (nose_x, nose_y), 5, (0, 255, 255), -1)

            # --- Blink Detection ---
            r_left = utils.blink_ratio(landmarks, config.left_eye, w, h)
            r_right = utils.blink_ratio(landmarks, config.right_eye, w, h)
            blink_r = (r_left + r_right) / 2.0

            if blink_r > config.BLINK_THRESH:
                blink_frame_count += 1
                cv2.putText(frame, "BLINK", (10, 40), 0, 1, (0, 0, 255), 2)

                if blink_frame_count >= config.BLINK_LIMIT:
                    # --- 1. Single Click ---
                    pyautogui.click()
                    
                    # --- 2. Triple-Blink Voice Toggle ---
                    now_t = time.time()
                    last_blink_event_times.append(now_t)
                    # Purge old events
                    last_blink_event_times = [
                        t for t in last_blink_event_times 
                        if now_t - t <= config.TRIPLE_BLINK_WINDOW
                    ]
                    
                    if len(last_blink_event_times) >= 3:
                        # Toggle voice activation
                        with shared_state['lock']:
                            shared_state['voice_active'] = not shared_state['voice_active']
                            active = shared_state['voice_active']
                        
                        msg = "Voice mode activated." if active else "Voice mode deactivated."
                        voice_control.speak(msg)
                        last_blink_event_times.clear() # Reset

                    # Avoid repeated clicks
                    blink_frame_count = 0 
            else:
                blink_frame_count = 0

            # --- Cursor Movement ---
            if calib.calibrated:
                mapped = calib.map_to_screen(nose_x, nose_y)
                if mapped:
                    # Apply smoothing
                    smooth_pos[0] = utils.smooth_val(smooth_pos[0], mapped[0], config.SMOOTHING)
                    smooth_pos[1] = utils.smooth_val(smooth_pos[1], mapped[1], config.SMOOTHING)
                    
                    try:
                        pyautogui.moveTo(int(smooth_pos[0]), int(smooth_pos[1]), duration=0.0)
                    except Exception:
                        pass # Ignore occasional pyautogui errors

        # --- Calibration Overlay Text ---
        overlay_text = calib.get_overlay_text()
        if overlay_text:
            cv2.putText(frame, overlay_text, (10, 20), 0, 0.6, (0, 255, 255), 2)
            
        # --- Show Camera Feed ---
        preview = cv2.resize(frame, (config.CAM_WIN_W, config.CAM_WIN_H))
        cv2.imshow("Head + Voice Mouse", preview)
        # Keep window pinned
        cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

        # --- Key Handling ---
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        if key == ord('c'):
            msg = calib.start()
            voice_control.speak(msg)

        # Handle calibration key presses (1-5)
        if 0 <= calib.stage < 5 and key == ord(str(calib.stage + 1)):
            if landmarks:
                point = utils.avg_pt(landmarks, config.nose_idx, w, h)
                msg = calib.add_point(point)
                if msg:
                    voice_control.speak(msg)
            else:
                print("Cannot calibrate: No face detected.")
                voice_control.speak("I can't see your face.")

    # ===== 5. Cleanup =====
    cap.release()
    cv2.destroyAllWindows()
    print("Exiting.")

if __name__ == "__main__":
    main()