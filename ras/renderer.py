import cv2
import math
import numpy as np

def draw_hud_box(frame, x1, y1, x2, y2, color, thickness):
    line_len = 40
    cv2.line(frame,(x1,y1),(x1+line_len,y1),color,thickness)
    cv2.line(frame,(x1,y1),(x1,y1+line_len),color,thickness)
    cv2.line(frame,(x2,y1),(x2-line_len,y1),color,thickness)
    cv2.line(frame,(x2,y1),(x2,y1+line_len),color,thickness)
    cv2.line(frame,(x1,y2),(x1+line_len,y2),color,thickness)
    cv2.line(frame,(x1,y2),(x1,y2-line_len),color,thickness)
    cv2.line(frame,(x2,y2),(x2-line_len,y2),color,thickness)
    cv2.line(frame,(x2,y2),(x2,y2-line_len),color,thickness)


def apply_glow(frame, overlay, kernel_size):
    overlay = cv2.GaussianBlur(overlay,(kernel_size,kernel_size),0)
    return cv2.addWeighted(frame,0.85,overlay,0.15,0)