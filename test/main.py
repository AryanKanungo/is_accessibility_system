import cv2
import logging
from blink_detector import detect_blink
from eye_tracker import navigate_keyboard_by_grid
import gui
from utils import initialize_camera, initialize_face_mesh, initialize_dlib
from gui import launch_gui

logging.basicConfig(filename="eye_tracking.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize components
cam = initialize_camera()
face_mesh = initialize_face_mesh()
detector, predictor = initialize_dlib()

# Start GUI
app, gui = launch_gui()

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            logging.error("Failed to capture frame from camera.")
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect blink
        blink_detected = detect_blink(gray_frame, detector, predictor)
        gui.set_blink_detected(blink_detected)

        # Eye tracking
        output = face_mesh.process(rgb_frame)
        if output.multi_face_landmarks:
            navigate_keyboard_by_grid(output.multi_face_landmarks[0].landmark)

        # Update GUI
        gui.update_frame(frame)
        app.processEvents()

except Exception as e:
    logging.critical(f"Unexpected error: {str(e)}")

finally:
    cam.release()
    cv2.destroyAllWindows()
    logging.info("Program terminated gracefully.")
