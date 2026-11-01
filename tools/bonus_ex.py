# -*- coding: utf-8 -*-
r"""보너스(연결) 게임 그림 BONUS.BIN(2워드)·BONUS_02.BIN(1워드, = DR_H?002.SZ3 항목 002) 한글화(2026-11-01) — tools/rectjob.py
  python tools/bonus_ex.py → work/gfx/prev_bonus.png · prev_bonus02.png
"""
import os, sys, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ, rectjob as RJ

DISC = os.path.join(ROOT, 'work', 'disc0')
# 공통(두 그림 같은 배치 아님 — 그림마다 좌표)
GRAD = [(30, 24, 0)] * 5 + [(30, 22, 0)] * 4 + [(30, 19, 0)] * 4 + [(30, 16, 0)] * 4 + [(30, 11, 0)] * 5 + [(30, 0, 0)] * 6   # 보너스게임 노랑→빨강(원본 줄 색)
BONUS02 = [
    dict(r=(0, 143, 92, 160), t='정지위치', k='T', f='G14B'), dict(r=(94, 143, 192, 160), t='정지위치', k='T', f='G14B'),
    dict(r=(0, 162, 22, 176), t='남은', k='T', f='G9'), dict(r=(94, 162, 116, 176), t='남은', k='T', f='G9'),
    dict(r=(10, 180, 180, 199), t='시간 안에 충격 없이', k='M', f='G14B', a='l'),
    dict(r=(10, 202, 180, 220), t='화차를 연결하라', k='M', f='G14B', a='l'),
    dict(r=(2, 231, 111, 249), t='연결 실패', k=32, f='B15', s='plain', fill=(0, 0, 31)),
    dict(r=(114, 231, 221, 249), t='연결 성공', k=241, f='B15', s='plain', fill=(0, 0, 31)),
    dict(r=(230, 226, 441, 252), t='보너스게임', k=241, f='B2', s='ring', fill=GRAD[:26], rc=(0, 0, 0)),
]
BONUS = [
    dict(r=(130, 14, 232, 30), t='남은시간', k='M'),
    dict(r=(216, 30, 240, 50), t='초', k='M'),
    dict(r=(352, 0, 444, 16), t='정지위치', k='T', f='G14B'), dict(r=(352, 31, 448, 47), t='정지위치', k='T', f='G14B'),
    dict(r=(352, 18, 374, 33), t='남은', k='T', f='G9'), dict(r=(352, 51, 374, 66), t='남은', k='T', f='G9'),
    dict(r=(352, 108, 440, 130), t='보 너 스', k=('F', {219, 231}), f='G14BB', s='ring', fill=(0, 30, 0), rc=(1, 1, 1), inpaint=2),
    dict(r=(360, 136, 452, 154), t='시간초과', k='M'),
    dict(r=(110, 166, 224, 200), t='충격미터', k=253, f='B2', s='plain', fill=(30, 0, 11)),
    dict(r=(228, 168, 284, 182), t='합격범위', k='M', f='G9'),
    dict(r=(286, 168, 316, 182), t='위험', k='M', f='G9'),
    dict(r=(470, 376, 496, 392), t='초', k='T', f='G14W', s='ring'), dict(r=(470, 392, 496, 408), t='초', k='T', f='G14W', s='ring'),
    dict(r=(10, 388, 180, 407), t='시간 안에 충격 없이', k='M', f='G14B', a='l'),
    dict(r=(10, 410, 180, 428), t='화차를 연결하라', k='M', f='G14B', a='l'),
    dict(r=(2, 439, 111, 457), t='연결 실패', k=44, f='B15', s='shadow', fill=0, rc=201),
    dict(r=(112, 439, 221, 457), t='연결 성공', k=221, f='B15', s='shadow', fill=0, rc=201),
    dict(r=(226, 434, 446, 461), t='보너스게임', k=221, f='B2', s='ring', fill=GRAD[:27], rc=(0, 0, 0)),
]


def _rgbidx(pal, v):
    if isinstance(v, tuple) and len(v) == 3 and all(isinstance(x, int) for x in v):
        return int(np.argmin([((p & 31) - v[0]) ** 2 + ((p >> 5 & 31) - v[1]) ** 2 + ((p >> 10 & 31) - v[2]) ** 2 + (1000 if i == 0 else 0) for i, p in enumerate(pal)]))
    if isinstance(v, list): return [_rgbidx(pal, x) for x in v]
    return v


HUD_DY = {'BONUS': 79, 'BONUS_02': -161}                 # 운전 HUD(001) 버튼 판과 같은 그림 — 위아래 차이


def hud_buttons(A, d, name):
    """비상·해제·끔·마스콘 = hud_ex(하스피 통과)와 같은 작업, 색 번호만 이 그림 팔레트로"""
    import hud_ex
    hp = np.frombuffer(open(hud_ex.SRC, 'rb').read()[0x40:0x240], '>u2').astype(int); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    jobs = []
    for j in hud_ex.JOBS:
        if j['t'] not in ('비상', '해제', '끔'): continue                         # 마스콘 = masukon_labels(단색 칸 통째로 밀고 쓰기)
        x, y, w, h = j['r']; v = int(hp[j['c']]); y += HUD_DY[name]
        reg = A.orig[y:y + h, x:x + w]; same = [i for i in range(256) if int(pal[i]) == v]
        c = max(same, key=lambda i: int((reg == i).sum())) if same else None
        if c is None or not (reg == c).any():                                    # 같은 색 없으면 칸 안 가장 가까운 색
            cs = set(reg.ravel().tolist()); c = min(cs, key=lambda i: ((pal[i] & 31) - (v & 31)) ** 2 + ((pal[i] >> 5 & 31) - (v >> 5 & 31)) ** 2 + ((pal[i] >> 10 & 31) - (v >> 10 & 31)) ** 2)
        jobs.append(dict(j, r=(x, y, w, h), c=c, **({'ds': 'plain'} if j['t'] == '마스콘' else {})))   # 마스콘: 칸이 7줄이라 그림자가 덩어리 → 그림자 없이
    keep = hud_ex.JOBS; hud_ex.JOBS = jobs
    try: done = hud_ex.apply(A)
    finally: hud_ex.JOBS = keep
    masukon_labels(A, name)
    return done


MASU_Y = {'BONUS': 286, 'BONUS_02': 46}
MASU_TXT = {'BONUS': 120, 'BONUS_02': 179}            # マスコン 칸 속(26×13, 단색) 맨 위 행 — x 322+32i, 6칸


def masukon_labels(A, name):
    """하스피: 단색 바탕이니 칸을 통째로 바탕색으로 밀고 글자만 쓴다(그림자 없음, 글자색 = 원래 글자 밝은 색)"""
    y0 = MASU_Y[name]
    for i in range(6):
        x0 = 322 + 32 * i; o = A.orig[y0:y0 + 13, x0:x0 + 26]
        cnt = collections.Counter(o.ravel().tolist()); bg = cnt.most_common(1)[0][0]
        pal = np.frombuffer(A.d[0x40:0x240], '>u2').astype(int); lum = lambda c: (pal[c] & 31) + (pal[c] >> 5 & 31) + (pal[c] >> 10 & 31)
        tc = collections.Counter(o[4:11][o[4:11] != bg].tolist())
        txt = MASU_TXT[name]                                                         # 원래 マスコン 글자색(모든 칸 같은 노란 계열)
        A.can[y0:y0 + 13, x0:x0 + 26] = bg
        lv = GJ.word('마스콘', 26, 13, 'G7', 'plain')
        A.can[y0:y0 + 13, x0:x0 + 26][lv > 0] = txt


def build(name, jobs):
    d = open(os.path.join(DISC, name + '.BIN'), 'rb').read(); A = atlas.Atlas(d)
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    jobs = [{k: (_rgbidx(pal, v) if k in ('fill', 'rc') else v) for k, v in j.items()} for j in jobs]
    done = RJ.apply(A, d, jobs) + hud_buttons(A, d, name)
    if name == 'BONUS':                                                          # 합격범위 아래 괄호 줄(184~189행) — 하스피: 잡스런 줄 삭제
        A.can[184:190, 226:288] = 253
    new = A.save()
    return d, A, done, new


if __name__ == '__main__':
    for name, jobs, out in (('BONUS_02', BONUS02, 'prev_bonus02.png'), ('BONUS', BONUS, 'prev_bonus.png')):
        d, A, done, new = build(name, jobs); print(name, '바꾼 곳', len(done), '새 셀', A.added)
        ys, xs = np.nonzero(A.orig); H, W = ys.max() + 1, xs.max() + 1
        a = GJ.rgb(A.orig[:H, :W], d); b = GJ.rgb(A.can[:H, :W], d)
        sh = np.concatenate([a, np.full((H, 4, 3), 255, np.uint8), b], 1)
        Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', out))
