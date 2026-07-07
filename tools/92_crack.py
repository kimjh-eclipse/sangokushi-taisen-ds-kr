# -*- coding: utf-8 -*-
# VRAM 평문 맵과 TIT_1L3 압축 스트림 정렬 → 코덱 해독
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom

SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['TIT_1L3.SCM']
d = sang[off:off+sz]
mofs = struct.unpack_from('<8H', d, 0)[4]
C = d[mofs:]
print('압축 스트림', len(C), 'B, head:', C[:24].hex(' '))

# 평문 후보 영역들에서 압축 스트림 초반 리터럴(u16들) 위치 찾기
lits = [C[3:3+2], C[3:3+6], C[3:3+12]]   # 헤더 2B + ctrl 1B 후 리터럴 가정
for tag, P0, P1 in (('A', 0x232800, 0x233800), ('B', 0x23d000, 0x23e000), ('C', 0x22c800, 0x22e000)):
    reg = raw[P0:P1]
    for probe_len in (12, 6):
        p = C[3:3+probe_len]
        i = reg.find(p)
        if i >= 0:
            print(f'영역{tag}: 스트림 리터럴 {probe_len}B → 평문오프셋 {i:#x} (엔트리 {i//2}, 홀짝 {i%2})')
            break
    else:
        print(f'영역{tag}: 리터럴 미발견')
