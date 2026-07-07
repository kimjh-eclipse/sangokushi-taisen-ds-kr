# -*- coding: utf-8 -*-
# 미확인 CNCP 파일 전체 콘택트 시트 (각 파일 첫 2셀)
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
SKIP = ('MA2','NP_','NPS','BU_','FCE','CA_','NV_','FC_','ITE','HAI','KE_','TKE','C20','GET','SNAME','F_0','F_1','F_2','F_3','F_4','F_5','F_6','F_7','C0','C1','CC0','CC1')
SEEN = {'BTNALL.SCM','BTNALL2.SCM','DCHOOSE.SCM','BACKOBJ.SCM','FR_BTN.SCM','FR_BTN2.SCM','FR_BTN3.SCM',
        'KEYCH.SCM','TIT_OBJ.SCM','TITLE_OB.SCM','BMOJI.SCM','NACR01_1.SCM','NAMETAG.SCM','NAMPLATE.SCM',
        'EX_NO.SCM','AP.SCM','EDCR01_4.SCM','EDCL01_1.SCM','ED_BOTAN.SCM','ED_OKURI.SCM','ED_RESET.SCM',
        'ED_KOTEI.SCM','ED_BALL.SCM','ED_COST.SCM','ED_HEI.SCM','ED_KUNI.SCM','ED_MAGIC.SCM','ED_WAZA.SCM',
        'DEC_4.SCM','DEC_6.SCM'}
cands = [n for n, o, s in toc if n.endswith('.SCM') and not n.startswith(SKIP) and n not in SEEN]
files = {n: (o, s) for n, o, s in toc}
items = []
for nm in cands:
    off, sz = files[nm]
    try:
        r = scmimg.decode(sang[off:off+sz])
        g = r['gfx']
        if g[:4] != b'CNCP': continue
        info = cncp.parse(g)
        pal = scmimg.pal_to_rgb(r['pal'])
        ims = []
        for ci in range(min(2, len(info['cells']))):
            im, _, _ = cncp.render_cell(g, info['cells'][ci], pal)
            if im: ims.append(im)
        if ims: items.append((nm, len(info['cells']), ims))
    except Exception:
        continue
print(f'{len(items)}개 CNCP 파일')
COLS = 8
CW, CH = 120, 100
rows = (len(items)+COLS-1)//COLS
sheet = Image.new('RGB', (COLS*CW, rows*CH), (35, 35, 35))
dr = ImageDraw.Draw(sheet)
for k, (nm, nc, ims) in enumerate(items):
    X, Y = (k % COLS)*CW, (k // COLS)*CH
    dr.text((X+2, Y), f'{nm[:-4]}({nc})', fill=(255, 255, 0))
    x = X+2
    for im in ims:
        if im.width > 56 or im.height > 84:
            im = im.crop((0, 0, min(56, im.width), min(84, im.height)))
        sheet.paste(im, (x, Y+12), im)
        x += im.width + 4
sheet.save(os.path.join(WORK, 'contact_cncp.png'))
print('-> contact_cncp.png')
