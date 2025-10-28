# utils.py
"""
Contains general-purpose utility functions, including math helpers
for averaging points, calculating blink ratios, and smoothing values.
"""

import pyautogui

# Get screen dimensions once
SCREEN_W, SCREEN_H = pyautogui.size()

def avg_pt(lm, idx, w, h):
    """
    Calculates the average (x, y) pixel coordinate for a list of landmark indices.
    """
    x = sum(lm[i].x * w for i in idx) / len(idx)
    y = sum(lm[i].y * h for i in idx) / len(idx)
    return int(x), int(y)

def blink_ratio(lm, idx, w, h):
    """
    Calculates a robust inverse eye aspect ratio.
    A larger number means the eye is more closed.
    
    This is a more stable version than the original.
    """
    try:
        # Get scaled pixel coordinates for all 6 points
        # [0]=corner, [1]=upper, [2]=upper, [3]=corner, [4]=lower, [5]=lower
        p = [(lm[i].x * w, lm[i].y * h) for i in idx]
        
        # Horizontal distance (between corners p0 and p3)
        horizontal = abs(p[0][0] - p[3][0])
        
        # Vertical distance 1 (outer: p1 to p5)
        vertical_1 = abs(p[1][1] - p[5][1])
        
        # Vertical distance 2 (inner: p2 to p4)
        vertical_2 = abs(p[2][1] - p[4][1])
        
        # Average vertical distance
        avg_vertical = (vertical_1 + vertical_2) / 2
        
        # Calculate the inverse ratio
        # (Add 1e-6 to avoid division by zero)
        ratio = horizontal / (avg_vertical + 1e-6)
        
        return ratio
    
    except Exception as e:
        print(f"Blink ratio error: {e}")
        return 0.0 # Return a safe value

def smooth_val(prev, new, a):
    """
    Applies exponential-moving-average smoothing to a value.
    'a' is the smoothing factor (e.g., config.SMOOTHING).
    """
    if prev is None:
        return new
    # Linear interpolation: prev * (1-a) + new * a
    return prev + (new - prev) * a