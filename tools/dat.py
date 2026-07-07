# -*- coding: utf-8 -*-
# DAT(CSV, cp932) 바이트 기반 필드 번역기.
# 라인/셀 분해를 bytes로 → 번역 셀만 cp932 인코드 교체 → 미번역 부분 100% 바이트 보존.
# 규칙: 번역문에 반각 ',' 금지(컬럼 구분자). 전각 '，'/'、' 사용.
import os

def load(path):
    raw = open(path, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    rows = [ln.split(b",") for ln in lines]
    return rows, nl

def save(path, rows, nl):
    raw = nl.join(b",".join(cells) for cells in rows)
    open(path, "wb").write(raw)

def extract(path, col_spec):
    """번역 대상 셀: [{row,col,jp}]. 헤더(#)·비일본어 제외."""
    rows, nl = load(path)
    out = []
    for ri, cells in enumerate(rows):
        if not cells or cells[0][:1] == b"#":
            continue
        for ci in col_spec:
            if ci < len(cells) and cells[ci].strip():
                try:
                    v = cells[ci].decode("cp932")
                except UnicodeDecodeError:
                    continue
                if any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in v):
                    out.append({"row": ri, "col": ci, "jp": v})
    return out

def apply_map(path, out_path, tmap, encode_fn=None):
    """tmap: {(row,col): ko}. encode_fn(ko)->bytes로 셀 교체.
    encode_fn 미지정 시 cp932(무번역/일본어용). 한글은 korean.encode 필요."""
    rows, nl = load(path)
    for (ri, ci), ko in tmap.items():
        if "," in ko:
            raise ValueError(f"반각 쉼표 금지: r{ri}c{ci} {ko!r}")
        enc = encode_fn(ko) if encode_fn else ko.encode("cp932")
        # 구분자/개행 바이트 혼입 방지
        if b"," in enc or b"\r" in enc or b"\n" in enc:
            raise ValueError(f"금지 바이트 혼입: r{ri}c{ci} {ko!r}")
        rows[ri][ci] = enc
    save(out_path, rows, nl)
    return len(tmap)

if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
    SPECS = {
        "CARDS2.DAT": [4, 5, 11],
        "ITEM.DAT":   [1, 26, 31],
        "TACTICS.DAT":[1, 29, 30],
        "TRICKS.DAT": [1],
        "CARDS.DAT":  [1, 24],
    }
    total = 0
    for fn, spec in SPECS.items():
        items = extract(os.path.join(WORK, fn), spec)
        rows, nl = load(os.path.join(WORK, fn))
        save(os.path.join(WORK, fn + ".rt"), rows, nl)
        same = open(os.path.join(WORK, fn + ".rt"), "rb").read() == open(os.path.join(WORK, fn), "rb").read()
        print(f"{fn}: 번역대상 {len(items)}셀, 바이트왕복동일={same}")
        total += len(items)
    print(f"총 번역대상 셀: {total}")
