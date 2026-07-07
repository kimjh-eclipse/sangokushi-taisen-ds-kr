# -*- coding: utf-8 -*-
# 최선 문법으로 해제하며 (셀인덱스→스트림위치) 추적 → 행시작 실측 오프셋과 비교해 어긋나는 지점 규명
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

# 실측 행시작 (cell(0,cy) → 바이트오프셋) from 66_correlate
ROWSTART = {0:3, 1:43, 2:101, 3:159, 4:219, 5:281, 6:337, 7:392, 8:456, 9:520,
            10:584, 11:648, 12:702, 13:758, 14:822}

out = []
pos = 2
srcpos = []   # out index -> ctrl 토큰 시작 위치
n = len(raw)
tokens = []
while pos < n and len(out) < 1600:
    tp = pos
    c = raw[pos]; pos += 1
    if c < 0x80:
        cnt = c + 1
        vals = []
        for _ in range(cnt):
            if pos+2 > n: break
            v = struct.unpack_from('<H', raw, pos)[0]; pos += 2
            vals.append(v)
        tokens.append((tp, f'LIT{cnt}', vals))
        for v in vals:
            srcpos.append(tp); out.append(v)
    else:
        if pos+2 > n: break
        e = struct.unpack_from('<H', raw, pos)[0]; pos += 2
        cnt = (c & 0x7f) + 2
        tokens.append((tp, f'RLE{cnt}', [e]))
        for _ in range(cnt):
            srcpos.append(tp); out.append(e)

print(f'해제 {len(out)}엔트리, 토큰 {len(tokens)}개')
# 행시작 예측 vs 실측
for cy, exp_ofs in sorted(ROWSTART.items()):
    i = cy*32
    if i < len(srcpos):
        # cell(0,cy)가 리터럴이면 값위치=ctrl+1, 표에서 실측은 값 위치
        got = srcpos[i]
        print(f'행{cy:2d}: 실측 값오프셋={exp_ofs}  예측 ctrl오프셋={got} (값이면 +1={got+1})')
# 어긋나기 시작하는 행 주변 토큰 출력
print('\n토큰 나열 (오프셋 300~480):')
for tp, kind, vals in tokens:
    if 300 <= tp <= 480:
        vs = ' '.join(f'{v:04x}' for v in vals[:8])
        print(f'  @{tp}: {kind} {vs}')
