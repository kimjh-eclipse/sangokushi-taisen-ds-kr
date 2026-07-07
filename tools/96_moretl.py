# -*- coding: utf-8 -*-
# 전투/도감/계급 잔여 arm9 번역 추가 (J↔K 동일바이트 스캔으로 발견된 미번역분)
#  → arm9_new_out.json에 병합 (55_build_final.py가 원문 NUL길이로 적용)
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, korean

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
aJ = bytes(ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds')).arm9)

# CARDS2 무장명 사전 (Χ블록용)
import nfp
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['CARDS2.DAT']
d = sang[off:off+sz]
nl = b'\r\n' if b'\r\n' in d else b'\n'
rows = [ln.split(b',') for ln in d.split(nl)]
ko = json.load(open(os.path.join(WORK, 'cd_out', 'CARDS2.DAT.name.json'), encoding='utf-8'))
namedict = {}
for ri, r in enumerate(rows):
    if len(r) < 5: continue
    kj = r[4].decode('cp932', errors='replace')
    kr = ko.get(f'{ri}_4', '')
    if kj and kr and kj not in namedict:
        namedict[kj] = kr

ENT = []  # (off, jp확인용, ko)

def add(off, jp, kor):
    ENT.append((off, jp, kor))

# ── 전투 상대 진영명 (구조체 내장이라 기존 스캔이 놓침) ──
add(0x140ae4, '董卓軍', '동탁군')

# ── 2자 계략명 별사본 (0x135cf4 존, \n 유무 2세트) ──
T2 = {'士気':'사기','車輪':'차륜','速軍':'속군','再起':'재기','増援':'증원',
      '正兵':'정병','神速':'신속','再建':'재건','遠弓':'원궁'}
for o in (0x135cf4,0x135cfc,0x135d04,0x135d0c,0x135d14,0x135d1c,0x135d24,0x135d2c,0x135d34,
          0x135d3c,0x135d44,0x135d4c,0x135d54,0x135d5c,0x135d64,0x135d6c,0x135d74,0x135d7c):
    end = aJ.find(b'\x00', o)
    jp = aJ[o:end].decode('cp932')
    base = jp.rstrip('\n')
    add(o, jp, T2[base] + ('\n' if jp.endswith('\n') else ''))

# ── 계략 요미가나 (이웃 번역 표기와 일치시킴: 재기법/충군법/촉군 대공세…) ──
YOMI = {
    'さいきのほう':'재기법', 'さいけんのほう':'재건법', 'れんかんのほう':'연환법',
    'そくぐんのほう':'속군법', 'ぞうえんのほう':'증원법', 'せいへいのほう':'정병법',
    'しょうぐんのほう':'충군법',
    'ごぐんのだいこうせい':'오군 대공세', 'ぎぐんのだいこうせい':'위군 대공세',
    'たぜいのだいこうせい':'타세 대공세', 'しんそくのだいこうせい':'신속 대공세',
    'しゃりんのだいこうせい':'차륜 대공세', 'とおゆみのだいこうせい':'원궁 대공세',
    'しょくぐんのだいこうせい':'촉군 대공세', 'せいりょうぐんのだいこうせい':'서량군 대공세',
    'えんしょうぐんのだいこうせい':'원소군 대공세',
}
for o in (0x135e38,0x135e58,0x135e88,0x135e98,0x135ea8,0x135eb8,0x135edc,
          0x135f98,0x135fc8,0x136010,0x136058,0x136070,0x1360a0,0x1360e8,0x136254,0x136274):
    end = aJ.find(b'\x00', o)
    jp = aJ[o:end].decode('cp932')
    base = jp.rstrip('\n')
    add(o, jp, YOMI[base] + ('\n' if jp.endswith('\n') else ''))

# ── 전투 메시지 짧은 것들 ──
add(0x13a194, '一瞬', '일순')
add(0x13a1e0, '#復活', '#부활')
add(0x13a1e8, '#敗退', '#패퇴')
add(0x13a1f0, '#勝利', '#승리')
add(0x13a210, '#伏兵', '#복병')
add(0x13a25c, '#計略', '#계략')

# ── 스테이지 제목/이벤트 ──
add(0x13f170, '揚州、攻略　その一', '양주, 공략 그 1')
add(0x13f184, '揚州、攻略　その二', '양주, 공략 그 2')
add(0x13f198, '揚州、攻略　その三', '양주, 공략 그 3')
add(0x13f39c, '出立', '출발')
add(0x13f3ac, '発見', '발견')
add(0x13ed88, '二○○年', '200년')

# ── 계급명 (개행 세트 0x13f528~) ──
NUM = {'一':'일','二':'이','三':'삼','四':'사','五':'오','六':'육','七':'칠','八':'팔','九':'구','十':'십'}
UNIT = {'品':'품','級':'급','州':'주'}
SPECIAL_RANK = {'都尉':'도위','校尉':'교위','丞相':'승상','覇者':'패자','覇王':'패왕'}
o = 0x13f528
while o <= 0x13f638:
    end = aJ.find(b'\x00', o)
    jp = aJ[o:end].decode('cp932')
    base = jp.rstrip('\n')
    if base in SPECIAL_RANK:
        kr = SPECIAL_RANK[base]
    else:
        kr = NUM[base[0]] + UNIT[base[1]]
    add(o, jp, kr + '\n')
    o = end + 1
    while o < 0x13f640 and aJ[o] == 0: o += 1
add(0x13f730, '覇　王\n', '패　왕\n')

# ── 계급명 (무개행 세트 0x1463ac~) + スカ ──
o = 0x1463ac
while o <= 0x1464e8:
    end = aJ.find(b'\x00', o)
    jp = aJ[o:end].decode('cp932')
    base = jp.strip()
    if not base:
        o = end + 1
        continue
    if base == 'スカ':
        kr = '꽝'
    elif base in SPECIAL_RANK:
        kr = SPECIAL_RANK[base]
    elif len(base) == 2 and base[0] in NUM and base[1] in UNIT:
        kr = NUM[base[0]] + UNIT[base[1]]
    else:
        o = end + 1
        while o < 0x1464f0 and aJ[o] == 0: o += 1
        continue
    if jp.endswith(' '): kr += ' '
    add(o, jp, kr)
    o = end + 1
    while o < 0x1464f0 and aJ[o] == 0: o += 1
add(0x14012c, 'スカ', '꽝')

# ── 카드 앞뒤면 라벨 ──
add(0x140750, '#%s伝・右', '#%s전・우')
add(0x14075c, '#%s伝・左', '#%s전・좌')

# ── 세력/병종/도감 라벨 (0x146f50 존) ──
for off_, jp_, kr_ in ((0x146f50,'魏','위'),(0x146f54,'呉','오'),(0x146f58,'蜀','촉'),
                       (0x146f5c,'西涼','서량'),(0x146f64,'袁紹','원소'),(0x146f6c,'南蛮','남만'),
                       (0x146f84,'歩兵','보병'),(0x146f8c,'騎兵','기병'),(0x146f94,'槍兵','창병'),
                       (0x146f9c,'弓兵','궁병'),(0x146fac,'象兵','상병'),
                       (0x1470c8,'称号','칭호'),(0x1470d0,'兵種','병종'),(0x1470d8,'戦器','전기'),
                       (0x1470e0,'兵法','병법'),(0x1470e8,'特技','특기'),(0x1470f0,'計略','계략')):
    add(off_, jp_, kr_)

# ── Χ+무장명 블록 (0x1438xx~0x144c34) + 0x142090 ──
FALLBACK = {'蔡瑁':'채모','周姫':'주희','于吉':'우길','田豊':'전풍','顔良':'안량','孟獲':'맹획'}
xoffs = [0x142090]
o = 0x14389c
while o <= 0x144c34:
    if aJ[o:o+2] == 'Χ'.encode('cp932'):
        xoffs.append(o)
    o += 4
for o in xoffs:
    end = aJ.find(b'\x00', o)
    jp = aJ[o:end].decode('cp932', errors='replace')
    nm = jp[1:]
    kr = namedict.get(nm) or FALLBACK.get(nm)
    if not kr:
        print(f'  건너뜀(사전없음): {o:#x} {jp!r}')
        continue
    add(o, jp, 'Χ' + kr)

# ── 검증 + 병합 ──
outp = os.path.join(WORK, 'arm9_new_out.json')
cur = json.load(open(outp, encoding='utf-8'))
have = {it['off'] for it in cur}
ok = bad = dup = 0
for off_, jp_, kr_ in ENT:
    end = aJ.find(b'\x00', off_)
    raw = aJ[off_:end]
    try:
        real = raw.decode('cp932')
    except Exception:
        real = None
    if real != jp_:
        print(f'불일치 {off_:#x}: 예상 {jp_!r} 실제 {real!r}'); bad += 1; continue
    enc = korean.encode(kr_)
    if len(enc) > len(raw):
        print(f'길이초과 {off_:#x}: {jp_!r}({len(raw)}B) → {kr_!r}({len(enc)}B)'); bad += 1; continue
    if off_ in have:
        dup += 1; continue
    cur.append({'off': off_, 'ko': kr_})
    have.add(off_)
    ok += 1
print(f'추가 {ok}, 중복 {dup}, 오류 {bad} (총 {len(cur)})')
if bad == 0:
    json.dump(cur, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('저장:', outp)
else:
    print('오류 있어 저장 안 함')
