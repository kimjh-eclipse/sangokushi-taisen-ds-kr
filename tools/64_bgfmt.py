# -*- coding: utf-8 -*-
# 비트맵(타일+맵) 서브포맷 분석: TIT_1L0(모드배너), NA_BGR01(이름등록BG)
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

for nm in (sys.argv[1:] or ['TIT_1L0.SCM', 'NA_BGR01.SCM', 'TIT_0L.SCM']):
    off, sz = files[nm]
    d = sang[off:off+sz]
    u16 = struct.unpack_from('<8H', d, 0)
    u32 = struct.unpack_from('<4I', d, 0x10)
    print(f'== {nm} (파일 {sz}B)')
    print('  u16[0..7]:', [hex(v) for v in u16])
    print('  u32@10,14,18,1c:', [hex(v) for v in u32])
    r = scmimg.decode(d)
    print('  sections:', r['sections'], 'endpos:', hex(r['endpos']))
    # endpos 이후 잔여
    rem = sz - r['endpos']
    print(f'  잔여 {rem}B @ {hex(r["endpos"])}:', d[r['endpos']:r['endpos']+16].hex())
    # gfx가 여러 LZ10 섹션의 연결일 가능성: sections에 이미 나옴
    g = r['gfx']
    print('  gfx head:', g[:16].hex(), ' tail:', g[-16:].hex())
