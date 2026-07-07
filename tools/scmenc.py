# -*- coding: utf-8 -*-
# SCM 그래픽 재인코더: 편집된 gfx(CNCP payload) → MC 파일 재조립
# 원본 MC 헤더 유지, 팔레트 그대로, gfx만 LZ10 재압축.
import struct
import ndspy.lz10
import scmimg

def rebuild(orig_scm, new_gfx):
    """orig_scm: 원본 MC 바이트. new_gfx: 편집된 CNCP payload(해제 상태).
    반환: 새 MC 바이트 (헤더+팔레트 원본 유지 + new_gfx LZ10 재압축)."""
    h = scmimg.parse_header(orig_scm)
    r = scmimg.decode(orig_scm)
    # 원본에서 팔레트 섹션이 어디서 끝나는지(=gfx 시작) 재현
    palbytes = h['colors'] * 2
    pos = 0x20
    out = bytearray(orig_scm[:0x20])   # MC 헤더 그대로
    # 팔레트 섹션 재출력 (원본 그대로 복사)
    if palbytes:
        if orig_scm[pos] == 0x10:
            s, = struct.unpack_from('<I', orig_scm, pos)
            if (s >> 8) == palbytes:
                _, np = scmimg.lz10_dec_track(orig_scm, pos + 4, palbytes)
                out += orig_scm[pos:np]; pos = np
            else:
                out += orig_scm[pos:pos+palbytes]; pos += palbytes
        else:
            out += orig_scm[pos:pos+palbytes]; pos += palbytes
        # 정렬 패딩 복사
        if pos % 4:
            pad = 4 - pos % 4
            out += orig_scm[pos:pos+pad]; pos += pad
    # gfx: LZ10 재압축 (BIOS 헤더 포함)
    comp = ndspy.lz10.compress(new_gfx)
    out += comp
    # 4바이트 정렬
    if len(out) % 4:
        out += b'\x00' * (4 - len(out) % 4)
    # MC 헤더 0x10 = gfx 해제크기 갱신
    struct.pack_into('<I', out, 0x10, len(new_gfx))
    return bytes(out)

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
    # 무수정 왕복: decode gfx → rebuild → 다시 decode 하여 gfx 동일?
    for nm in ('BTNALL.SCM', 'DCHOOSE.SCM', 'EX_NO.SCM'):
        off, sz = files[nm]
        d = sang[off:off+sz]
        gfx = scmimg.decode(d)['gfx']
        rebuilt = rebuild(d, gfx)
        gfx2 = scmimg.decode(rebuilt)['gfx']
        ok = gfx2 == gfx
        print(f'{nm}: 왕복 gfx일치={ok}  원본={sz}B 재빌드={len(rebuilt)}B (차이 {len(rebuilt)-sz:+d})')
