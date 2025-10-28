# main.py
"""
The main application file (the "conductor").
This script is the entry point that:
1. Initializes all the other modules (FaceTracker, Calibration, VoiceController).
2. Sets up the threading for the voice assistant.
3. Runs the main, infinite `while True` loop to read the camera.
4. Processes gestures (blinks, triple-blinks) and moves the mouse.
5. Listens for keyboard inputs ('c', 'q', '1-5') to control the app.
"""

import cv2
import pyautogui
import time
import threading
import os

# Import our custom Python files
import config
import utils
from face_tracking import FaceTracker
from calibration import Calibration
from voice_assistant import VoiceController

def main():
    """The main function that runs the entire application."""
    
    # ===== 1. Initialization =====
    
    # This dictionary is the *only* thing shared between the main (camera)
    # thread and the background (voice) thread.
    # 'lock' is crucial: It prevents both threads from trying to
    # change 'voice_active' at the exact same time (a "race condition").
    shared_state = {
        'voice_active': False,
        'lock': threading.Lock()
    }
    
    # Create one instance of each of our helper classes
    tracker = FaceTracker()
    calib = Calibration()
    # Pass the shared_state to the voice controller so it can communicate
    voice_control = VoiceController(shared_state)
    
    # This is a key step: It starts the '_voice_listener_loop'
    # function from voice_assistant.py on a new, separate thread.
    # The 'daemon=True' (set inside the function) means this thread
    # will automatically die when this main.py script stops.
    voice_control.start_listener_thread()
    
    # Initialize the OpenCV camera capture
    cap = cv2.VideoCapture(config.CAM_INDEX)
    
    # --- Add a check to see if the camera actually opened ---
    if not cap.isOpened():
        print(f"--- FATAL ERROR ---")
        print(f"Could not open camera index {config.CAM_INDEX}.")
        print(f"Try changing 'CAM_INDEX = 0' in config.py to 1 (or 2).")
        print(f"Or, check if another app is using the camera.")
        return # Exit the program if the camera can't be opened
    else:
        print(f"Camera {config.CAM_INDEX} opened successfully.")
        
    # ===== 2. Setup Camera Window =====
    
    # Create the window
    cv2.namedWindow("Head + Voice Mouse", cv2.WINDOW_NORMAL)
    # Set its size based on the config file
    cv2.resizeWindow("Head + Voice Mouse", config.CAM_WIN_W, config.CAM_WIN_H)
    
    # Calculate the (x, y) coordinates to pin the window
    # to the top-right corner of the screen.
    win_x = utils.SCREEN_W - config.CAM_WIN_W - 10
    win_y = 10
    # Move the window to that position
    cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

    # ===== 3. Main Loop State Variables =====
    
    # Holds the [x, y] of the *smoothed* cursor position
    smooth_pos = [None, None]
    # Counts consecutive frames where the eye is closed (for clicks)
    blink_frame_count = 0
    # Stores timestamps of recent blinks (for triple-blink toggle)
    last_blink_event_times = []

    print("Press 'c' to calibrate. Press 'q' to quit.")
    # Queue the "Ready" message for the voice assistant to speak
    voice_control.speak("Assistant ready.")

    # ===== 4. Main Application Loop =====
    # This is the "heart" of the program. It runs for every single frame.
    while True:
        # --- A. Read Frame from Camera ---
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed.")
            time.sleep(0.5) # Wait a bit if cam fails
            continue

        # Flip the frame horizontally (like a mirror)
        frame = cv2.flip(frame, 1)
        # Get the frame's height (h) and width (w)
        h, w = frame.shape[:2]

        # --- B. Process Face Landmarks ---
        # Pass the frame to our FaceTracker class to find the 478 points
        landmarks = tracker.process_frame(frame)

        # --- C. If a Face is Found ---
        if landmarks:
            # Get the stable (x, y) coordinate for the nose
            nose_x, nose_y = utils.avg_pt(landmarks, config.nose_idx, w, h)
            # Draw a circle on the nose in the preview window
            cv2.circle(frame, (nose_x, nose_y), 5, (0, 255, 255), -1)

            # --- D. Blink Detection Logic ---
            # Get the blink ratio for both eyes
            r_left = utils.blink_ratio(landmarks, config.left_eye, w, h)
            r_right = utils.blink_ratio(landmarks, config.right_eye, w, h)
            # Average the two ratios for a more stable reading
            blink_r = (r_left + r_right) / 2.0

            # Check if the eye is "closed" (ratio is past our threshold)
            if blink_r > config.BLINK_THRESH:
                # If closed, increment the frame counter
                blink_frame_count += 1
                cv2.putText(frame, "BLINK", (10, 40), 0, 1, (0, 0, 255), 2)

                # Check if the eye has been held closed long enough
                if blink_frame_count >= config.BLINK_LIMIT:
                    
                    # --- 1. Trigger Single Click ---
                    pyautogui.click()
                    
                    # --- 2. Check for Triple-Blink (Voice Toggle) ---
                    now_t = time.time()
                    # Add this blink's timestamp to our list
                    last_blink_event_times.append(now_t)
                    
                    # "Purge" old blinks from the list that are
                    # outside our 2.0-second time window.
                    last_blink_event_times = [
                        t for t in last_blink_event_times 
                        if now_t - t <= config.TRIPLE_BLINK_WINDOW
                    ]
                    
                    # If we have 3 or more recent blinks, toggle voice
                    if len(last_blink_event_times) >= 3:
                        # Use the 'lock' to safely change the shared_state
                        with shared_state['lock']:
                            # Flip the boolean
                            shared_state['voice_active'] = not shared_state['voice_active']
                            active = shared_state['voice_active']
                        
                        # Prepare the feedback message
                        msg = "Voice mode activated." if active else "Voice mode deactivated."
                        # Send the message to the voice thread to be spoken
                        voice_control.speak(msg)
                        # Clear the list to prevent re-triggering
                        last_blink_event_times.clear()

                    # Reset the click counter to avoid rapid-fire clicks
                    blink_frame_count = 0
            else:
                # If the eye is open, reset the counter
                blink_frame_count = 0

            # --- E. Cursor Movement Logic ---
            # Only move the mouse if calibration is complete
            if calib.calibrated:
                # Use the calibration class to map nose (x,y) to screen (x,y)
                mapped = calib.map_to_screen(nose_x, nose_y)
                
                if mapped:
                    # Apply smoothing to the new (x, y) coordinates
                    smooth_pos[0] = utils.smooth_val(smooth_pos[0], mapped[0], config.SMOOTHING)
                    smooth_pos[1] = utils.smooth_val(smooth_pos[1], mapped[1], config.SMOOTHING)
                    
                    try:
                        # Move the mouse cursor to the smoothed position
                        pyautogui.moveTo(int(smooth_pos[0]), int(smooth_pos[1]), duration=0.0)
                    except Exception:
                        pass # Ignore occasional pyautogui errors

        # --- F. Draw Overlays ---
        # Get the helper text from the calibration class
        overlay_text = calib.get_overlay_text()
        if overlay_text:
            # Draw the text (e.g., "Press 'c' to calibrate") on the frame
            cv2.putText(frame, overlay_text, (10, 20), 0, 0.6, (0, 255, 255), 2)
            
        # --- G. Show the Camera Feed ---
        # Resize the final frame to the small preview size
        preview = cv2.resize(frame, (config.CAM_WIN_W, config.CAM_WIN_H))
        # Display the small frame in our window
        cv2.imshow("Head + Voice Mouse", preview)
        # Force the window to stay pinned in the top-right corner
        cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

        # --- H. Key Handling ---
        # Wait 1ms for a key press
        key = cv2.waitKey(1) & 0xFF

        # 'q' = Quit
        if key == ord('q'):
            break

        # 'c' = Start Calibration
        if key == ord('c'):
            msg = calib.start() # Reset the calibration state
            voice_control.speak(msg) # Speak the instructions

        # '1-5' = Calibration Steps
        # Check if we're in calibration (stage 0-4) AND
        # if the pressed key matches the current stage number
        if 0 <= calib.stage < 5 and key == ord(str(calib.stage + 1)):
            if landmarks:
                # Get the current nose position
                point = utils.avg_pt(landmarks, config.nose_idx, w, h)
                # Add this point to the calibration data
                msg = calib.add_point(point)
                # Speak the feedback (e.g., "Top left captured.")
                if msg:
                    voice_control.speak(msg)
            else:
                # User tried to calibrate but no face was found
                print("Cannot calibrate: No face detected.")
                voice_control.speak("I can't see your face.")

    # ===== 5. Cleanup =====
    # When the 'while True' loop is broken (by 'q'), release the camera...
    cap.release()
    # ...and close all OpenCV windows.
    cv2.destroyAllWindows()
    print("Exiting.")

# This "if" statement ensures that main() only runs
# when you execute this file directly (not when you import it).
if __name__ == "__main__":
    main()