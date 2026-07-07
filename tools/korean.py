# -*- coding: utf-8 -*-
# 한국어 텍스트 → 게임 인코딩 (한글은 매핑된 SJIS 한자 코드로)
import json, os

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
MAP = {ch: code for ch, code in json.load(open(os.path.join(WORK, "hangul_map.json"), encoding="utf-8")).items()}

# 특수문자 → SJIS 대응 (전각)
SPECIAL = {
    "…": "…", "·": "・", "「": "「", "」": "」", "『": "『", "』": "』",
    "~": "～", "―": "―", "—": "―", "‘": "‘", "’": "’", "“": "“", "”": "”",
    "×": "×", "○": "○", "●": "●", "◆": "◆", "★": "★", "☆": "☆",
    "→": "→", "←": "←", "↑": "↑", "↓": "↓", "℃": "℃", "%": "%",
}

def encode(text):
    out = bytearray()
    for ch in text:
        if ch in MAP:
            code = MAP[ch]
            out += bytes([code >> 8, code & 0xFF])
        elif ord(ch) < 0x80:
            out.append(ord(ch))
        else:
            s = SPECIAL.get(ch, ch)
            try:
                out += s.encode("cp932")   # 게임 SJIS=cp932(기종의존문자 포함)
            except UnicodeEncodeError:
                raise ValueError(f"인코딩 불가 문자: {ch!r} in {text!r}")
    return bytes(out)

def decode(data):
    """디버그용 역변환"""
    rev = {v: k for k, v in MAP.items()}
    out = []
    i = 0
    while i < len(data):
        b = data[i]
        if b < 0x80:
            out.append(chr(b)); i += 1
        else:
            code = (b << 8) | data[i+1]
            if code in rev:
                out.append(rev[code])
            else:
                out.append(bytes([b, data[i+1]]).decode("shift_jis", "replace"))
            i += 2
    return "".join(out)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    t = "장군님! 기다리고 있었습니다."
    e = encode(t)
    print(e.hex())
    print(decode(e))
    assert decode(e) == t
    print("OK")
