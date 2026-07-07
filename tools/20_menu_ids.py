# -*- coding: utf-8 -*-
# DeSmuME 메뉴 열거 → 스크린샷/일시정지 등 커맨드 ID 확보
import ctypes, sys
from ctypes import wintypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

user32 = ctypes.windll.user32
h = emu.find_window()
menu = user32.GetMenu(h)

def walk(m, depth=0):
    n = user32.GetMenuItemCount(m)
    for i in range(n):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetMenuStringW(m, i, buf, 256, 0x400)  # MF_BYPOSITION
        mid = user32.GetMenuItemID(m, i)
        sub = user32.GetSubMenu(m, i)
        print("  " * depth + f"[{i}] id={mid} {buf.value!r}")
        if sub:
            walk(sub, depth + 1)

walk(menu)
