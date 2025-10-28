# main.py
"""
Main application file that initializes all modules and runs the
main OpenCV loop to process gestures and user input.
"""

import cv2
import pyautogui
import time
import threading
import os

# --- Import all our custom Python modules ---
import config
import utils
from face_tracking import FaceTracker
from calibration import Calibration
from voice_assistant import VoiceController

def main():
    """The main function that runs the entire application."""
    
    # ===== 1. Initialization =====
    
    # --- Create the shared dictionary and lock for thread communication.
    shared_state = {
        'voice_active': False,
        'lock': threading.Lock()
    }
    
    # --- Initialize instances of our controller classes.
    tracker = FaceTracker()
    calib = Calibration()
    voice_control = VoiceController(shared_state)
    
    # --- Start the voice assistant logic on a separate background thread.
    voice_control.start_listener_thread()
    
    # --- Initialize the OpenCV camera.
    cap = cv2.VideoCapture(config.CAM_INDEX)
    
    # --- Check if the camera opened successfully.
    if not cap.isOpened():
        print(f"--- FATAL ERROR: Could not open camera {config.CAM_INDEX} ---")
        return
    else:
        print(f"Camera {config.CAM_INDEX} opened successfully.")
        
    # ===== 2. Setup Camera Window =====
    
    # --- Create and pin the small camera preview window to the top-right.
    cv2.namedWindow("Head + Voice Mouse", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Head + Voice Mouse", config.CAM_WIN_W, config.CAM_WIN_H)
    win_x = utils.SCREEN_W - config.CAM_WIN_W - 10
    win_y = 10
    cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

    # ===== 3. Main Loop State Variables =====
    
    # --- Initialize variables to track smoothing, blinks, and time.
    smooth_pos = [None, None]
    blink_frame_count = 0
    last_blink_event_times = []

    print("Press 'c' to calibrate. Press 'q' to quit.")
    voice_control.speak("Assistant ready.")

    # ===== 4. Main Application Loop =====
    while True:
        # --- Read a new frame from the camera.
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed.")
            time.sleep(0.5)
            continue

        # --- Flip the frame and get its dimensions.
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # --- Get all face landmarks from the frame.
        landmarks = tracker.process_frame(frame)

        # --- If a face was found, process gestures.
        if landmarks:
            # --- Get the stable nose position for tracking.
            nose_x, nose_y = utils.avg_pt(landmarks, config.nose_idx, w, h)
            cv2.circle(frame, (nose_x, nose_y), 5, (0, 255, 255), -1)

            # --- Calculate the average blink ratio for both eyes.
            r_left = utils.blink_ratio(landmarks, config.left_eye, w, h)
            r_right = utils.blink_ratio(landmarks, config.right_eye, w, h)
            blink_r = (r_left + r_right) / 2.0

            # --- Check if the eye is "closed" (past the blink threshold).
            if blink_r > config.BLINK_THRESH:
                blink_frame_count += 1
                cv2.putText(frame, "BLINK", (10, 40), 0, 1, (0, 0, 255), 2)

                # --- If eye is held closed, trigger click and check for triple-blink.
                if blink_frame_count >= config.BLINK_LIMIT:
                    # --- 1. Perform a single mouse click.
                    pyautogui.click()
                    
                    # --- 2. Check for triple-blink to toggle voice mode.
                    now_t = time.time()
                    last_blink_event_times.append(now_t)
                    # --- Purge old blinks from the list.
                    last_blink_event_times = [
                        t for t in last_blink_event_times 
                        if now_t - t <= config.TRIPLE_BLINK_WINDOW
                    ]
                    
                    # --- If 3+ blinks occurred, toggle voice mode.
                    if len(last_blink_event_times) >= 3:
                        with shared_state['lock']:
                            shared_state['voice_active'] = not shared_state['voice_active']
                            active = shared_state['voice_active']
                        
                        msg = "Voice mode activated." if active else "Voice mode deactivated."
                        voice_control.speak(msg)
                        last_blink_event_times.clear() # Reset

                    # --- Reset frame count to prevent rapid-fire clicks.
                    blink_frame_count = 0 
            else:
                # --- If eye is open, reset the blink counter.
                blink_frame_count = 0

            # --- If calibrated, move the mouse cursor.
            if calib.calibrated:
                # --- Map nose (x,y) to screen (x,y) using calibration data.
                mapped = calib.map_to_screen(nose_x, nose_y)
                if mapped:
                    # --- Apply smoothing to the cursor position.
                    smooth_pos[0] = utils.smooth_val(smooth_pos[0], mapped[0], config.SMOOTHING)
                    smooth_pos[1] = utils.smooth_val(smooth_pos[1], mapped[1], config.SMOOTHING)
                    
                    # --- Move the mouse.
                    try:
                        pyautogui.moveTo(int(smooth_pos[0]), int(smooth_pos[1]), duration=0.0)
                    except Exception:
                        pass # Ignore occasional errors

        # --- Draw calibration helper text on the frame.
        overlay_text = calib.get_overlay_text()
        if overlay_text:
            cv2.putText(frame, overlay_text, (10, 20), 0, 0.6, (0, 255, 255), 2)
            
        # --- Resize and display the final camera preview.
        preview = cv2.resize(frame, (config.CAM_WIN_W, config.CAM_WIN_H))
        cv2.imshow("Head + Voice Mouse", preview)
        # --- Keep the window pinned to the top-right.
        cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

        # --- Handle keyboard inputs (q, c, 1-5).
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break # Quit the main loop
        if key == ord('c'):
            msg = calib.start() # Start calibration
            voice_control.speak(msg)

        # --- Process calibration key presses (1-5).
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
    # --- Release the camera and close all windows when the loop exits.
    cap.release()
    cv2.destroyAllWindows()
    print("Exiting.")

if __name__ == "__main__":
    # --- Run the main() function when the script is executed.
    main()