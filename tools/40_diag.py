# -*- coding: utf-8 -*-
# 클릭 지점 진단: 좌표에 어떤 창이 있는지 + 창 스크린샷
import os, sys, time, ctypes
from ctypes import wintypes
from PIL import ImageGrab
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
h = emu.find_window()
x, y, w, hh = emu.client_rect(h)
print(f"client origin=({x},{y}) size={w}x{hh}")

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

for cx, cy in ((1303, 290), (949, 370)):
    pt = POINT(x + cx, y + cy)
    hw = user32.WindowFromPoint(pt)
    # 최상위 창 얻기
    GA_ROOT = 2
    root = user32.GetAncestor(hw, GA_ROOT)
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(root, buf, 256)
    print(f"point client({cx},{cy}) screen({pt.x},{pt.y}): window={buf.value!r} (h={root}, target={h})")

img = ImageGrab.grab(bbox=(x, y, x + w, y + hh))
img.save(os.path.join(WORK, "diag_window.png"))
print("saved diag_window.png")
