# -*- coding: utf-8 -*-
r"""그림 안 «특정 색 글자» 덩어리 상자 찾기(2026-11-01) — 노선 선택 등 같은 글자가 여러 벌인 그림 조사용
  boxes(C, pal, pred, gap=4) → [(x0, y0, x1, y1)] (pred(r,g,b) 참인 화소를 가로 gap 안에서 이어 붙인 덩어리)"""
import numpy as np


def mask(C, pal, pred):
    v = pal[C]; return pred(v & 31, v >> 5 & 31, v >> 10 & 31)


def boxes(C, pal, pred, gap=4, minpx=6):
    m = mask(C, pal, pred) & (C != 0)
    k = np.zeros_like(m)
    for dx in range(-gap, gap + 1):
        k |= np.roll(m, dx, 1)
    k |= np.roll(k, 1, 0) | np.roll(k, -1, 0)
    seen = np.zeros_like(k); out = []
    for sy, sx in zip(*np.nonzero(k)):
        if seen[sy, sx]: continue
        st = [(sy, sx)]; seen[sy, sx] = True; ys = [sy]; xs = [sx]
        while st:
            y, x = st.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < k.shape[0] and 0 <= xx < k.shape[1] and k[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; st.append((yy, xx)); ys.append(yy); xs.append(xx)
        y0, y1, x0, x1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
        if m[y0:y1, x0:x1].sum() >= minpx: out.append((x0, y0, x1, y1))
    return sorted(out, key=lambda b: (b[1], b[0]))
