# -*- coding: utf-8 -*-
# NP 식자 검수 + 잔여 매핑 조사
import os, sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp
from PIL import Image, ImageDraw

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

# 1) 식자 결과 6종 렌더
sheet = Image.new('RGB', (6*110, 100), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k, np_id in enumerate((1, 4, 7, 25, 100, 160)):
    p = os.path.join(WORK, 'np_kr', f'NP_{np_id:04d}.SCM')
    if not os.path.exists(p):
        continue
    d = open(p, 'rb').read()
    r = scmimg.decode(d)
    info = cncp.parse(r['gfx'])
    pal = scmimg.pal_to_rgb(r['pal'])
    im, _, _ = cncp.render_cell(r['gfx'], info['cells'][0], pal)
    im = im.transpose(Image.ROTATE_90)
    sheet.paste(im, (k*110+4, 20), im)
    dr.text((k*110+4, 4), f'{np_id:04d}', fill=(255, 255, 0))
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'npkr_check.png'))

# 2) NP 파일 번호 분포와 col2=0 행들
nplist = sorted(int(n[3:7]) for n in files if n.startswith('NP_') and n[3:7].isdigit())
print('NP 번호: min', nplist[0], 'max', nplist[-1], '개수', len(nplist))
gaps = [i for i in range(nplist[0], nplist[-1]+1) if i not in set(nplist)]
print('빠진 번호 수:', len(gaps), gaps[:10])
off, sz = files['CARDS2.DAT']
d = sang[off:off+sz]
nl = b'\r\n' if b'\r\n' in d else b'\n'
rows = [ln.split(b',') for ln in d.split(nl)]
zero = [(ri, r[4].decode('cp932', errors='replace'), r[0].decode(), r[3].decode())
        for ri, r in enumerate(rows) if len(r) > 5 and r[2] == b'0' and r[4].strip()]
print('col2=0 행:', len(zero))
for z in zero[:12]: print(' ', z)
# col2 값 최대/유니크
vals = [int(r[2]) for r in rows if len(r) > 5 and r[2].isdigit()]
print('col2: 유니크', len(set(vals)), '최대', max(vals))
