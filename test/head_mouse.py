import cv2, mediapipe as mp, pyautogui, numpy as np, time

# ===== Settings =====
SMOOTHING = 0.2
SENS_X, SENS_Y = 0.6, 0.6   # ↓ less sensitive
BLINK_THRESH, BLINK_LIMIT = 5.5, 2
CAM_INDEX = 0

# ===== Init =====
screen_w, screen_h = pyautogui.size()
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)
cap = cv2.VideoCapture(CAM_INDEX)
nose_idx, left_eye, right_eye = [1, 2, 4], [33,160,158,133,153,144], [362,385,387,263,373,380]
calib, cam_pts, smooth = {}, {}, [None, None]
calib_labels = ["CENTER", "TL", "TR", "BL", "BR"]
stage, calibrated = -1, False
blink_count = 0

# ===== Helpers =====
def avg_pt(lm, idx, w, h): 
    pts = [(lm[i].x*w, lm[i].y*h) for i in idx]
    return np.mean(pts,0).astype(int)

def blink_ratio(lm, idx, w, h):
    p=[(lm[i].x*w,lm[i].y*h) for i in idx]
    return (np.hypot(p[0][0]-p[3][0],p[0][1]-p[3][1])+1e-6)/(np.hypot(p[1][0]-p[5][0],p[1][1]-p[5][1])+1e-6)

def smooth_val(prev,new,a): return new if prev is None else prev*(1-a)+new*a

def map_to_screen(x,y):
    if len(cam_pts)<5: return None
    L=(cam_pts["TL"][0]+cam_pts["BL"][0])/2; R=(cam_pts["TR"][0]+cam_pts["BR"][0])/2
    T=(cam_pts["TL"][1]+cam_pts["TR"][1])/2; B=(cam_pts["BL"][1]+cam_pts["BR"][1])/2
    nx,ny=(x-L)/(R-L+1e-6),(y-T)/(B-T+1e-6)
    nx=(nx-0.5)*SENS_X+0.5; ny=(ny-0.5)*SENS_Y+0.5
    return (int(nx*screen_w), int(ny*screen_h))

# ===== Main Loop =====
print("Press 'c' to calibrate (look at center/corners, press 1–5). 'q' to quit.")
while True:
    ok, frame = cap.read()
    if not ok: break
    frame = cv2.flip(frame,1); h,w=frame.shape[:2]
    res = face_mesh.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0].landmark
        x,y = avg_pt(lm,nose_idx,w,h)
        cv2.circle(frame,(x,y),5,(0,255,255),-1)

        # Blink click
        r=(blink_ratio(lm,left_eye,w,h)+blink_ratio(lm,right_eye,w,h))/2
        if r>BLINK_THRESH:
            blink_count+=1; cv2.putText(frame,"BLINK",(10,40),0,1,(0,0,255),2)
            if blink_count>=BLINK_LIMIT: pyautogui.click(); blink_count=0
        else: blink_count=0

        if calibrated:
            mapped=map_to_screen(x,y)
            if mapped:
                smooth[0]=smooth_val(smooth[0],mapped[0],SMOOTHING)
                smooth[1]=smooth_val(smooth[1],mapped[1],SMOOTHING)
                pyautogui.moveTo(int(smooth[0]),int(smooth[1]),duration=0.02)
        else:
            cv2.putText(frame,"Press 'c' to calibrate",(10,h-20),0,0.7,(0,0,255),2)

    # Calibration flow
    if stage>=0 and stage<5:
        cv2.putText(frame,f"Look {calib_labels[stage]} & press {stage+1}",(10,30),0,0.8,(0,255,255),2)
    key=cv2.waitKey(1)&0xFF
    if key==ord('c'):
        stage,calibrated=0,False; cam_pts.clear(); print("Calibration started.")
    if 0<=stage<5 and key==ord(str(stage+1)) and res.multi_face_landmarks:
        cam_pts[calib_labels[stage]]=avg_pt(res.multi_face_landmarks[0].landmark,nose_idx,w,h)
        stage+=1; time.sleep(0.2)
        if stage==5: calibrated=True; print("✓ Calibrated")
    if key==ord('q'): break
    cv2.imshow("Head Mouse",frame)

cap.release(); cv2.destroyAllWindows()
