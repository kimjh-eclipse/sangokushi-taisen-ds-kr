# -*- coding: utf-8 -*-
# 창 포커스 후 실제 화면 캡처 → 창 레이아웃 파악
import ctypes, time, os, sys
from ctypes import wintypes
from PIL import ImageGrab
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
h = emu.find_window()

# AttachThreadInput 트릭으로 포커스 강제
kernel32 = ctypes.windll.kernel32
fg = user32.GetForegroundWindow()
cur_tid = kernel32.GetCurrentThreadId()
fg_tid = user32.GetWindowThreadProcessId(fg, None)
tgt_tid = user32.GetWindowThreadProcessId(h, None)
user32.AttachThreadInput(cur_tid, fg_tid, True)
user32.AttachThreadInput(cur_tid, tgt_tid, True)
user32.BringWindowToTop(h)
user32.SetForegroundWindow(h)
time.sleep(0.5)

x, y, w, hh = emu.client_rect(h)
print(f"client: origin=({x},{y}) size={w}x{hh}")
img = ImageGrab.grab(bbox=(x, y, x + w, y + hh))
img.save(os.path.join(WORK, "shot_window.png"))

user32.AttachThreadInput(cur_tid, fg_tid, False)
user32.AttachThreadInput(cur_tid, tgt_tid, False)
print("saved")
