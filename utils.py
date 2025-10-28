# utils.py
"""
Contains general-purpose utility functions, including math helpers
for averaging points, calculating blink ratios, and smoothing values.
"""

import pyautogui

# --- Get screen dimensions once for global use.
SCREEN_W, SCREEN_H = pyautogui.size()

def avg_pt(lm, idx, w, h):
    """Calculates the average (x, y) pixel coordinate for a list of landmark indices."""
    x = sum(lm[i].x * w for i in idx) / len(idx)
    y = sum(lm[i].y * h for i in idx) / len(idx)
    return int(x), int(y)

def blink_ratio(lm, idx, w, h):
    """Calculates a robust width-to-height ratio for the eye to detect blinks."""
    try:
        # --- Get scaled pixel coordinates for all 6 eye points.
        p = [(lm[i].x * w, lm[i].y * h) for i in idx]
        
        # --- Calculate horizontal and average vertical distances.
        horizontal = abs(p[0][0] - p[3][0])
        vertical_1 = abs(p[1][1] - p[5][1])
        vertical_2 = abs(p[2][1] - p[4][1])
        avg_vertical = (vertical_1 + vertical_2) / 2.0
        
        # --- Calculate the final ratio, avoiding division by zero.
        ratio = horizontal / (avg_vertical + 1e-6)
        
        return ratio
    
    except Exception as e:
        # --- Return a safe value (eye open) if an error occurs.
        print(f"Blink ratio error: {e}")
        return 0.0

def smooth_val(prev, new, a):
    """Applies exponential-moving-average smoothing to a value."""
    if prev is None:
        return new
    # --- Linear interpolation: (new * factor) + (old * (1 - factor))
    return (new * a) + (prev * (1.0 - a))