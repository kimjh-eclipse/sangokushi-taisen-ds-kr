# -*- coding: utf-8 -*-
# SCM 그래픽(MC 컨테이너) 파서: 헤더(폭/높이/색수) + 섹션(팔레트/타일, raw|LZ10|허프만)
import struct

def lz10_dec_track(src, pos, decsize):
    """BIOS LZ10 raw 스트림(헤더 없음) 해제 + 소비 끝위치 반환"""
    out = bytearray()
    n = len(src)
    while len(out) < decsize:
        if pos >= n: raise ValueError('EOF')
        flags = src[pos]; pos += 1
        for bit in range(8):
            if len(out) >= decsize: break
            if flags & (0x80 >> bit):
                if pos + 2 > n: raise ValueError('EOF ref')
                b1, b2 = src[pos], src[pos+1]; pos += 2
                ln = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out): raise ValueError('bad disp')
                for _ in range(ln):
                    out.append(out[-disp])
            else:
                if pos >= n: raise ValueError('EOF lit')
                out.append(src[pos]); pos += 1
    return bytes(out), pos

def parse_header(d):
    assert d[:2] == b'MC'
    u16 = struct.unpack_from('<8H', d, 0)
    psz, = struct.unpack_from('<I', d, 0x10)
    tail = struct.unpack_from('<2I', d, 0x18)
    return {'ver': u16[1], 'hdr': u16[2], 'w': u16[3], 'h': u16[4],
            'colors': u16[6], 'flag7': u16[7], 'payload': psz, 'tail': tail}

def read_section(d, pos, decsize):
    """섹션 하나: raw(decsize 그대로) 또는 BIOS 스트림. (data, newpos, kind)"""
    b0 = d[pos] if pos < len(d) else None
    # LZ10 헤더포함(0x10 + size24)
    if b0 == 0x10:
        s, = struct.unpack_from('<I', d, pos)
        size = s >> 8
        out, np = lz10_dec_track(d, pos + 4, size)
        return out, np, 'lz10'
    # BIOS 허프만(0x28/0x24) → 내부에 LZ10 스트림이 든 체인
    if b0 in (0x24, 0x28):
        import mc, ndspy.lz10
        mid = mc.huff_decompress(d, pos)
        if isinstance(mid, tuple): mid = mid[0]
        if mid[:1] == b'\x10':
            out = ndspy.lz10.decompress(bytes(mid))
            return bytes(out), len(d), 'huff+lz10'
        return bytes(mid), len(d), 'huff'
    raise ValueError(f'unknown section at 0x{pos:x} b0={b0:#x}')

def decode(d):
    """MC 그래픽 → dict(w,h,colors,palette(BGR555 bytes), gfx(bytes), sections meta)"""
    h = parse_header(d)
    pos = 0x20
    palbytes = h['colors'] * 2
    sections = []
    # 팔레트: raw 우선 시도(뒤에 유효한 LZ10이 이어지는지 확인), 실패 시 LZ10
    pal = None
    if palbytes:
        # LZ10 팔레트 우선 판별: 0x10 헤더 + 해제크기 == colors*2
        if d[pos] == 0x10:
            s, = struct.unpack_from('<I', d, pos)
            if (s >> 8) == palbytes:
                out, np, _ = read_section(d, pos, None)
                pal = out; pos = np
                sections.append(('pal', 'lz10', len(out)))
        if pal is None and pos + palbytes <= len(d):
            nxt = pos + palbytes
            if nxt >= len(d) or d[nxt] in (0x10, 0x24, 0x28):
                pal = bytes(d[pos:pos+palbytes]); pos = nxt
                sections.append(('pal', 'raw', palbytes))
        if pal is None:
            out, np, k = read_section(d, pos, None)
            pal = out; pos = np
            sections.append(('pal', k, len(out)))
        # 섹션 4바이트 정렬 (0 패딩)
        if pos % 4:
            pad = 4 - pos % 4
            if all(b == 0 for b in d[pos:pos+pad]):
                pos += pad
    # 현재 위치가 섹션이 아니고 u16[3](다수 변형에서 gfx 파일오프셋)이 유효 섹션이면 점프
    gofs = h['w']
    if (pos < len(d) and d[pos] not in (0x10, 0x24, 0x28)
            and pos < gofs <= len(d) - 4 and d[gofs] in (0x10, 0x24, 0x28)):
        pos = gofs
    # 그래픽 섹션들: 남은 스트림 전부
    gfx = bytearray()
    while pos < len(d) - 4:
        try:
            out, np, k = read_section(d, pos, None)
        except ValueError:
            break
        gfx += out
        sections.append(('gfx', k, len(out)))
        pos = np
        if pos % 4:  # 4바이트 정렬
            if all(b == 0 for b in d[pos:pos + (4 - pos % 4)]):
                pos += 4 - pos % 4
    return {'hdr': h, 'pal': pal, 'gfx': bytes(gfx), 'sections': sections, 'endpos': pos}

def pal_to_rgb(pal):
    cols = []
    for i in range(0, len(pal), 2):
        v = pal[i] | (pal[i+1] << 8)
        r = (v & 31) << 3; g = ((v >> 5) & 31) << 3; b = ((v >> 10) & 31) << 3
        cols.append((r, g, b))
    return cols

def render_4bpp_tiles(gfx, pal, tiles_w, scale=2, out_path=None):
    """4bpp 8x8 타일 나열 렌더 (tiles_w = 가로 타일수)"""
    from PIL import Image
    cols = pal_to_rgb(pal)
    ntiles = len(gfx) // 32
    tiles_h = (ntiles + tiles_w - 1) // tiles_w
    img = Image.new('RGB', (tiles_w * 8, tiles_h * 8), (255, 0, 255))
    px = img.load()
    for t in range(ntiles):
        tx, ty = (t % tiles_w) * 8, (t // tiles_w) * 8
        base = t * 32
        for y in range(8):
            for x in range(8):
                b = gfx[base + y * 4 + x // 2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                # 서브팔레트 0 가정
                if v < len(cols):
                    px[tx + x, ty + y] = cols[v]
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    if out_path: img.save(out_path)
    return img

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
    for nm in ('EX_NO.SCM', 'DCHOOSE.SCM', 'BTNALL.SCM'):
        off, sz = files[nm]
        d = sang[off:off+sz]
        try:
            r = decode(d)
        except Exception as e:
            print(f'{nm}: 실패 {e}'); continue
        h = r['hdr']
        print(f"{nm}: {h['w']}x{h['h']} colors={h['colors']} payload={h['payload']} "
              f"gfx={len(r['gfx'])}B sections={r['sections']} end=0x{r['endpos']:x}/{sz}")
        tw = max(1, h['w'] // 8)
        render_4bpp_tiles(r['gfx'], r['pal'], tw, 3, os.path.join(WORK, f'img_{nm}.png'))
        print(f'  -> img_{nm}.png')
