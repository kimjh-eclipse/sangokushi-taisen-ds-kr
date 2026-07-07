# -*- coding: utf-8 -*-
# 지정 클라이언트 좌표 클릭 + 프레임버퍼 스크린샷
import ctypes, time, os, sys, glob
from ctypes import wintypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def force_focus(h):
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    ft = user32.GetWindowThreadProcessId(fg, None)
    tt = user32.GetWindowThreadProcessId(h, None)
    user32.AttachThreadInput(cur, ft, True); user32.AttachThreadInput(cur, tt, True)
    user32.BringWindowToTop(h); user32.SetForegroundWindow(h)
    time.sleep(0.4)
    user32.AttachThreadInput(cur, ft, False); user32.AttachThreadInput(cur, tt, False)

def click_client(h, cx, cy):
    x, y, w, hh = emu.client_rect(h)
    sx, sy = x + cx, y + cy
    user32.SetCursorPos(sx, sy)
    time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.15)
    user32.mouse_event(4, 0, 0, 0, 0); time.sleep(0.3)

def quickshot(h, tag):
    before = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png"))
    user32.SendMessageW(h, 0x111, 130, 0)
    time.sleep(1.0)
    new = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png")) - before
    if new:
        p = new.pop()
        dst = os.path.join(WORK, f"fb_{tag}.png")
        if os.path.exists(dst): os.remove(dst)
        os.rename(p, dst)
        return dst
    return None

if __name__ == "__main__":
    h = emu.find_window()
    args = sys.argv[1:]
    tag = args[0]
    clicks = [(int(args[i]), int(args[i+1])) for i in range(1, len(args)-1, 2)]
    if clicks:
        force_focus(h)
        for cx, cy in clicks:
            click_client(h, cx, cy)
        time.sleep(2)
    p = quickshot(h, tag)
    print("shot:", p)
