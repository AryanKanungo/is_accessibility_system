# face_tracking.py
import cv2, mediapipe as mp, pyautogui, time
from utils import avg_pt, blink_ratio, map_to_screen, smooth_val
from config import *
from voice_assistant import speak, voice_active, voice_lock
from calibration import start_calibration
import threading

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)

def run_tracking():
    cap = cv2.VideoCapture(CAM_INDEX)
    smooth = [None, None]
    blink_frame_count = 0
    last_blink_event_times = []
    calibrated = False
    cam_pts = {}
    stage = -1

    print("Press 'c' to calibrate and 'q' to quit.")
    cv2.namedWindow("Head + Voice Mouse", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Head + Voice Mouse", CAM_WIN_W, CAM_WIN_H)
    win_x, win_y = SCREEN_W - CAM_WIN_W - 10, 10
    cv2.moveWindow("Head + Voice Mouse", win_x, win_y)

    while True:
        ok, frame = cap.read()
        if not ok: break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        res = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Draw and detect nose
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            x, y = avg_pt(lm, [1, 2, 4], w, h)
            cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)
            # Blink and control logic here (similar to your main code)

        preview = cv2.resize(frame, (CAM_WIN_W, CAM_WIN_H))
        cv2.imshow("Head + Voice Mouse", preview)
        cv2.moveWindow("Head + Voice Mouse", win_x, win_y)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
