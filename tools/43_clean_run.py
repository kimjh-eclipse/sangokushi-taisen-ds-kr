# -*- coding: utf-8 -*-
# 깨끗한 재실행: 기본 창(비최대화), PrintWindow로 렌더영역 측정, 프레임버퍼 대조
import ctypes, time, os, sys, glob
from ctypes import wintypes
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu
from PIL import Image

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

rompath = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "test_poc.nds")

emu.kill(); time.sleep(1.5)
for f in glob.glob(r"C:\Emul\Desmume\Battery\*.dsv"):
    if "an Goku" in os.path.basename(f) or "test_" in os.path.basename(f):
        try: os.remove(f)
        except: pass
emu.launch(rompath, wait=30)
h = emu.find_window()
# 최상단, 이동만(크기 유지)
user32.ShowWindow(h, 1)  # SW_SHOWNORMAL
time.sleep(0.3)
user32.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0040)  # NOSIZE|SHOWWINDOW, topmost
time.sleep(0.3)

# 창 전체 캡처 (PrintWindow)
r = wintypes.RECT(); user32.GetWindowRect(h, ctypes.byref(r))
W, H = r.right - r.left, r.bottom - r.top
hdc = user32.GetWindowDC(h)
mdc = gdi32.CreateCompatibleDC(hdc)
bmp = gdi32.CreateCompatibleBitmap(hdc, W, H)
gdi32.SelectObject(mdc, bmp)
ok = user32.PrintWindow(h, mdc, 2)
class BMIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
bmi = BMIH(biSize=ctypes.sizeof(BMIH), biWidth=W, biHeight=-H, biPlanes=1, biBitCount=32, biCompression=0)
buf = ctypes.create_string_buffer(W * H * 4)
gdi32.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bmi), 0)
img = Image.frombuffer("RGB", (W, H), buf, "raw", "BGRX", 0, 1)
img.save(os.path.join(WORK, "clean_win.png"))
gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(h, hdc)
print(f"PrintWindow ok={ok} winRect=({r.left},{r.top},{r.right},{r.bottom}) size={W}x{H}")

cx, cy, cw, ch = emu.client_rect(h)
print(f"client origin=({cx},{cy}) size={cw}x{ch}")
