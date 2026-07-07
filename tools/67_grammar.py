# -*- coding: utf-8 -*-
# 맵 압축 문법 브루트포스: (litK, rleK, zero특수, 헤더스킵) 조합 → 행시작 오프셋과 구조적 셀로 채점
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
    """타일이 2색 이상(단색 아님)인가"""
    base = t*32
    return len(set(tiles[base:base+32])) > 1

tm = json.load(open(os.path.join(WORK, 'truemap.json'), encoding='utf-8'))
truth = {}
for cx, cy, (t, p, hf, vf) in tm:
    if t < ntiles and structured(t):
        truth[(cx, cy)] = t | (hf<<10) | (vf<<11) | (p<<12)
print(f'구조적 진짜셀: {len(truth)}')

def decode(raw, pre, litK, rleK, zmode, maxout=4096):
    """zmode: 0=0x00도 리터럴ctrl, 1=0x00이면 다음바이트=RLE카운트(투명0), 2=0x00이면 다음바이트=리터럴수"""
    out = []
    pos = pre
    n = len(raw)
    while pos < n and len(out) < maxout:
        c = raw[pos]; pos += 1
        if c == 0 and zmode == 1:
            if pos >= n: break
            out += [0]*(raw[pos]+1); pos += 1
        elif c == 0 and zmode == 2:
            if pos >= n: break
            k = raw[pos]+1; pos += 1
            for _ in range(k):
                if pos+2 > n: return out
                out.append(struct.unpack_from('<H', raw, pos)[0]); pos += 2
        elif c < 0x80:
            for _ in range(c + litK):
                if pos+2 > n: return out
                out.append(struct.unpack_from('<H', raw, pos)[0]); pos += 2
        else:
            if pos+2 > n: return out
            e = struct.unpack_from('<H', raw, pos)[0]; pos += 2
            out += [e]*((c & 0x7f) + rleK)
    return out

best = []
for pre in range(4):
    for litK in (0, 1, 2):
        for rleK in (1, 2, 3):
            for zmode in (0, 1, 2):
                for W in (32, 64):
                    ent = decode(raw, pre, litK, rleK, zmode)
                    if not (600 <= len(ent) <= 2200): continue
                    sc = 0
                    for (cx, cy), e in truth.items():
                        i = cy*W + cx
                        if i < len(ent) and ent[i] == e: sc += 1
                    best.append((sc, pre, litK, rleK, zmode, W, len(ent)))
best.sort(reverse=True)
for sc, pre, litK, rleK, zmode, W, ln in best[:10]:
    print(f'점수={sc}/{len(truth)} pre={pre} litK={litK} rleK={rleK} zmode={zmode} W={W} 해제엔트리={ln}')
