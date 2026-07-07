# -*- coding: utf-8 -*-
import ctypes, subprocess, time, os, sys
from ctypes import wintypes
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# 실행 중인 DeSmuME 있으면 나열, 없으면 실행
r = subprocess.run(["tasklist", "/fi", "imagename eq DeSmuME_0.9.13_x64.exe"], capture_output=True, text=True)
print(r.stdout.strip().splitlines()[-1] if r.stdout else "?")

title = ctypes.create_unicode_buffer(512)
wins = []
@ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def cb(h, l):
    if user32.IsWindowVisible(h):
        user32.GetWindowTextW(h, title, 512)
        if title.value.strip():
            wins.append((h, title.value))
    return True
user32.EnumWindows(cb, 0)
for h, t in wins:
    if "esmu" in t or "DeS" in t:
        rect = wintypes.RECT()
        user32.GetWindowRect(h, ctypes.byref(rect))
        cr = wintypes.RECT()
        user32.GetClientRect(h, ctypes.byref(cr))
        print(f"hwnd={h} title={t!r} rect=({rect.left},{rect.top},{rect.right},{rect.bottom}) client=({cr.right}x{cr.bottom})")
