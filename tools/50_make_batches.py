# -*- coding: utf-8 -*-
# 번역 대상을 엔트리별 소스 JSON으로 추출 (work/tl_src/eNNN.json)
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
SRC = os.path.join(WORK, "tl_src")
os.makedirs(SRC, exist_ok=True)
d = json.load(open(os.path.join(WORK, "sar_strings.json"), encoding="utf-8"))
jp = re.compile(r"[぀-ヿ一-鿿]")

manifest = []
for e in d:
    if not e:
        continue
    ei = e["entry"]
    items = []
    for p, s in e["strings"]:
        # 번역 대상: 일본어 포함. 순수 기호/숫자/공백/전각공백은 원문 유지(스킵)
        if jp.search(s):
            items.append({"off": p, "jp": s})
    if items:
        fn = os.path.join(SRC, f"e{ei:03d}.json")
        json.dump({"entry": ei, "items": items}, open(fn, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        manifest.append((ei, len(items)))

json.dump(manifest, open(os.path.join(WORK, "tl_manifest.json"), "w", encoding="utf-8"))
print(f"엔트리 파일 {len(manifest)}개 생성, 총 {sum(n for _,n in manifest)} 문자열")
# 배치 분할: 엔트리를 11묶음으로
batches = [[] for _ in range(11)]
for i, (ei, n) in enumerate(manifest):
    batches[i % 11].append(ei)
for bi, b in enumerate(batches):
    print(f"batch{bi}: entries {b}")
json.dump(batches, open(os.path.join(WORK, "tl_batches.json"), "w", encoding="utf-8"))
