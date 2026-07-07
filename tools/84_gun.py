# -*- coding: utf-8 -*-
# 단독 '軍' 문자열 후보 조사 (arm9 + overlays)
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ndspy.rom

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
a9 = bytes(rom.arm9)

# 기존 번역 상태
data = json.load(open(os.path.join(BASE, 'work', 'arm9_new_out.json'), encoding='utf-8'))
for off in (0x139f18, 0x139f20, 0x139f28):
    for d in data:
        if d['off'] == off:
            print(f'기존번역 {off:#x}: {d["ko"]}')

# 단독 軍(8c 52) 뒤 NUL: 주변 16B와 함께
pat = b'\x8c\x52\x00'
st = 0
while True:
    i = a9.find(pat, st)
    if i < 0: break
    st = i + 1
    pre = a9[i-8:i]
    post = a9[i:i+8]
    # 앞이 텍스트 문자면 단독이 아님 (2바이트 문자 꼬리 감지 대략)
    print(f'{i:#x}: pre={pre.hex(" ")} post={post.hex(" ")}')
    if st > 0x150000: break

# 오버레이 전수
for ovId, ov in rom.loadArm9Overlays().items():
    d = bytes(rom.files[ov.fileID])
    st = 0
    while True:
        i = d.find(pat, st)
        if i < 0: break
        st = i + 1
        print(f'ov{ovId}(file{ov.fileID}) @{i:#x}: pre={d[i-8:i].hex(" ")} post={d[i:i+8].hex(" ")}')
