# -*- coding: utf-8 -*-
# scenario.sar 리빌더: 엔트리별 문자열 교체 + 포인터 재매핑
import struct

def parse(sar):
    n = struct.unpack_from("<I", sar, 0)[0] // 8
    return [struct.unpack_from("<II", sar, i * 8) for i in range(n)]

def get_strings(sar, off, sz):
    scriptSz, textSz = struct.unpack_from("<II", sar, off)
    pool = sar[off + scriptSz: off + scriptSz + textSz]
    strs = []
    p = 0
    while p < len(pool):
        q = pool.find(b"\0", p)
        if q < 0: q = len(pool)
        strs.append((p, pool[p:q]))
        p = q + 1
    return strs

def rebuild_entry(sar, off, sz, translations, encode_fn):
    """translations: {old_pool_offset: 한국어str}. 반환: 새 엔트리 bytes"""
    scriptSz, textSz = struct.unpack_from("<II", sar, off)
    script = bytearray(sar[off + 8: off + scriptSz])
    strs = get_strings(sar, off, sz)
    # 새 풀 구성
    remap = {}
    pool = bytearray()
    for p, raw in strs:
        remap[p] = len(pool)
        if p in translations:
            pool += encode_fn(translations[p])
        else:
            pool += raw
        pool += b"\0"
    # 스크립트 포인터 재매핑 (4바이트 정렬 u32, 상위바이트 0x81, low24가 문자열 시작)
    starts = set(remap.keys())
    hits = 0
    for i in range(0, len(script) - 3, 4):
        v, = struct.unpack_from("<I", script, i)
        if (v >> 24) == 0x81 and (v & 0xFFFFFF) in starts:
            struct.pack_into("<I", script, i, 0x81000000 | remap[v & 0xFFFFFF])
            hits += 1
    newTextSz = len(pool)
    out = struct.pack("<II", scriptSz, newTextSz) + bytes(script) + bytes(pool)
    return out, hits

def rebuild(sar, all_translations, encode_fn):
    """all_translations: {entry_idx: {pool_off: str}}"""
    entries = parse(sar)
    n = len(entries)
    blobs = []
    for i, (off, sz) in enumerate(entries):
        if i in all_translations and sz:
            blob, hits = rebuild_entry(sar, off, sz, all_translations[i], encode_fn)
        else:
            blob = bytes(sar[off:off + sz])
        blobs.append(blob)
    # 테이블 재구성 (16바이트 정렬)
    table = bytearray()
    pos = n * 8
    pos = (pos + 0xF) & ~0xF
    body = bytearray()
    for blob in blobs:
        start = pos + len(body)
        pad = (-start) % 16
        body += b"\0" * pad
        start += pad
        table += struct.pack("<II", start, len(blob))
        body += blob
    return bytes(table) + b"\0" * (pos - n * 8) + bytes(body)

if __name__ == "__main__":
    import os, sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
    import ndspy.rom
    BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
    sar_data = bytes(rom.files[rom.filenames.idOf("scenario.sar")])
    # 무변조 왕복: 빈 번역으로 rebuild → 파싱 가능성 확인
    out = rebuild(sar_data, {}, lambda s: s.encode("shift_jis"))
    ent_old = parse(sar_data)
    ent_new = parse(out)
    same = all(sar_data[o1:o1+s1] == out[o2:o2+s2] for (o1, s1), (o2, s2) in zip(ent_old, ent_new))
    print("entries:", len(ent_old), "content identical:", same, f"size {len(sar_data)} -> {len(out)}")
