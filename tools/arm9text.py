# -*- coding: utf-8 -*-
# arm9 인플레이스 텍스트: 엄격 추출 + 길이제약 치환
import re

def is_text_char(c):
    # cp932로 인코딩 가능한 인쇄가능 문자면 텍스트로 간주(그리스ε·로마숫자Ⅰ·원문자① 등
    # 기종의존문자 포함). 노이즈는 상위 가나/마커/한자 조건이 억제.
    if not c.isprintable():
        return False
    try:
        c.encode('cp932')
        return True
    except UnicodeEncodeError:
        return False

def extract(a9, lo=0, hi=None):
    """NUL 종단, 가나 포함, 전부 텍스트 문자인 SJIS 문자열. [{off,nbytes,jp}]"""
    hi = hi if hi is not None else len(a9)
    pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|[\xa1-\xdf]){4,}')
    out = []
    for m in pat.finditer(a9[lo:hi]):
        off = lo + m.start(); end = lo + m.end()
        if end >= len(a9) or a9[end] != 0:      # NUL 종단만
            continue
        raw = m.group()
        try:
            s = raw.decode('cp932')
        except UnicodeDecodeError:
            continue
        if not any('぀' <= c <= 'ヿ' for c in s):      # 가나 1+ 필수
            continue
        if not all(is_text_char(c) for c in s):
            continue
        if sum(1 for c in s if '一' <= c <= '鿿' or '぀' <= c <= 'ヿ') < 2:
            continue
        out.append({'off': off, 'nbytes': len(raw), 'jp': s})
    return out

def extract_ml(a9, lo=0, hi=None):
    """NUL 구분 문자열(내부 개행 0x0a 허용) → 다줄 텍스트 통짜 포착. [{off,nbytes,jp}]"""
    hi = hi if hi is not None else len(a9)
    out = []
    p = lo
    while p < hi:
        q = a9.find(b'\x00', p, hi)
        if q < 0:
            break
        raw = a9[p:q]
        p = q + 1
        if len(raw) < 4:
            continue
        # 텍스트 문자(개행 포함)로만 구성, 가나 포함, 한자/가나 2+
        try:
            s = raw.decode('cp932')
        except UnicodeDecodeError:
            continue
        if not all(is_text_char(c) or c == '\n' for c in s):
            continue
        has_kana = any('぀' <= c <= 'ヿ' for c in s)
        has_marker = any(c in '：％「」『』＜＞・0123456789%、。！？…（）〜・＆' for c in s)
        hanzi = sum(1 for c in s if '一' <= c <= '鿿')
        # 가나 / (마커+한자2) / 순수한자3+ 허용 (순수 한자 UI 라벨 포착; 노이즈는 후검토)
        if not (has_kana or (has_marker and hanzi >= 2) or hanzi >= 3):
            continue
        if hanzi + sum(1 for c in s if '぀' <= c <= 'ヿ') < 2:
            continue
        out.append({'off': p - 1 - len(raw), 'nbytes': len(raw), 'jp': s})
    return out

def apply(a9, patches, encode_fn, allow_nl=False):
    """patches: [{off,nbytes,ko}]. 길이제약 내 인플레이스 치환 + NUL 패딩.
    allow_nl=True면 번역문 내 개행(\\n) 허용(원문이 개행 포함 다줄 문자열일 때).
    반환 (new_a9, errors)"""
    buf = bytearray(a9)
    errors = []
    for p in patches:
        enc = encode_fn(p['ko'])
        if b'\x00' in enc:
            errors.append((p['off'], 'NUL 포함', p['ko'])); continue
        if not allow_nl and (b'\r' in enc or b'\n' in enc):
            errors.append((p['off'], '개행 포함', p['ko'])); continue
        if len(enc) > p['nbytes']:
            errors.append((p['off'], f"길이초과 {len(enc)}>{p['nbytes']}", p['ko'])); continue
        buf[p['off']:p['off'] + len(enc)] = enc
        # 남는 공간 NUL 패딩 (원문 잔여 바이트 지우기)
        for i in range(p['off'] + len(enc), p['off'] + p['nbytes']):
            buf[i] = 0
    return bytes(buf), errors

if __name__ == "__main__":
    import os, sys, json
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import ndspy.rom
    BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
    a9 = bytes(rom.arm9)
    items = extract(a9)
    print(f"arm9 엄격 추출: {len(items)}개")
    # 중복 문자열 확인
    from collections import Counter
    dup = Counter(it['jp'] for it in items)
    print(f"고유 문자열: {len(dup)}, 중복 상위: {dup.most_common(3)}")
    json.dump(items, open(os.path.join(BASE, "work", "arm9_src.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for it in items[:30]:
        print(f"  0x{it['off']:x} ({it['nbytes']}B): {it['jp'][:44]}")
