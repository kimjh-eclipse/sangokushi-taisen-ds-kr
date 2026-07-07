# -*- coding: utf-8 -*-
# 원본 ROM 부팅 → 타이틀/메뉴 스크린샷
import sys, time, os
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

emu.kill()
emu.launch(os.path.join(BASE, "San Goku Shi Taisen (J).nds"), wait=30)
h = emu.find_window()
print("hwnd:", h)
emu.focus(h)
emu.shot(h, os.path.join(WORK, "shot_boot.png"))
# Start 누르고 메뉴로
emu.key(emu.VK["enter"]); time.sleep(3)
emu.shot(h, os.path.join(WORK, "shot_title2.png"))
emu.key(emu.VK["enter"]); time.sleep(3)
emu.shot(h, os.path.join(WORK, "shot_menu.png"))
print("done")
