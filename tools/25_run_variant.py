# -*- coding: utf-8 -*-
# 변조 ROM 부팅 → 오른손 확인 클릭 → 튜토리얼 대사 스크린샷
#   usage: 25_run_variant.py rom.nds tag
import os, sys, time, glob
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu
import importlib
c = importlib.import_module("23_click") if False else None

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
rompath, tag = sys.argv[1], sys.argv[2]

emu.kill(); time.sleep(1.5)

# 세이브 삭제 (첫부팅 흐름 고정)
for f in glob.glob(r"C:\Emul\Desmume\Battery\*.dsv"):
    base = os.path.basename(f)
    if "an Goku Shi Taisen" in base or "test_" in base:
        try: os.remove(f); print("removed save:", base)
        except PermissionError: print("locked:", base)
emu.launch(rompath, wait=32)
h = emu.find_window()

import ctypes
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def force_focus(hw):
    fg = user32.GetForegroundWindow()
    cur = kernel32.GetCurrentThreadId()
    ft = user32.GetWindowThreadProcessId(fg, None)
    tt = user32.GetWindowThreadProcessId(hw, None)
    user32.AttachThreadInput(cur, ft, True); user32.AttachThreadInput(cur, tt, True)
    user32.BringWindowToTop(hw); user32.SetForegroundWindow(hw)
    time.sleep(0.4)
    user32.AttachThreadInput(cur, ft, False); user32.AttachThreadInput(cur, tt, False)

def click_client(hw, cx, cy):
    x, y, w, hh = emu.client_rect(hw)
    user32.SetCursorPos(x + cx, y + cy); time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.15)
    user32.mouse_event(4, 0, 0, 0, 0); time.sleep(0.3)

def quickshot(hw, t):
    before = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png"))
    user32.SendMessageW(hw, 0x111, 130, 0); time.sleep(1.2)
    new = set(glob.glob(r"C:\Emul\Desmume\Screenshots\*.png")) - before
    if new:
        p = new.pop()
        dst = os.path.join(WORK, f"fb_{t}.png")
        if os.path.exists(dst): os.remove(dst)
        os.rename(p, dst); return dst

quickshot(h, tag + "_boot")
force_focus(h)
click_client(h, 1303, 290)   # はい
time.sleep(3)
p = quickshot(h, tag + "_dialog")
print("shot:", p)
