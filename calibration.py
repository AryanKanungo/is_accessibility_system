# calibration.py
import time
from config import CALIB_LABELS

def start_calibration():
    print("Calibration started.")
    print("Look at each corner and press 1–5.")
    return 0, {}, False

def capture_point(stage, res, labels, lm_idx, w, h, avg_fn):
    cam_pts = {}
    if res.multi_face_landmarks:
        cam_pts[labels[stage]] = avg_fn(res.multi_face_landmarks[0].landmark, lm_idx, w, h)
        stage += 1
        time.sleep(0.2)
        if stage == len(labels):
            print("✓ Calibrated")
            return stage, cam_pts, True
    return stage, cam_pts, False
