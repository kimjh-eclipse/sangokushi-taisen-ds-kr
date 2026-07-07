# -*- coding: utf-8 -*-
# 모드선택 배너(TIT_1R) 한글 식자 1단계: 6개 스테이트에서 배너 레이어 추출·역매핑
#  각 상태: 엔진B BG2(8bpp 항등맵) → 셀별 (TIT_1R 타일, hf, vf, palrow) + 화면 렌더
import sys, os, json, zlib, struct
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm, scmimg
from PIL import Image

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
OUT = os.path.join(WORK, 'banner')
os.makedirs(OUT, exist_ok=True)
STATES = {k: rf'C:\Emul\Desmume\StateSlots\San Goku Shi Taisen (K).ds{k}' for k in range(1, 7)}
LCDM_OFF = 0x080f6d0 + 12
VMEM_OFF = 0x080e6b8 + 12
TILES_OFF = LCDM_OFF + 0x40000 + 0x10000   # B BG charBase4
SCR_OFF = LCDM_OFF + 0x40000 + 0x1000      # scrBase2 (항등맵이지만 확인용)

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['TIT_1R.SCM']
t1r = sang[off:off+sz]
t1r_info = bgscm.parse(t1r)
SRC = bytes(t1r_info['tiles'])
NT = t1r_info['ntiles']

def flip4(tb32, hf, vf):
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            b = tb32[y*4 + x//2]
            v = (b >> 4) if (x & 1) else (b & 0xF)
            sx = 7-x if hf else x
            sy = 7-y if vf else y
            if sx & 1: out[sy*4 + sx//2] |= v << 4
            else: out[sy*4 + sx//2] |= v
    return bytes(out)

LUT = {}
for t in range(NT):
    tb = SRC[t*32:(t+1)*32]
    for hf in (0, 1):
        for vf in (0, 1):
            LUT.setdefault(flip4(tb, hf, vf), (t, hf, vf))

def load_state(path):
    d = open(path, 'rb').read()
    return zlib.decompress(d[0x20:])

def extract(raw):
    """returns pal(256 rgb), img8(256x256 인덱스), cellmap{i:(t,hf,vf,prow)}"""
    pal = []
    for i in range(256):
        v, = struct.unpack_from('<H', raw, VMEM_OFF + 0x400 + i*2)
        pal.append(((v&31)<<3, ((v>>5)&31)<<3, ((v>>10)&31)<<3))
    idx = [[0]*256 for _ in range(256)]
    cellmap = {}
    for i in range(1024):
        tb8 = raw[TILES_OFF + i*64: TILES_OFF + (i+1)*64]
        cx, cy = (i % 32)*8, (i // 32)*8
        prow_set = set()
        for y in range(8):
            for x in range(8):
                v = tb8[y*8+x]
                idx[cy+y][cx+x] = v
                if v: prow_set.add(v >> 4)
        if len(set(tb8)) == 1:
            continue
        b4 = bytearray(32)
        for k in range(0, 64, 2):
            b4[k//2] = (tb8[k] & 0xF) | ((tb8[k+1] & 0xF) << 4)
        hit = LUT.get(bytes(b4))
        if hit:
            prow = max(prow_set) if prow_set else 0
            cellmap[i] = (hit[0], hit[1], hit[2], prow)
    return pal, idx, cellmap

def render(pal, idx, path):
    img = Image.new('RGB', (256, 256), (255, 0, 255))
    px = img.load()
    for y in range(256):
        for x in range(256):
            v = idx[y][x]
            if v: px[x, y] = pal[v]
    img.transpose(Image.ROTATE_90).save(path)

if __name__ == '__main__':
    allmaps = {}
    for k, path in STATES.items():
        raw = load_state(path)
        pal, idx, cm = extract(raw)
        render(pal, idx, os.path.join(OUT, f'state{k}.png'))
        allmaps[str(k)] = {str(i): v for i, v in cm.items()}
        # 인덱스 원본도 저장 (편집용)
        json.dump(idx, open(os.path.join(OUT, f'state{k}_idx.json'), 'w'))
        print(f'state{k}: 매핑 {len(cm)}셀')
    json.dump(allmaps, open(os.path.join(OUT, 'cellmaps.json'), 'w'))
    # 팔레트 저장 (상태1 기준)
    raw = load_state(STATES[1])
    pal, _, _ = extract(raw)
    json.dump(pal, open(os.path.join(OUT, 'pal.json'), 'w'))
    # 타일 공유 현황
    share = defaultdict(set)
    for k, cm in allmaps.items():
        for i, (t, hf, vf, p) in cm.items():
            share[t].add((k, int(i)))
    multi = {t: len(v) for t, v in share.items() if len({loc for loc in v}) > 6}
    print('다중참조 타일(>6회):', len(multi))
