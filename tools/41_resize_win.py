# -*- coding: utf-8 -*-
# DeSmuME 창을 복원+고정크기로, 화면 배율 1x 메뉴 적용 후 캡처
import ctypes, time, os, sys, glob
from ctypes import wintypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
h = emu.find_window()

# 복원(비최대화)
user32.ShowWindow(h, 9)   # SW_RESTORE
time.sleep(0.3)
# 크기 지정: 폭 540, 높이 830 (2화면 세로 2x 근처)
user32.SetWindowPos(h, 0, 100, 50, 560, 900, 0x0040)
time.sleep(0.3)

# View 메뉴에서 배율 관련 ID 확인용 덤프
menu = user32.GetMenu(h)
def walk(m, path=""):
    n = user32.GetMenuItemCount(m)
    for i in range(n):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetMenuStringW(m, i, buf, 256, 0x400)
        mid = user32.GetMenuItemID(m, i)
        sub = user32.GetSubMenu(m, i)
        t = buf.value
        if any(k in t for k in ("1x","2x","3x","Rotation","atio","otate","ize")):
            print(f"{path}[{i}] id={mid} {t!r}")
        if sub: walk(sub, path + t + ">")
walk(menu)

x, y, w, hh = emu.client_rect(h)
print(f"client origin=({x},{y}) size={w}x{hh}")
