# -*- coding: utf-8 -*-
# 동일 지오메트리(32x40) 셀들 픽셀 다수결 → 깨끗한 구슬 복원 검증
# 상태(눌림 등)별로 구슬 인덱스가 다른지도 확인
import os, sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
r = scmimg.decode(sang[files['BTNALL.SCM'][0]:files['BTNALL.SCM'][0]+files['BTNALL.SCM'][1]])
g = r['gfx']
info = cncp.parse(g)

def index_map(ci):
    """32x40 지오메트리 셀 → 40행x32열 인덱스 맵"""
    cell = info['cells'][ci]
    m = [[0]*32 for _ in range(40)]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)+20; y = cncp.sgn(a0&0xFF,8)+20
        tile = a2 & 0x3FF
        tw, th = w//8, h//8
        for ty in range(th):
            for tx in range(tw):
                tofs = cell['gfxBase'] + (tile+ty*tw+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs+yy*4+xx//2]
                        v = (b>>4) if (xx&1) else (b&0xF)
                        m[y+ty*8+yy][x+tx*8+xx] = v
    return m

# 32x40 지오메트리 셀 목록
std = [i for i,c in enumerate(info['cells'])
       if len(c['oams'])==2 and cncp.sgn(c['oams'][0][0]&0xFF,8)==-20]
print('32x40 셀:', std)
maps = {i: index_map(i) for i in std}

# 각 상태 그룹 가설: 버튼 3연속 (n, n+1, n+2). 같은 버튼 상태간 차이 확인
for a,b in ((0,1),(0,2),(6,7),(6,8),(12,13),(12,14)):
    diff = sum(1 for y in range(40) for x in range(32) if maps[a][y][x]!=maps[b][y][x])
    print(f'cell{a} vs cell{b}: 다른픽셀={diff}')

# 다수결 구슬 (상태0 그룹 = 각 버튼 첫번째 셀로 추정되는 것들로)
def majority(cells):
    m = [[0]*32 for _ in range(40)]
    for y in range(40):
        for x in range(32):
            c = Counter(maps[i][y][x] for i in cells)
            m[y][x] = c.most_common(1)[0][0]
    return m

grp0 = [0,6,9,12,15,18,24,36,44]  # 각 버튼 상태0(추정)
orb = majority(grp0)
# 검증: cell6/cell12과 다수결의 차이 픽셀수 (=글자 픽셀수여야)
for ci in (0,6,12):
    diff = sum(1 for y in range(40) for x in range(32) if maps[ci][y][x]!=orb[y][x])
    print(f'majority vs cell{ci}: 차이={diff}')
HEX='0123456789ABCDEF'
print('다수결 구슬:')
for row in orb:
    print('  '+''.join('.' if v==0 else HEX[v] for v in row))
json.dump(orb, open(os.path.join(WORK,'orb_state0.json'),'w'))
print('-> orb_state0.json 저장')
