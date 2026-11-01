# -*- coding: utf-8 -*-
r"""전차로 GO! EX VDP2 그림 묶음(2026-10-31 조사) — HUD·안내 판넬 등
  머리 u32 BE: [0]=맵 쪽 수(보통 1, 2쪽이면 맵 자리에 이어 붙음) [1]=보통 [0]과 같음(GO_SEL @273C 는 2,1) [2]=맵 한 쪽 바이트 [3]=셀 VRAM 기준?(보통 0, 1워드 맵은 0x8000)
              [4]=0x10 [5]=PN 형식(0 = 2워드, 1 = 1워드) [6]=팔레트 바이트(0x200) [7]=셀 바이트
              [8]=팔레트 오프셋(0x40) [9]=셀 오프셋(0x240) [10]=맵 오프셋(= 0x240 + 셀 바이트)
  셀 = 8bpp 8×8(64 B), 팔레트 = RGB555 BE 256색, 맵 = 2워드: 64×64 쪽(w1 & 0x7FFF = 셀 번호 ×0x20 단위)
                                              1워드: 16×16 글자 32×32 쪽(v & 0x3FF ×0x80, 2×2 셀, 비트10/11 = 좌우/상하 뒤집기)
  python tools/v2img.py     → work/img/<묶음>_<항목>.png (맵 그대로) + _sheet.png(셀 나열)
"""
import os, struct, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import arc


def rgb(e):
    e = np.asarray(e)
    return np.stack([(e & 31) << 3, ((e >> 5) & 31) << 3, ((e >> 10) & 31) << 3], -1).astype(np.uint8)


def parse(d):
    if len(d) < 0x240: return None
    w = struct.unpack(">11I", d[:44])
    if not (1 <= w[0] <= 8 and 1 <= w[1] <= w[0]) or w[8] != 0x40 or w[9] != 0x240: return None
    return dict(pages=w[0], mapsz=w[2] * w[0], base=w[3], one=w[5], palsz=w[6], cellsz=w[7], pal=w[8], cell=w[9], map=w[10])


def render(d, H=None):
    H = H or parse(d)
    pal = np.frombuffer(d[H['pal']:H['pal'] + H['palsz']], '>u2').astype(int)
    cells = d[H['cell']:H['cell'] + H['cellsz']]; mp = d[H['map']:H['map'] + H['mapsz']]
    if H['one']:   # 1워드 = 16×16 글자(2×2 셀, 좌상·우상·좌하·우하), 32×32 쪽, 번호(v & 0x3FF) ×0x80
        n = len(mp) // 2; W = 32; R = (n + W - 1) // W
        out = np.zeros((R * 16, W * 16, 3), np.uint8)
        for k in range(n):
            cy, cx = divmod(k, W)
            v = struct.unpack_from('>H', mp, k * 2)[0]; a = (v & 0x3FF) * 0x80; hf, vf = v >> 10 & 1, v >> 11 & 1
            if a + 256 > len(cells): continue
            q = [np.frombuffer(cells[a + 64 * j:a + 64 * j + 64], np.uint8).reshape(8, 8) for j in range(4)]
            px = np.block([[q[0], q[1]], [q[2], q[3]]])
            if hf: px = px[:, ::-1]
            if vf: px = px[::-1]
            c = rgb(pal[px]); c[px == 0] = 0
            out[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16] = c
        return out
    n = len(mp) // 4; W = 64; R = (n + W - 1) // W
    out = np.zeros((R * 8, W * 8, 3), np.uint8)
    for k in range(n):
        cy, cx = divmod(k, W)
        w0, w1 = struct.unpack_from('>HH', mp, k * 4); ch = w1 & 0x7FFF; hf, vf = w0 >> 14 & 1, w0 >> 15 & 1
        a = ch * 0x20
        if a + 64 > len(cells): continue
        px = np.frombuffer(cells[a:a + 64], np.uint8).reshape(8, 8)
        if hf: px = px[:, ::-1]
        if vf: px = px[::-1]
        c = rgb(pal[px]); c[px == 0] = 0
        out[cy * 8:cy * 8 + 8, cx * 8:cx * 8 + 8] = c
    return out


def sheet(d, H=None, W=32):
    H = H or parse(d)
    pal = np.frombuffer(d[H['pal']:H['pal'] + H['palsz']], '>u2').astype(int)
    cells = d[H['cell']:H['cell'] + H['cellsz']]; n = len(cells) // 64; R = (n + W - 1) // W
    out = np.zeros((R * 8, W * 8, 3), np.uint8)
    for k in range(n):
        px = np.frombuffer(cells[k * 64:k * 64 + 64], np.uint8).reshape(8, 8); c = rgb(pal[px]); c[px == 0] = 0
        out[k // W * 8:k // W * 8 + 8, k % W * 8:k % W * 8 + 8] = c
    return out


def embedded(d):
    """BIN 오버레이 안에 박힌 CHR 압축 그림 → [(오프셋, 풀린 바이트)] (GO_SEL·GO_NAME·GO_RANK 등, 2026-10-31)"""
    res = []; i = 0
    while i < len(d) - 10:
        if d[i] < 6 and d[i + 1] == 0:
            u, c = struct.unpack_from('<II', d, i + 2)
            if 64 < c <= len(d) - i - 10 and c < u <= c * 16 and u < 0x100000:
                try:
                    o = arc.chr_dec(d[i:i + 10 + c])
                    if parse(o): res.append((i, o)); i += 10 + c; continue
                except Exception:
                    pass
        i += 1
    return res


def items():
    """→ [(이름, 바이트)] 디스크 전체에서(묶음 두 단계까지) 이 형식 항목"""
    res = []

    def walk(name, d, depth):
        if parse(d): res.append((name, d)); return
        if d[:8] == b'DARC0090' and depth < 3:
            for k, o, b in arc.darc(d): walk('%s_%03d' % (name, k), b, depth + 1)
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'disc0', '*'))):
        d = open(p, 'rb').read()
        if d[:4] == b'SZ3\0': d = arc.sz3(d)
        elif arc.is_chr(d): d = arc.chr_dec(d)
        walk(os.path.basename(p).replace('.', '_'), d, 0)
        if p.upper().endswith('.BIN') and not parse(d) and not arc.is_chr(open(p, 'rb').read()):
            for o, e in embedded(d): res.append(('%s_at%05X' % (os.path.basename(p).replace('.', '_'), o), e))
    return res


if __name__ == '__main__':
    out = os.path.join(ROOT, 'work', 'img'); os.makedirs(out, exist_ok=True)
    for nm, d in items():
        H = parse(d); im = render(d, H)
        ys, xs = np.nonzero(im.sum(2))
        if len(ys): im = im[:ys.max() + 1, :xs.max() + 1]
        Image.fromarray(im).save(os.path.join(out, nm + '.png'))
        Image.fromarray(sheet(d, H)).save(os.path.join(out, nm + '_sheet.png'))
        print(nm, 'one' if H['one'] else 'two', hex(H['base']), H['cellsz'] // 64, '셀', im.shape[1], 'x', im.shape[0])
