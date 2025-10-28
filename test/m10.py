import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import dlib
import math

# Initialize mediapipe face mesh for eye tracking
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Initialize dlib for blink detection
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
left_eye_landmarks = [36, 37, 38, 39, 40, 41]
right_eye_landmarks = [42, 43, 44, 45, 46, 47]
BLINK_RATIO_THRESHOLD = 5.7

# Screen and grid settings
screen_w, screen_h = pyautogui.size()
keyboard_start_y = screen_h // 2
grid_cols = 100
grid_rows = 30
key_width = screen_w // grid_cols
key_height = (screen_h // 2) // grid_rows

cam = cv2.VideoCapture(0)

eye_movement_threshold = 0.03
speed_multiplier = 0.04
pyautogui.moveTo(screen_w // 2, keyboard_start_y + (screen_h // 4))

# Blink detection helper functions from Test2.py
def midpoint(point1, point2):
    return (point1.x + point2.x) / 2, (point1.y + point2.y) / 2

def euclidean_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_blink_ratio(eye_points, facial_landmarks):
    corner_left = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    corner_right = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))
    
    horizontal_length = euclidean_distance(corner_left, corner_right)
    vertical_length = euclidean_distance(center_top, center_bottom)
    
    ratio = horizontal_length / vertical_length
    return ratio
 
# Function to track eye movements and move the cursor
def navigate_keyboard_by_grid(landmarks):
    left_eye = [landmarks[145], landmarks[159]]
    right_eye = [landmarks[374], landmarks[386]]
    
    avg_left_eye_y = (left_eye[0].y + left_eye[1].y) / 2
    avg_right_eye_y = (right_eye[0].y + right_eye[1].y) / 2
    avg_eye_y = (avg_left_eye_y + avg_right_eye_y) / 2
    avg_left_eye_x = (left_eye[0].x + left_eye[1].x) / 2
    avg_right_eye_x = (right_eye[0].x + right_eye[1].x) / 2
    avg_eye_x = (avg_left_eye_x + avg_right_eye_x) / 2

    eye_y_shift = avg_eye_y - 0.5
    eye_x_shift = avg_eye_x - 0.5

    cur_x, cur_y = pyautogui.position()

    if abs(eye_x_shift) > eye_movement_threshold:
        move_x = np.sign(eye_x_shift) * key_width
        cur_x = np.clip(cur_x + move_x, 0, screen_w)

    if abs(eye_y_shift) > eye_movement_threshold:
        move_y = np.sign(eye_y_shift) * key_height
        cur_y = np.clip(cur_y + move_y, keyboard_start_y, screen_h)

    pyautogui.moveTo(cur_x, cur_y)

# Main loop
while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to open camera")
        break
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blink detection with Dlib
    faces = detector(gray_frame)
    for face in faces:
        landmarks = predictor(gray_frame, face)

        left_eye_ratio = get_blink_ratio(left_eye_landmarks, landmarks)
        right_eye_ratio = get_blink_ratio(right_eye_landmarks, landmarks)
        blink_ratio = (left_eye_ratio + right_eye_ratio) / 2

        if blink_ratio > BLINK_RATIO_THRESHOLD:
            # Blink detected, trigger an action (e.g., click)
            pyautogui.click()

    # Eye tracking with MediaPipe
    output = face_mesh.process(rgb_frame)
    landmark_points = output.multi_face_landmarks
    if landmark_points:
        landmarks = landmark_points[0].landmark
        navigate_keyboard_by_grid(landmarks)

    cv2.imshow('Eye Controlled Keyboard with Blink Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
