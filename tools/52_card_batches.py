# -*- coding: utf-8 -*-
# 카드 DB 번역 소스를 파일·유형별로 추출 (이름류 / 설명문류 분리)
import os, sys, json
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
sys.stdout.reconfigure(encoding="utf-8")
import dat

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
CSRC = os.path.join(WORK, "cd_src")
os.makedirs(CSRC, exist_ok=True)

SPECS = {
    "CARDS2.DAT": {"name": [4, 5], "desc": [11]},
    "ITEM.DAT":   {"name": [1, 31], "desc": [26]},
    "TACTICS.DAT":{"name": [1], "desc": [29, 30]},
    "TRICKS.DAT": {"name": [1], "desc": []},
    "CARDS.DAT":  {"name": [1, 24], "desc": []},
}

manifest = []
for fn, groups in SPECS.items():
    for kind, cols in groups.items():
        if not cols:
            continue
        items = dat.extract(os.path.join(WORK, fn), cols)
        if not items:
            continue
        # 셀 키에 파일명 포함
        rec = {"file": fn, "kind": kind,
               "items": [{"row": it["row"], "col": it["col"], "jp": it["jp"]} for it in items]}
        out = os.path.join(CSRC, f"{fn}.{kind}.json")
        json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        manifest.append((fn, kind, len(items)))
        print(f"{fn} [{kind}]: {len(items)}셀 -> {os.path.basename(out)}")
json.dump(manifest, open(os.path.join(WORK, "cd_manifest.json"), "w", encoding="utf-8"))
print("총", sum(n for _,_,n in manifest))
