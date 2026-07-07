# -*- coding: utf-8 -*-
# arm9 0x140000-0x143800 카드 소속명 영역: NUL종단 문자열 전수 + 미번역 검출 + 번역 추가
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ndspy.rom

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
a9 = bytes(rom.arm9)
data = json.load(open(os.path.join(WORK, 'arm9_new_out.json'), encoding='utf-8'))
have = {d['off'] for d in data}

TL = {
    '魏軍': '위군', '呉軍': '오군', '蜀軍': '촉군', '漢軍': '한군', '袁軍': '원군',
    '西涼軍': '서량군', '董卓軍': '동탁군', '呂布軍': '여포군', '馬超軍': '마초군',
    '南蛮軍': '남만군', '黄巾軍': '황건군', '袁紹軍': '원소군', '袁術軍': '원술군',
    '劉表軍': '유표군', '劉璋軍': '유장군', '孫堅軍': '손견군', '孫策軍': '손책군',
    '劉備軍': '유비군', '曹操軍': '조조군', '朝廷': '조정', '賊軍': '적군',
    '無所属': '무소속', '在野': '재야', '不明': '불명', '張角軍': '장각군',
    '陶謙軍': '도겸군', '公孫瓚軍': '공손찬군', '韓遂軍': '한수군', '張魯軍': '장로군',
    '劉焉軍': '유언군', '何進軍': '하진군',
}

# NUL 종단 문자열 스캔
found = {}
i = 0x140000
end = 0x143800
while i < end:
    if a9[i] == 0:
        i += 1; continue
    j = a9.find(b'\x00', i)
    if j < 0 or j - i > 24:
        i += 1; continue
    seg = a9[i:j]
    try:
        s = seg.decode('cp932')
    except Exception:
        i = j + 1; continue
    if any('一' <= c <= '鿿' for c in s):
        found.setdefault(s, []).append(i)
    i = j + 1

added = miss = 0
for s, offs in sorted(found.items()):
    tr = TL.get(s)
    status = []
    for off in offs:
        if off in have:
            status.append('기존')
        elif tr:
            nb = len(s.encode('cp932'))
            kb = len(tr) * 2
            if kb <= nb:
                data.append({'off': off, 'ko': tr}); have.add(off); added += 1
                status.append('추가')
            else:
                status.append(f'길이초과({kb}>{nb})')
        else:
            miss += 1
            status.append('번역없음')
    print(f'{s} x{len(offs)}: {tr or "-"} [{",".join(status[:6])}]')
json.dump(data, open(os.path.join(WORK, 'arm9_new_out.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'추가 {added}, 번역없음 {miss}, 총 {len(data)}')
