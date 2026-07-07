# -*- coding: utf-8 -*-
# 이름등록/메뉴 후보 SCM 탐색 렌더
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

targets = sys.argv[1:] or ['BTNALL2.SCM', 'KEYCH.SCM', 'NAMETAG.SCM', 'BMOJI.SCM',
                           'FR_BTN.SCM', 'FR_BTN2.SCM', 'FR_BTN3.SCM',
                           'TIT_OBJ.SCM', 'TITLE_OB.SCM', 'FON_TIT.SCM']
for nm in targets:
    if nm not in files:
        print(f'{nm}: 없음'); continue
    off, sz = files[nm]
    d = sang[off:off+sz]
    try:
        r = scmimg.decode(d)
    except Exception as e:
        print(f'{nm}: decode 실패 ({e}) size={sz}')
        continue
    h = r['hdr']
    gfx = r['gfx']
    tag = gfx[:4]
    print(f"{nm}: {h['w']}x{h['h']} colors={h['colors']} gfx={len(gfx)}B 매직={tag}")
    if tag == b'CNCP':
        try:
            pal = scmimg.pal_to_rgb(r['pal'])
            n = cncp.render_all(gfx, pal, os.path.join(WORK, f'cells_{nm}.png'), scale=2)
            print(f'  -> cells_{nm}.png ({n}셀)')
        except Exception as e:
            print(f'  CNCP 렌더 실패: {e}')
    else:
        # 비트맵형 추정: 타일 나열 렌더
        try:
            tw = max(1, h['w'] // 8)
            scmimg.render_4bpp_tiles(gfx, r['pal'], tw, 2, os.path.join(WORK, f'img_{nm}.png'))
            print(f'  -> img_{nm}.png (타일나열 {tw}열)')
        except Exception as e:
            print(f'  렌더 실패: {e}')
