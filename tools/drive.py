# -*- coding: utf-8 -*-
# DeSmuME 조작 헬퍼: 데스크톱 좌표 클릭(신뢰됨) + 프레임버퍼/데스크톱 캡처
import ctypes, time, os, glob, sys
from ctypes import wintypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu
from PIL import ImageGrab

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
u = ctypes.windll.user32; k = ctypes.windll.kernel32

def H(): return emu.find_window()

def focus_top():
    h = H()
    fg = u.GetForegroundWindow(); cur = k.GetCurrentThreadId()
    ft = u.GetWindowThreadProcessId(fg, None); tt = u.GetWindowThreadProcessId(h, None)
    u.AttachThreadInput(cur, ft, True); u.AttachThreadInput(cur, tt, True)
    u.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    u.BringWindowToTop(h); u.SetForegroundWindow(h); u.SetActiveWindow(h)
    time.sleep(0.4)
    u.AttachThreadInput(cur, ft, False); u.AttachThreadInput(cur, tt, False)
    return h

def winrect(h):
    r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
    return r

def click_img(ix, iy):
    """focus_top 후의 데스크톱-grab 이미지 좌표 = winrect 상대"""
    h = H(); r = winrect(h)
    u.SetCursorPos(r.left + ix, r.top + iy); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.25)
    u.mouse_event(4, 0, 0, 0, 0); time.sleep(0.6)

def desktop(tag):
    h = focus_top(); r = winrect(h)
    img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
    img.save(os.path.join(WORK, tag + ".png")); return img

def fb(tag):
    h = H()
    b = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png"))
    u.SendMessageW(h, 0x111, 130, 0); time.sleep(0.9)
    n = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png")) - b
    if n:
        p = n.pop(); d = os.path.join(WORK, tag + ".png")
        if os.path.exists(d): os.remove(d)
        os.rename(p, d); return d

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "desktop": desktop(sys.argv[2])
    elif cmd == "fb": print(fb(sys.argv[2]))
    elif cmd == "click":
        focus_top()
        for i in range(2, len(sys.argv) - 1, 2):
            click_img(int(sys.argv[i]), int(sys.argv[i+1]))
        time.sleep(1.0)
        if len(sys.argv) % 2 == 1:  # trailing tag
            desktop(sys.argv[-1])
