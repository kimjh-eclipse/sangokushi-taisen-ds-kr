# -*- coding: utf-8 -*-
# 프레임버퍼(256x384) 좌표로 터치 + 스크린샷. 화면 렌더 rect는 종횡비 유지 가정으로 계산.
import ctypes, time, os, sys, glob
from ctypes import wintypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
FB_W, FB_H = 256, 384

def force_focus(hw):
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    ft = user32.GetWindowThreadProcessId(fg, None)
    tt = user32.GetWindowThreadProcessId(hw, None)
    user32.AttachThreadInput(cur, ft, True); user32.AttachThreadInput(cur, tt, True)
    user32.BringWindowToTop(hw); user32.SetForegroundWindow(hw)
    time.sleep(0.4)
    user32.AttachThreadInput(cur, ft, False); user32.AttachThreadInput(cur, tt, False)

def screen_rect(hw):
    """클라이언트 안에서 DS화면이 그려지는 rect(종횡비 유지, 상단 툴바 제외 추정)"""
    cx, cy, cw, ch = emu.client_rect(hw)
    # 툴바 높이 추정: 창 상단 chrome 아래. DeSmuME 0.9.13 툴바 client 내부에는 없음(별도) → 0
    avail_w, avail_h = cw, ch
    scale = min(avail_w / FB_W, avail_h / FB_H)
    rw, rh = FB_W * scale, FB_H * scale
    ox = cx + (avail_w - rw) / 2
    oy = cy + (avail_h - rh) / 2
    return ox, oy, scale

def touch(hw, fx, fy):
    ox, oy, scale = screen_rect(hw)
    sx = int(ox + fx * scale)
    sy = int(oy + fy * scale)
    user32.SetCursorPos(sx, sy); time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.15)
    user32.mouse_event(4, 0, 0, 0, 0); time.sleep(0.3)
    return sx, sy

def shot(hw, tag):
    before = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png"))
    user32.SendMessageW(hw, 0x111, 130, 0); time.sleep(1.0)
    new = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png")) - before
    if new:
        p = new.pop(); dst = os.path.join(WORK, f"{tag}.png")
        if os.path.exists(dst): os.remove(dst)
        os.rename(p, dst); return dst

if __name__ == "__main__":
    h = emu.find_window()
    tag = sys.argv[1]
    pts = [(int(sys.argv[i]), int(sys.argv[i+1])) for i in range(2, len(sys.argv)-1, 2)]
    if pts:
        force_focus(h)
        for fx, fy in pts:
            sx, sy = touch(h, fx, fy)
            print(f"touch fb({fx},{fy}) -> screen({sx},{sy})")
            time.sleep(2.0)
    print("shot:", shot(h, tag))
