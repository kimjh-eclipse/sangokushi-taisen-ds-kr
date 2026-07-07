# -*- coding: utf-8 -*-
import ctypes, time, os, sys
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu
WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
user32 = ctypes.windll.user32
h = emu.find_window()
# 최상단 + 좌상단 배치
HWND_TOPMOST = -1
user32.ShowWindow(h, 9); time.sleep(0.2)
user32.SetWindowPos(h, HWND_TOPMOST, 0, 0, 560, 900, 0x0040); time.sleep(0.3)
# PrintWindow로 전체 창 캡처 (포커스 무관)
img = emu.shot(h, os.path.join(WORK, "pw_layout.png"))
print("window img size:", img.size)
# 클라이언트 영역 크기
x, y, w, hh = emu.client_rect(h)
print("client:", x, y, w, hh)
