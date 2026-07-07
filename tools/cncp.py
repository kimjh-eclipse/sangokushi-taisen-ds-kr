# -*- coding: utf-8 -*-
# CNCP(스프라이트 셀 뱅크) 파서/렌더러
# 구조: 'CNCP' ver u32 | cellTblOfs u32, cellCnt u32 | animTblOfs u32, animCnt u32 | endOfs u32, 0
#   0x20~: 4bpp 타일 gfx
#   cellTbl: 16B×N = [oamListPtr u32, oamCnt u32, gfxBase u32(=0x20), ???ofs u32]
#   oam item: 12B = attr0 u16, attr1 u16, attr2 u16, pad? u16, seq u16, pad u16
import struct

OBJ_SIZES = {  # (shape, size) -> (w,h)
    (0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),
    (1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),
    (2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64),
}

def parse(g):
    assert g[:4] == b'CNCP'
    cellOfs, cellCnt = struct.unpack_from('<II', g, 8)
    animOfs, animCnt = struct.unpack_from('<II', g, 0x10)
    endOfs, = struct.unpack_from('<I', g, 0x18)
    cells = []
    for i in range(cellCnt):
        p = cellOfs + i * 16
        oamPtr, oamCnt, gfxBase, xtra = struct.unpack_from('<IIII', g, p)
        oams = []
        for j in range(oamCnt):
            q = oamPtr + j * 12
            a0, a1, a2, pad, seq, pad2 = struct.unpack_from('<6H', g, q)
            oams.append((a0, a1, a2))
        cells.append({'oams': oams, 'gfxBase': gfxBase})
    return {'cells': cells, 'gfxStart': 0x20, 'cellOfs': cellOfs, 'animOfs': animOfs, 'end': endOfs}

def sgn(v, bits):
    return v - (1 << bits) if v >= (1 << (bits - 1)) else v

def render_cell(g, cell, pal_rgb, bpp=4):
    """OAM들을 조립해 (PIL Image, ox, oy) 반환. pal_rgb=[(r,g,b)]*colors"""
    from PIL import Image
    boxes = []
    for a0, a1, a2 in cell['oams']:
        shape = (a0 >> 14) & 3
        size = (a1 >> 14) & 3
        w, h = OBJ_SIZES[(shape, size)]
        x = sgn(a1 & 0x1FF, 9); y = sgn(a0 & 0xFF, 8)
        boxes.append((x, y, w, h))
    if not boxes:
        return None, 0, 0
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
    img = Image.new('RGBA', (x1 - x0, y1 - y0), (255, 0, 255, 0))
    px = img.load()
    gfxStart = cell['gfxBase']
    for a0, a1, a2 in cell['oams']:
        shape = (a0 >> 14) & 3; size = (a1 >> 14) & 3
        w, h = OBJ_SIZES[(shape, size)]
        x = sgn(a1 & 0x1FF, 9) - x0; y = sgn(a0 & 0xFF, 8) - y0
        hf = (a1 >> 12) & 1; vf = (a1 >> 13) & 1
        tile = a2 & 0x3FF; palno = (a2 >> 12) & 0xF
        tw, th = w // 8, h // 8
        for ty in range(th):
            for tx in range(tw):
                tofs = gfxStart + (tile + ty * tw + tx) * 32   # 1D 매핑
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs + yy * 4 + xx // 2]
                        v = (b >> 4) if (xx & 1) else (b & 0xF)
                        if v == 0:  # 투명
                            continue
                        ci = palno * 16 + v
                        if ci >= len(pal_rgb): continue
                        sx = tx * 8 + xx; sy = ty * 8 + yy
                        if hf: sx = w - 1 - sx
                        if vf: sy = h - 1 - sy
                        X, Y = x + sx, y + sy
                        if 0 <= X < img.width and 0 <= Y < img.height:
                            px[X, Y] = (*pal_rgb[ci], 255)
    return img, x0, y0

def render_all(g, pal_rgb, out_path, scale=3, cols=8):
    from PIL import Image, ImageDraw
    info = parse(g)
    imgs = []
    for i, c in enumerate(info['cells']):
        im, _, _ = render_cell(g, c, pal_rgb)
        imgs.append(im)
    cw = max((im.width for im in imgs if im), default=8) + 4
    ch = max((im.height for im in imgs if im), default=8) + 12
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw, rows * ch), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        X, Y = (i % cols) * cw, (i // cols) * ch
        if im: sheet.paste(im, (X + 2, Y + 10), im)
        d.text((X + 2, Y), str(i), fill=(255, 255, 0))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.save(out_path)
    return len(imgs)

if __name__ == '__main__':
    import os, sys, json
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
    import ndspy.rom, scmimg
    BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
    WORK = os.path.join(BASE, 'work')
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
    sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
    toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
    files = {n: (o, s) for n, o, s in toc}
    for nm in sys.argv[1:] or ('DCHOOSE.SCM', 'EX_NO.SCM', 'BTNALL.SCM'):
        off, sz = files[nm]
        r = scmimg.decode(sang[off:off+sz])
        pal = scmimg.pal_to_rgb(r['pal'])
        n = render_all(r['gfx'], pal, os.path.join(WORK, f'cells_{nm}.png'))
        print(f'{nm}: cells={n} -> cells_{nm}.png')
