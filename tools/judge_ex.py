# -*- coding: utf-8 -*-
r"""정차 판정 그림(DR_H?002.SZ3 항목 001, 4노선 같음) 한글화(2026-11-01) — 낱말 조각 모음, 조각마다 원래 칸 안에서
  노랑 속 + 짙은 빨강 테두리(일부 초록·흰 금속) · 숫자·m·× 는 그대로.
  python tools/judge_ex.py → work/gfx/prev_judge.png
"""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ

SRC = os.path.join(ROOT, 'work', 'x', 'DR_H1002.SZ3', '001.bin')
Y, G, W = 0x2, 0xC, 0x3
J = lambda r, c, t, f='G14B', **k: dict(r=(r[0], r[1], r[2] - r[0], r[3] - r[1]), c=c, t=t, f=f, s='ring', e='nonbg', bg=0, all=False, **k)   # 칸 = x0,y0,x1,y1
JOBS = [
    J((4, 0, 92, 16), Y, '정지위치'), J((230, 0, 298, 16), G, '합격!'), J((302, 0, 414, 16), W, '운전평가'),
    J((0, 16, 112, 32), Y, '오버런'), J((0, 32, 112, 48), Y, '오버런'), J((0, 48, 112, 64), Y, '오버런'),
    J((270, 16, 298, 32), Y, '초'), J((270, 32, 298, 48), Y, '초'), J((270, 48, 298, 64), Y, '초'),
    J((270, 64, 298, 80), Y, '초'), J((270, 130, 298, 147), Y, '초'),
    J((308, 16, 382, 32), Y, '다이아'), J((10, 64, 82, 80), Y, '다이아'),
    J((302, 32, 358, 48), G, '합격!', a='l'), J((302, 48, 358, 66), G, '정각!', a='l'),
    J((148, 64, 196, 80), Y, '지연'), J((302, 66, 348, 80), Y, '조착', a='l'),
    J((0, 83, 124, 99), Y, '역구내재가속'), J((0, 104, 142, 120), Y, '역진입속도초과'),
    J((8, 130, 54, 147), Y, '합계'), J((62, 130, 148, 147), Y, '마이너스'),
    J((240, 151, 262, 168), Y, '초'), J((262, 151, 300, 168), Y, '없음'), J((300, 151, 346, 168), Y, '감점'),
    J((240, 171, 262, 188), Y, '초'), J((262, 171, 300, 188), Y, '없음'), J((300, 171, 346, 188), Y, '감점'),
]


def build():
    d = open(SRC, 'rb').read(); A = atlas.Atlas(d); done = GJ.apply(A, JOBS); new = A.save()
    return d, A, done, new


if __name__ == '__main__':
    d, A, done, new = build(); print('바꾼 곳', len(done), '새 셀', A.added)
    a = GJ.rgb(A.orig[:192, :416], d); b = GJ.rgb(A.can[:192, :416], d)
    sh = np.concatenate([a, np.full((4, 416, 3), 255, np.uint8), b], 0)
    p = os.path.join(ROOT, 'work', 'gfx', 'prev_judge.png')
    Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(p); print(p)
