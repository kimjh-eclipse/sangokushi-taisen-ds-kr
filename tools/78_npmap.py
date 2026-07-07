# -*- coding: utf-8 -*-
# NP_XXXX ↔ CARDS2 카드ID 정렬 매핑 검증
import sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
rom = ndspy.rom.NintendoDSRom.fromFile(BASE + r'\San Goku Shi Taisen (J).nds')
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(BASE + r'\work\sangoku_toc.json', encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['CARDS2.DAT']
d = sang[off:off+sz]
nl = b'\r\n' if b'\r\n' in d else b'\n'
rows = [ln.split(b',') for ln in d.split(nl)]
recs = []
for ri, r in enumerate(rows):
    if len(r) > 4 and r[0].isdigit():
        recs.append((int(r[0]), ri, r[4].decode('cp932', errors='replace')))
recs.sort()
print('카드수', len(recs))
print('정렬 1~14:')
for k, (cid, ri, nm) in enumerate(recs[:14], 1):
    print(f'  {k}: id={cid} row={ri} {nm}')
fam = Counter(c // 1000 for c, _, _ in recs)
print('세력별:', dict(sorted(fam.items())))
print('마지막 3:', recs[-3:])
