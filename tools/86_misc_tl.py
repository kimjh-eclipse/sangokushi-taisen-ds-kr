# -*- coding: utf-8 -*-
# 0x140000 영역 잔여 미번역: Χ무장명/병법명/획득메시지 번역 추가
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ndspy.rom

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
a9 = bytes(rom.arm9)
data = json.load(open(os.path.join(WORK, 'arm9_new_out.json'), encoding='utf-8'))
have = {d['off'] for d in data}

# 무장명 사전 (CARDS2 원문↔한글)
src = json.load(open(os.path.join(WORK, 'cd_src', 'CARDS2.DAT.name.json'), encoding='utf-8'))
out = json.load(open(os.path.join(WORK, 'cd_out', 'CARDS2.DAT.name.json'), encoding='utf-8'))
namedict = {}
for it in src['items']:
    if it['col'] == 4:
        kor = out.get(f"{it['row']}_4")
        if kor: namedict[it['jp']] = kor
namedict.update({'雑兵': '잡병', '黄巾': '황건'})

TL = {
    '再建': '재건', '再起': '재기', '増援': '증원', '士気': '사기', '官軍': '관군',
    '正兵': '정병', '神速': '신속', '車輪': '차륜', '速軍': '속군', '遠弓': '원궁',
    '関羽': '관우', '馬超': '마초',
    '%s伝・右': '%s전・우', '%s伝・左': '%s전・좌',
    '%s伝・右を': '%s전・우를', '%s伝・左を': '%s전・좌를',
    '#入れ替えますか？': '#교체하시겠습니까?',
    '%sの宝玉を手に入れました': '%s의 보옥을 입수했습니다',
    '%sの戦器を手に入れました': '%s의 전기를 입수했습니다',
    '%sの戦器を装備しました': '%s의 전기 장비했습니다',
    'の兵法書を手に入れました': '의 병법서 입수했습니다',
    '装備しました': '장비했습니다',
    '手にいれました': '입수했습니다',
    '効果がアップしました': '효과가 상승했습니다',
    '効果時間がアップしました': '효과 시간이 상승했습니다',
    '回復量がアップしました': '회복량이 상승했습니다',
    '戦場で何かを発見しました': '전장에서 뭔가 발견했다',
}

found = {}
i = 0x140000
end = 0x143800
while i < end:
    if a9[i] == 0:
        i += 1; continue
    j = a9.find(b'\x00', i)
    if j < 0 or j - i > 26:
        i += 1; continue
    seg = a9[i:j]
    try:
        s = seg.decode('cp932')
    except Exception:
        i = j + 1; continue
    found.setdefault(s, []).append(i)
    i = j + 1

added = fail = 0
for s, offs in sorted(found.items()):
    tr = None
    if s in TL:
        tr = TL[s]
    elif s.startswith('Χ') and s[1:] in namedict:
        tr = 'Χ' + namedict[s[1:]]
    if not tr: continue
    nb = len(s.encode('cp932'))
    try:
        import korean
    except Exception:
        korean = None
    # 길이: cp932 기준 대략 (한글 2B/자, ・ 2B, 공백/ASCII 1B)
    kb = sum(2 if ord(c) > 0x7f else 1 for c in tr)
    if kb > nb:
        print(f'길이초과: {s} ({nb}) -> {tr} ({kb})')
        fail += 1
        continue
    for off in offs:
        if off in have: continue
        data.append({'off': off, 'ko': tr}); have.add(off); added += 1
json.dump(data, open(os.path.join(WORK, 'arm9_new_out.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'추가 {added}, 길이초과 {fail}, 총 {len(data)}')
