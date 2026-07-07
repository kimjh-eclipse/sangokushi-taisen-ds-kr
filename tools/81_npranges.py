# -*- coding: utf-8 -*-
# NP 번호 범위 나열 + 범위별 샘플 렌더
import os, sys, json
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
nplist = sorted(int(n[3:7]) for n in files if n.startswith('NP_') and len(n) == 11 and n[3:7].isdigit())
# 연속 범위 압축
ranges = []
st = prev = nplist[0]
for v in nplist[1:]:
    if v == prev + 1:
        prev = v; continue
    ranges.append((st, prev)); st = prev = v
ranges.append((st, prev))
print('범위:', ranges)

samples = [r[0] for r in ranges][:14]
sheet = Image.new('RGB', (7*120, 2*90), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k, np_id in enumerate(samples):
    nm = f'NP_{np_id:04d}.SCM'
    off, sz = files[nm]
    try:
        r = scmimg.decode(sang[off:off+sz])
        info = cncp.parse(r['gfx'])
        pal = scmimg.pal_to_rgb(r['pal'])
        im, _, _ = cncp.render_cell(r['gfx'], info['cells'][0], pal)
        im = im.transpose(Image.ROTATE_90)
        X, Y = (k % 7)*120, (k // 7)*90
        sheet.paste(im, (X+4, Y+16), im)
        dr.text((X+4, Y+2), f'{np_id:04d}', fill=(255, 255, 0))
    except Exception as e:
        print(nm, '실패', e)
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'np_ranges.png'))
print('ok')
