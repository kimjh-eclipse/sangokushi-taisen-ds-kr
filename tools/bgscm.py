# -*- coding: utf-8 -*-
# BG형 SCM(타일+NDS 맵) 디코더/렌더러/재인코더
#  MC헤더: u16[3]=gfx섹션 파일오프셋(0x20+팔레트), u16[4]=맵 파일오프셋, u16[5]=타일수, u16[6]=팔레트색수
#  팔레트 raw BGR555 @0x20 | gfx=LZ10(4bpp 타일들) | 맵=u16 엔트리(tile0-9|hf10|vf11|pal12-15), 32타일 폭
import struct
import ndspy.lz10
import scmimg

def decode_map(C):
    """압축 맵 스트림 해독 (2B 헤더 + 토큰들)
    0x00-0x3F: 리터럴 c+1 | 0x40: 확장 리터럴(다음바이트 N → N+1)
    0x80-0xBF: RLE (c&0x3F)+2 | 0xC0-0xFF: 증가런 (c&0x3F)+2"""
    hdr = bytes(C[:2])
    out = []
    ci = 2
    n = len(C)
    while ci < n - 1:
        c = C[ci]
        if c == 0x40:
            cnt = C[ci+1] + 1
            ci += 2
            for _ in range(cnt):
                if ci + 1 >= n: return hdr, out, ci
                out.append(C[ci] | (C[ci+1] << 8)); ci += 2
        elif c < 0x40:
            cnt = c + 1
            ci += 1
            for _ in range(cnt):
                if ci + 1 >= n: return hdr, out, ci
                out.append(C[ci] | (C[ci+1] << 8)); ci += 2
        elif c < 0xC0:
            v = C[ci+1] | (C[ci+2] << 8)
            out += [v] * ((c & 0x3F) + 2)
            ci += 3
        else:
            v = C[ci+1] | (C[ci+2] << 8)
            for k in range((c & 0x3F) + 2):
                out.append((v + k) & 0xFFFF)
            ci += 3
    return hdr, out, ci

def encode_map(hdr, entries):
    """encode: 탐욕적 (RLE/INC ≥3이면 런, 아니면 리터럴 배치)"""
    out = bytearray(hdr)
    i = 0
    n = len(entries)
    while i < n:
        # 런 길이 측정
        v = entries[i]
        r = 1
        while i + r < n and entries[i+r] == v and r < 65:
            r += 1
        inc = 1
        while i + inc < n and entries[i+inc] == (v + inc) & 0xFFFF and inc < 65:
            inc += 1
        if r >= 3:
            out.append(0x80 | (r - 2)); out += struct.pack('<H', v)
            i += r
            continue
        if inc >= 3:
            out.append(0xC0 | (inc - 2)); out += struct.pack('<H', v)
            i += inc
            continue
        # 리터럴 배치: 다음 런 시작 전까지
        j = i
        while j < n:
            vv = entries[j]
            rr = 1
            while j + rr < n and entries[j+rr] == vv and rr < 4:
                rr += 1
            ii = 1
            while j + ii < n and entries[j+ii] == (vv + ii) & 0xFFFF and ii < 4:
                ii += 1
            if rr >= 3 or ii >= 3:
                break
            j += 1
            if j - i >= 256: break
        cnt = j - i
        while cnt > 0:
            take = min(cnt, 256)
            if take <= 64:
                out.append(take - 1)
            else:
                out.append(0x40); out.append(take - 1)
            for k in range(take):
                out += struct.pack('<H', entries[i+k])
            i += take
            cnt -= take
    return bytes(out)

def parse(d):
    u16 = struct.unpack_from('<8H', d, 0)
    colors = u16[6]
    pal = d[0x20:0x20+colors*2]
    gofs, mofs, ntiles = u16[3], u16[4], u16[5]
    s, = struct.unpack_from('<I', d, gofs)
    assert (s & 0xFF) == 0x10, f'gfx가 LZ10이 아님 @{gofs:#x}'
    tiles, _ = scmimg.lz10_dec_track(d, gofs+4, s >> 8)
    m = d[mofs:]
    n = len(m) // 2
    entries = struct.unpack_from(f'<{n}H', m, 0)
    return {'pal': pal, 'tiles': tiles, 'map': list(entries), 'ntiles': ntiles,
            'gofs': gofs, 'mofs': mofs, 'u16': u16}

def render(info, tiles_w=32, scale=2, out_path=None):
    from PIL import Image
    cols = scmimg.pal_to_rgb(info['pal'])
    ent = info['map']
    tiles = info['tiles']
    H = (len(ent) + tiles_w - 1) // tiles_w
    img = Image.new('RGB', (tiles_w*8, H*8), (255, 0, 255))
    px = img.load()
    for i, e in enumerate(ent):
        tx, ty = (i % tiles_w)*8, (i // tiles_w)*8
        t = e & 0x3FF; hf = (e >> 10) & 1; vf = (e >> 11) & 1; p = (e >> 12) & 0xF
        base = t*32
        if base+32 > len(tiles): continue
        for y in range(8):
            for x in range(8):
                b = tiles[base+y*4+x//2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                ci = p*16+v
                sx = 7-x if hf else x; sy = 7-y if vf else y
                if ci < len(cols):
                    px[tx+sx, ty+sy] = cols[ci]
    if scale != 1:
        img = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
    if out_path: img.save(out_path)
    return img

def index_bitmap(info, tiles_w=32):
    """맵 적용된 전체 인덱스 비트맵(팔레트행 포함: 값=pal*16+v). 편집용."""
    ent = info['map']; tiles = info['tiles']
    H = (len(ent) + tiles_w - 1) // tiles_w
    bm = [[0]*(tiles_w*8) for _ in range(H*8)]
    pmap = [[0]*(tiles_w*8) for _ in range(H*8)]   # 픽셀별 팔레트행
    for i, e in enumerate(ent):
        tx, ty = (i % tiles_w)*8, (i // tiles_w)*8
        t = e & 0x3FF; hf = (e >> 10) & 1; vf = (e >> 11) & 1; p = (e >> 12) & 0xF
        base = t*32
        if base+32 > len(tiles): continue
        for y in range(8):
            for x in range(8):
                b = tiles[base+y*4+x//2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                sx = 7-x if hf else x; sy = 7-y if vf else y
                bm[ty+sy][tx+sx] = v
                pmap[ty+sy][tx+sx] = p
    return bm, pmap

def rebuild(d, info, bm, tiles_w=32):
    """편집된 인덱스 비트맵(bm) → 타일 재구성(플립 베이크+dedup) + 새 맵 → MC 재조립.
    범위 밖(타 파일 VRAM 참조) 엔트리는 그대로 보존한다."""
    ent = info['map']
    own = info['ntiles']
    H = (len(ent) + tiles_w - 1) // tiles_w
    tiledict = {}
    newtiles = bytearray()
    newmap = []
    # 범위 밖 엔트리가 참조할 수 있도록 자기 타일 인덱스 공간을 넘어서는 인덱스는 보존해야 함
    # → 새 타일 인덱스가 기존 범위 밖 참조와 충돌하지 않게, 범위 밖 엔트리는 원본 그대로 복사
    for i, e in enumerate(ent):
        t = e & 0x3FF
        if t >= own:
            newmap.append(e)          # 외부 참조 보존
            continue
        tx, ty = (i % tiles_w)*8, (i // tiles_w)*8
        hf = (e >> 10) & 1; vf = (e >> 11) & 1
        raw = bytearray(32)
        for y in range(8):
            for x in range(0, 8, 2):
                # 저장 타일 = 화면 픽셀의 역플립
                sx0 = 7-x if hf else x
                sx1 = 7-(x+1) if hf else x+1
                sy = 7-y if vf else y
                lo = bm[ty+sy][tx+sx0] & 0xF
                hi = bm[ty+sy][tx+sx1] & 0xF
                raw[y*4+x//2] = lo | (hi << 4)
        key = bytes(raw)
        if key not in tiledict:
            tiledict[key] = len(newtiles)//32
            newtiles += key
        newmap.append(tiledict[key] | (e & 0xFC00))
    ntiles = len(newtiles)//32
    assert ntiles <= own, f'타일수 증가 {ntiles} > {own} (외부참조 충돌 위험)'
    # 원본 타일수 유지(외부 참조 인덱스 불변 보장): 부족분은 0타일 패딩
    newtiles += b'\x00' * ((own - ntiles) * 32)
    ntiles = own
    comp = ndspy.lz10.compress(bytes(newtiles))
    gofs = info['gofs']
    out = bytearray(d[:gofs])            # 헤더+팔레트 그대로
    out += comp
    while len(out) % 16: out += b'\x00'  # 맵 오프셋 정렬(16B)
    mofs = len(out)
    for e in newmap:
        out += struct.pack('<H', e)
    struct.pack_into('<H', out, 8, mofs & 0xFFFF)    # u16[4]=맵 오프셋
    struct.pack_into('<H', out, 10, ntiles)          # u16[5]=타일수
    return bytes(out), ntiles


def rebuild_c(d, info, entries, bm):
    """압축맵 BG 재조립: 편집된 비트맵(bm) → 타일 재구성(dedup, 성장 허용) + encode_map.
    entries = 원본 해독 맵(팔레트/플립 속성 유지). 범위밖 참조가 없는 파일 전용."""
    tiledict = {}
    newtiles = bytearray()
    newmap = []
    for i, e in enumerate(entries):
        tx, ty = (i % 32)*8, (i // 32)*8
        hf = (e >> 10) & 1; vf = (e >> 11) & 1
        raw = bytearray(32)
        for y in range(8):
            for x in range(0, 8, 2):
                sx0 = 7-x if hf else x
                sx1 = 7-(x+1) if hf else x+1
                sy = 7-y if vf else y
                lo = bm[ty+sy][tx+sx0] & 0xF
                hi = bm[ty+sy][tx+sx1] & 0xF
                raw[y*4+x//2] = lo | (hi << 4)
        key = bytes(raw)
        if key not in tiledict:
            tiledict[key] = len(newtiles)//32
            newtiles += key
        newmap.append(tiledict[key] | (e & 0xFC00))
    ntiles = len(newtiles)//32
    assert ntiles <= 1024, f'타일 한계 초과 {ntiles}'
    comp = ndspy.lz10.compress(bytes(newtiles))
    hdr2 = bytes(d[info['mofs']:info['mofs']+2])
    mapc = encode_map(hdr2, newmap)
    out = bytearray(d[:info['gofs']])
    out += comp
    while len(out) % 16: out += bytes(1)
    mofs = len(out)
    out += mapc
    struct.pack_into('<H', out, 8, mofs & 0xFFFF)
    struct.pack_into('<H', out, 10, ntiles)
    return bytes(out), ntiles

if __name__ == '__main__':
    import os, sys, json
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    import ndspy.rom
    BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
    WORK = os.path.join(BASE, 'work')
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
    sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
    toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
    files = {n: (o, s) for n, o, s in toc}
    for nm in sys.argv[1:] or ['TIT_1L0.SCM', 'TIT_1L1.SCM', 'TIT_1L2.SCM', 'TIT_1L3.SCM', 'TIT_1L4.SCM', 'NA_BGR01.SCM', 'TIT_0L.SCM']:
        off, sz = files[nm]
        d = sang[off:off+sz]
        try:
            info = parse(d)
        except Exception as e:
            print(f'{nm}: 실패 {e}'); continue
        img = render(info, 32, 2, os.path.join(WORK, f'bg_{nm}.png'))
        # 왕복 검증
        bm, pmap = index_bitmap(info)
        r2, nt = rebuild(d, info, bm)
        info2 = parse(r2)
        img2 = render(info2, 32, 1)
        img1 = render(info, 32, 1)
        ok = list(img1.getdata()) == list(img2.getdata())
        print(f'{nm}: 타일{info["ntiles"]}→{nt} 맵{len(info["map"])} 왕복렌더일치={ok} -> bg_{nm}.png')
