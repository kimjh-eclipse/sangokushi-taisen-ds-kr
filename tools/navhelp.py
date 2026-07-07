# -*- coding: utf-8 -*-
# DeSmuME 내비게이션 헬퍼: 포커스클릭 + 터치 + 스냅 (단계별 검증용)
import sys, time, glob, ctypes, os, shutil
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import emu

u = ctypes.windll.user32
SS = r'C:\Emul\Desmume\Screenshots'
DST = r'C:\Emul\Switch\패치유틸.xdeltaUI\work\npchk'

def hwnd():
    h = emu.find_window()
    if not h:
        raise SystemExit('DeSmuME 창 없음 (크래시?)')
    return h

def snap(h, tag):
    before = {p: os.path.getmtime(p) for p in glob.glob(SS + r'\*.png')}
    u.PostMessageW(h, 0x111, 130, 0)
    time.sleep(1.8)
    for p in glob.glob(SS + r'\*.png'):
        if p not in before or os.path.getmtime(p) > before[p]:
            dst = os.path.join(DST, f'nv_{tag}.png')
            shutil.copy(p, dst)
            return dst
    return None

def focus_click(h):
    """상단화면(터치 아님) 물리 클릭으로 포커스 확보 — 게임 입력엔 무해"""
    x, y, w, hh = emu.client_rect(h)
    u.SetCursorPos(x + w // 2, y + hh // 4)
    time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.08); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.7)

def touch_verified(h, tx, ty, tag, settle=3.0):
    """포커스클릭 → 터치 → 스냅. 스냅 경로 반환"""
    focus_click(h)
    emu.touch(h, tx, ty)
    time.sleep(settle)
    return snap(h, tag)

def banners(img_path, y0=192, y1=384):
    """하단화면에서 배너(연어색) 세로 스트립 x구간 검출 → [(x중심, y중심)]"""
    from PIL import Image
    img = Image.open(img_path).convert('RGB')
    px = img.load()
    cols = {}
    for x in range(256):
        c = 0
        for y in range(y0, y1):
            r, g, b = px[x, y]
            if r > 185 and 90 < g < 175 and 90 < b < 175:
                c += 1
        if c > 20: cols[x] = c
    runs = []
    for x in sorted(cols):
        if runs and x - runs[-1][1] <= 3: runs[-1][1] = x
        else: runs.append([x, x])
    out = []
    for a, b in runs:
        if b - a < 6: continue
        xc = (a + b) // 2
        ys = [y for y in range(y0, y1)
              if (lambda c: c[0] > 185 and 90 < c[1] < 175 and 90 < c[2] < 175)(px[xc, y])]
        if ys:
            out.append((xc, (min(ys) + max(ys)) // 2 - 192))
    return out
