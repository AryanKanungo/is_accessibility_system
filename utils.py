# utils.py
def smooth_val(prev, new, a):
    if prev is None: return new
    return prev + (new - prev) * a

def avg_pt(lm, idx, w, h):
    x = sum(lm[i].x * w for i in idx) / len(idx)
    y = sum(lm[i].y * h for i in idx) / len(idx)
    return int(x), int(y)

def blink_ratio(lm, idx, w, h):
    p = [(lm[i].x*w, lm[i].y*h) for i in idx]
    horizontal = abs(p[0][0] - p[3][0])
    vertical = abs(p[1][1] - p[5][1]) + 1e-6
    return horizontal / vertical

def map_to_screen(x, y, cam_pts, screen_w, screen_h, sens_x, sens_y):
    if len(cam_pts) < 5:
        return None
    left = cam_pts["TL"][0]
    right = cam_pts["TR"][0]
    top = cam_pts["TL"][1]
    bottom = cam_pts["BL"][1]
    nx = (x - left) / (right - left + 1e-6)
    ny = (y - top) / (bottom - top + 1e-6)
    nx = 0.5 + (nx - 0.5) * sens_x
    ny = 0.5 + (ny - 0.5) * sens_y
    return int(nx * screen_w), int(ny * screen_h)
