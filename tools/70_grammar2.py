# -*- coding: utf-8 -*-
# 문법 브루트포스 2차: W=64 가설 + 확장 토큰(0x00/0x40대 변형)
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['TIT_1L1.SCM']
d = sang[off:off+sz]
mofs = struct.unpack_from('<8H', d, 0)[4]
raw = d[mofs:]
info = bgscm.parse(d)
tiles = info['tiles']
ntiles = len(tiles)//32

def structured(t):
    base = t*32
    return len(set(tiles[base:base+32])) > 1

tm = json.load(open(os.path.join(WORK, 'truemap_TIT_1L1.SCM.json'), encoding='utf-8'))
truth = {}
for cx, cy, (t, p, hf, vf) in tm:
    if t < ntiles and structured(t):
        truth[(cx, cy)] = t | (hf<<10) | (vf<<11) | (p<<12)
print(f'구조적 진짜셀 {len(truth)}')

def decode(pre, litK, rleK, z, hi):
    """z: 0x00 처리 (0=리터럴처럼, 1=다음바이트+1 투명런, 2=EOR정렬없음스킵1투명)
       hi: 0x40-0x7f 처리 (0=리터럴 c+litK 연장, 1=투명런 (c&0x3f)+1, 2=RLE (c&0x3f)+rleK)"""
    out = []
    pos = pre
    n = len(raw)
    while pos < n and len(out) < 4096:
        c = raw[pos]; pos += 1
        if c == 0 and z == 1:
            if pos >= n: break
            out += [0]*(raw[pos]+1); pos += 1
        elif c == 0 and z == 2:
            out.append(0)
        elif c < 0x40 or (c < 0x80 and hi == 0):
            for _ in range(c + litK):
                if pos+2 > n: return out
                out.append(struct.unpack_from('<H', raw, pos)[0]); pos += 2
        elif c < 0x80 and hi == 1:
            out += [0]*((c & 0x3f) + 1)
        elif c < 0x80 and hi == 2:
            if pos+2 > n: return out
            e = struct.unpack_from('<H', raw, pos)[0]; pos += 2
            out += [e]*((c & 0x3f) + rleK)
        else:
            if pos+2 > n: return out
            e = struct.unpack_from('<H', raw, pos)[0]; pos += 2
            out += [e]*((c & 0x7f) + rleK)
    return out

best = []
for pre in (0, 1, 2, 3, 4):
    for litK in (0, 1):
        for rleK in (1, 2, 3):
            for z in (0, 1, 2):
                for hi in (0, 1, 2):
                    for W in (32, 64):
                        ent = decode(pre, litK, rleK, z, hi)
                        sc = 0
                        for (cx, cy), e in truth.items():
                            i = cy*W + cx
                            if i < len(ent) and ent[i] == e: sc += 1
                        best.append((sc, pre, litK, rleK, z, hi, W, len(ent)))
best.sort(reverse=True)
for b in best[:12]:
    print(f'점수={b[0]}/{len(truth)} pre={b[1]} litK={b[2]} rleK={b[3]} z={b[4]} hi={b[5]} W={b[6]} 엔트리={b[7]}')
