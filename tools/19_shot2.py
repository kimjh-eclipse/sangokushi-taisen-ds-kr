# -*- coding: utf-8 -*-
import sys, time, os
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
h = emu.find_window()
print("hwnd:", h)
img = emu.shot(h, os.path.join(WORK, "shot_pw1.png"))
print("size:", img.size)
# PostMessage로 Enter(Start) 시도 후 재캡처
emu.pkey(h, emu.VK["enter"]); time.sleep(2)
emu.shot(h, os.path.join(WORK, "shot_pw2.png"))
