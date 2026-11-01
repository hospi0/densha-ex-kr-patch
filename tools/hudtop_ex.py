# -*- coding: utf-8 -*-
r"""위 HUD(DR_B?X00.SZ3 항목 000, 노선마다 다름 — 노선·차종 이름만 다르고 나머지 같음) 한글화(2026-10-31)
  次駅到着時刻·現在時刻 = 주황 한 색(테두리 없음, 8줄) → 갈무리9 · 노선 이름 = 파랑 + 오른쪽 그림자 → 갈무리9
  持ち時間 = 초록 + 테두리 → 갈무리11 Bold 10줄(B10, 노선 이름과 1줄 띄움) · 秒 = 분할선 지나는 큰 상자(획 3px) → 갈무리7 2배, 분할선(행 49) 보존
  python tools/hudtop_ex.py           → work/gfx/prev_hudtop.png (다섯 노선 원본|한글, 3배)
"""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atlas, gfxjob as GJ

ROUTE = {1: '야마노테선205계', 2: '케이힌토호쿠선209계', 3: '토카이도선221계', 4: '산인본선키하58계', 7: '토카이도선221계'}


def route_job(n, A, d):
    """노선 이름: 팔레트 값(파랑 0x7CE0)으로 속 번호 찾고 속+그림자(0x3800) 범위를 노선마다 잼"""
    pal = np.frombuffer(d[0x40:0x240], '>u2')
    r = A.orig[12:27, 100:256]
    blues = [int(i) for i in np.nonzero(pal == 0x7CE0)[0]]
    fill = max(blues, key=lambda i: int((r == i).sum())); shd = set(np.nonzero(pal == 0x3800)[0].tolist())
    m = (r == fill) | np.isin(r, list(shd)); ys, xs = np.nonzero(m)
    x0, x1 = 100 + xs.min() - 1, 100 + xs.max() + 2; y0, y1 = 12 + ys.min() - 1, 12 + ys.max() + 2
    return dict(r=(x0, y0, x1 - x0, y1 - y0), c=fill, t=ROUTE[n], f='G9', s='shadowR', all=False, e=frozenset({fill} | shd))


def jobs(n, A=None, d=None):
    return [
        dict(r=(16, 15, 70, 11), c=0x6, t='다음도착시각', f='G9', s='plain', a='l', all=False),
        dict(r=(16, 37, 70, 11), c=0x6, t='현재시각', f='G9', s='plain', a='l', all=False),
        route_job(n, A, d),
        dict(r=(144, 24, 84, 14), c=0xB, t='남은시간', f='B10', s='ring', e='bg', all=False, dy=1),   # 노선 이름과 1줄 띄움(하스피: 살짝 줄이기)
        dict(r=(217, 39, 24, 18), c=0xE, t='초', f='A', s='plain', e='nonbg', keep=[10], all=False),
    ] + [dict(r=(417, y, 24, 18), c=0xE, t='초', f='A', s='plain', e='nonbg', keep=[10], all=False) for y in (273, 385, 417)]   # 숫자 띠 끝 秒 3벌(게임은 이걸 씀 — 하스피 «시간 표시 초가 한자»)


def build(n):
    d = open(os.path.join(ROOT, 'work', 'x', 'DR_B%dX00.SZ3' % n, '000.bin'), 'rb').read()
    A = atlas.Atlas(d); done = GJ.apply(A, jobs(n, A, d)); new = A.save()
    return d, A, done, new


if __name__ == '__main__':
    rows = []
    for n in (1, 2, 3, 4, 7):
        d, A, done, new = build(n)
        print(n, '새 셀', A.added)
        a = GJ.rgb(A.orig[8:60, 0:250], d); b = GJ.rgb(A.can[8:60, 0:250], d)
        rows.append(np.concatenate([a, np.full((a.shape[0], 4, 3), 255, np.uint8), b], 1))
        rows.append(np.full((3, rows[-1].shape[1], 3), 255, np.uint8))
    sh = np.concatenate(rows, 0)
    p = os.path.join(ROOT, 'work', 'gfx', 'prev_hudtop.png')
    Image.fromarray(sh).resize((sh.shape[1] * 3, sh.shape[0] * 3), Image.NEAREST).save(p); print(p)
