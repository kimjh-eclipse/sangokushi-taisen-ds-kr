# -*- coding: utf-8 -*-
# 이미 실행 중인 에뮬레이터에서 클릭 재시도 → 튜토리얼 대사 도달
import os, sys, time, glob, ctypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
h = emu.find_window()

def force_focus(hw):
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    ft = user32.GetWindowThreadProcessId(fg, None)
    tt = user32.GetWindowThreadProcessId(hw, None)
    user32.AttachThreadInput(cur, ft, True); user32.AttachThreadInput(cur, tt, True)
    user32.BringWindowToTop(hw); user32.SetForegroundWindow(hw)
    time.sleep(0.4)
    user32.AttachThreadInput(cur, ft, False); user32.AttachThreadInput(cur, tt, False)

def click(hw, cx, cy):
    x, y, w, hh = emu.client_rect(hw)
    user32.SetCursorPos(x + cx, y + cy); time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.15)
    user32.mouse_event(4, 0, 0, 0, 0); time.sleep(0.3)

def quickshot(hw, t):
    before = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png"))
    user32.SendMessageW(hw, 0x111, 130, 0); time.sleep(1.0)
    new = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png")) - before
    if new:
        p = new.pop()
        dst = os.path.join(WORK, f"fb_{t}.png")
        if os.path.exists(dst): os.remove(dst)
        os.rename(p, dst); return dst

force_focus(h)
for i, (cx, cy) in enumerate(sys.argv[1:] and
        [(int(sys.argv[j]), int(sys.argv[j+1])) for j in range(1, len(sys.argv)-1, 2)] or
        [(1303, 290), (1303, 290), (1303, 290)]):
    click(h, cx, cy)
    time.sleep(2.5)
    quickshot(h, f"adv{i}")
    print(f"adv{i} done")
