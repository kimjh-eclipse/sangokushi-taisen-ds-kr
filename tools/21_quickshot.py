# -*- coding: utf-8 -*-
# WM_COMMAND(130) = Quick Screenshot 트리거 → 저장 위치 확인
import ctypes, time, os, glob, sys
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import emu

user32 = ctypes.windll.user32
h = emu.find_window()
WM_COMMAND = 0x111
before = set(glob.glob(r"C:\Emul\Desmume\*.png")) | set(glob.glob(r"C:\Emul\Desmume\**\*.png", recursive=True))
user32.SendMessageW(h, WM_COMMAND, 130, 0)
time.sleep(1.5)
after = set(glob.glob(r"C:\Emul\Desmume\*.png")) | set(glob.glob(r"C:\Emul\Desmume\**\*.png", recursive=True))
new = after - before
print("new files:", new)
if not new:
    # ini에서 스크린샷 경로 확인
    ini = r"C:\Emul\Desmume\desmume.ini"
    if os.path.exists(ini):
        for line in open(ini, encoding="utf-8", errors="replace"):
            if "creen" in line or "Path" in line.strip():
                print(line.rstrip())
