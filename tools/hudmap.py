# -*- coding: utf-8 -*-
r"""스테이트 화면 NBG1 칸 → HUD 아틀라스(DR_B?X00 001) 좌표 표 (2026-10-31)
  python tools/hudmap.py <스테이트> <열0> <열1> <행0> <행1>"""
import os, sys, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import v2img, vdp2render as R
d = open(os.path.join(ROOT, 'work', 'x', 'DR_B4X00.SZ3', '001.bin'), 'rb').read(); H = v2img.parse(d)
mp = d[H['map']:H['map'] + H['mapsz']]
where = collections.defaultdict(list)
for k in range(64 * 64):
    w0, w1 = struct.unpack_from('>HH', mp, k * 4); where[(w1 & 0x7fff)].append((k % 64 * 8, k // 64 * 8))
st = sys.argv[1]; c0, c1, r0, r1 = map(int, sys.argv[2:6])
v, reg, cram = R.load(st); base = 0x78000
for cy in range(r0, r1):
    row = []
    for cx in range(c0, c1):
        w0, w1 = struct.unpack_from('>HH', v, base + (cy * 64 + cx) * 4); n = (w1 & 0x7fff) - 0x1000
        L = where.get(n, [])
        row.append('%3d,%3d' % L[0] if L else '   -   ')
    print('%2d ' % cy + '|'.join(row))
