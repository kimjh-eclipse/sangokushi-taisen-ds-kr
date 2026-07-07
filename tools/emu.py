# -*- coding: utf-8 -*-
# DeSmuME 자동화: 실행 / 키입력 / 터치클릭 / 스크린샷
import subprocess, time, ctypes, os, sys
from ctypes import wintypes
from PIL import ImageGrab

DESMUME = r"C:\Emul\Desmume\DeSmuME_0.9.13_x64.exe"
user32 = ctypes.windll.user32
try:
    # 퍼모니터 DPI 인식 v2 — 모니터 간 DPI 차이로 인한 좌표 가상화(클릭 빗나감) 방지
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    user32.SetProcessDPIAware()

_proc = None

def launch(rompath, wait=25):
    global _proc
    _proc = subprocess.Popen([DESMUME, rompath])
    time.sleep(wait)
    return _proc

def find_window():
    hwnd = ctypes.c_void_p(0)
    title = ctypes.create_unicode_buffer(256)
    found = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        user32.GetWindowTextW(h, title, 256)
        # 일시정지 시 제목이 'Paused', 실행 중엔 'DeSmuME ...' 또는 ROM 이름
        if ("DeSmuME" in title.value or title.value == "Paused"
                or "San Goku" in title.value) and user32.IsWindowVisible(h):
            found.append((h, title.value))
        return True
    user32.EnumWindows(cb, 0)
    return found[0][0] if found else None

def focus(hwnd):
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)

# SendInput 키보드
KEYEVENTF_KEYUP = 2
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]
class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]

def key(vk, hold=0.1):
    inp = INPUT(type=1); inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(hold)
    inp.ki.dwFlags = KEYEVENTF_KEYUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.15)

VK = {"enter": 0x0D, "x": 0x58, "z": 0x5A, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
      "a": 0x41, "s": 0x53, "q": 0x51, "w": 0x57, "space": 0x20, "shift": 0x10, "esc": 0x1B}

def client_rect(hwnd):
    r = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, r.right, r.bottom

def shot(hwnd, path):
    """PrintWindow로 포커스 없이 창 내용 캡처 (전체 창, 메뉴바 포함)"""
    from PIL import Image
    gdi32 = ctypes.windll.gdi32
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)  # PW_RENDERFULLCONTENT
    class BMIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
    bmi = BMIH(biSize=ctypes.sizeof(BMIH), biWidth=w, biHeight=-h, biPlanes=1, biBitCount=32, biCompression=0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    if path: img.save(path)
    return img

WM_KEYDOWN, WM_KEYUP = 0x100, 0x101
def pkey(hwnd, vk, hold=0.12):
    """PostMessage 방식 키입력 (포커스 불필요; DeSmuME가 수신하면 동작)"""
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
    time.sleep(hold)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, 0xC0000000)
    time.sleep(0.15)

def touch(hwnd, tx, ty):
    """DS 하단화면 좌표 (0-255, 0-191) -> 클라이언트 좌표로 클릭"""
    x, y, w, h = client_rect(hwnd)
    scale = w / 256
    sx = x + int(tx * scale)
    sy = y + int(h / 2 + ty * scale)   # 하단 화면은 클라이언트 아래 절반
    user32.SetCursorPos(sx, sy)
    time.sleep(0.1)
    user32.mouse_event(2, 0, 0, 0, 0)  # LBUTTONDOWN
    time.sleep(0.12)
    user32.mouse_event(4, 0, 0, 0, 0)  # LBUTTONUP
    time.sleep(0.2)

def kill():
    global _proc
    if _proc: _proc.kill(); _proc = None
    os.system("taskkill /f /im DeSmuME_0.9.13_x64.exe >nul 2>&1")
