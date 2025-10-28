# utils.py
"""
Contains general-purpose utility functions (also called "helpers").
These functions perform simple, reusable tasks like math calculations,
which keeps the main code files cleaner.
"""

import pyautogui

# Get the screen's width and height *once* when the program starts.
# This is more efficient than asking for it repeatedly.
SCREEN_W, SCREEN_H = pyautogui.size()

def avg_pt(lm, idx, w, h):
    """
    Calculates the average (x, y) pixel coordinate from a list of landmarks.
    
    This is used to find a stable "center" for tracking, like the nose,
    by averaging 3 landmark points instead of relying on just one.
    
    Args:
        lm (list): The full list of 478 landmarks from MediaPipe.
        idx (list): The list of *indices* we want to average (e.g., [1, 2, 4] for the nose).
        w (int): The width of the camera frame (to scale the coords).
        h (int): The height of the camera frame (to scale the coords).
    """
    # MediaPipe gives landmark coords as a ratio (0.0 to 1.0).
    # We multiply by the frame's width (w) and height (h) to get pixel values.
    
    # Calculate the average X coordinate
    x = sum(lm[i].x * w for i in idx) / len(idx)
    # Calculate the average Y coordinate
    y = sum(lm[i].y * h for i in idx) / len(idx)
    
    return int(x), int(y)

def blink_ratio(lm, idx, w, h):
    """
    Calculates a robust "eye aspect ratio" (EAR).
    This function returns the ratio of the eye's width to its average height.
    
    - A high number (e.g., > 5.5) means a CLOSED eye (big width, small height).
    - A low number (e.g., 2-4) means an OPEN eye.
    
    
    """
    try:
        # Get the (x, y) pixel coordinates for the 6 eye landmarks
        # specified in the 'idx' list (e.g., config.left_eye).
        p = [(lm[i].x * w, lm[i].y * h) for i in idx]
        
        # p[0] = Outer corner
        # p[3] = Inner corner
        # p[1], p[2] = Upper eyelid points
        # p[4], p[5] = Lower eyelid points
        
        # Calculate the horizontal distance (width) between the corners
        horizontal = abs(p[0][0] - p[3][0])
        
        # Calculate the first vertical distance (height)
        vertical_1 = abs(p[1][1] - p[5][1])
        
        # Calculate the second vertical distance (height)
        vertical_2 = abs(p[2][1] - p[4][1])
        
        # We average the two vertical distances to make the
        # measurement stable even if the head is slightly tilted.
        avg_vertical = (vertical_1 + vertical_2) / 2.0
        
        # Calculate the final ratio: Width / Average Height
        # We add 1e-6 (a tiny number) to prevent a "division by zero" error
        # if the eye is perfectly closed (avg_vertical = 0).
        ratio = horizontal / (avg_vertical + 1e-6)
        
        return ratio
    
    except Exception as e:
        # A safety catch in case landmarks are briefly lost
        print(f"Blink ratio error: {e}")
        return 0.0 # Return a "safe" value (eye open)

def smooth_val(prev, new, a):
    """
    Applies simple exponential smoothing to a value.
    This prevents the cursor from being jittery.
    
    Args:
        prev: The previous (old) smoothed value.
        new: The new, raw value (e.g., from the camera).
        a: The smoothing factor (from config.SMOOTHING, e.g., 0.2).
    """
    # If this is the first frame, there is no 'prev' value,
    # so just return the new value directly.
    if prev is None:
        return new
    
    # This is the smoothing formula:
    # (new_value * 20%) + (old_value * 80%)
    # This makes the cursor "glide" to the new position
    # instead of "jumping" there.
    return (new * a) + (prev * (1.0 - a))