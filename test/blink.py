import cv2
import dlib
import math
import pyautogui

# Initialize dlib for blink detection
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Eye landmark indices for dlib's 68-point model
left_eye_landmarks = [36, 37, 38, 39, 40, 41]
right_eye_landmarks = [42, 43, 44, 45, 46, 47]

# Blink detection threshold
BLINK_RATIO_THRESHOLD = 5.7

# Helper functions
def midpoint(point1, point2):
    return (point1.x + point2.x) / 2, (point1.y + point2.y) / 2

def euclidean_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def get_blink_ratio(eye_points, facial_landmarks):
    corner_left = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    corner_right = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))
    
    horizontal_length = euclidean_distance(corner_left, corner_right)
    vertical_length = euclidean_distance(center_top, center_bottom)
    
    ratio = horizontal_length / vertical_length
    return ratio

# Open webcam
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to open camera")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)

        left_eye_ratio = get_blink_ratio(left_eye_landmarks, landmarks)
        right_eye_ratio = get_blink_ratio(right_eye_landmarks, landmarks)
        blink_ratio = (left_eye_ratio + right_eye_ratio) / 2

        if blink_ratio > BLINK_RATIO_THRESHOLD:
            # Blink detected, trigger click
            pyautogui.click()
            cv2.putText(frame, "BLINK DETECTED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 
                        1.2, (0, 0, 255), 2)

    cv2.imshow("Blink Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
