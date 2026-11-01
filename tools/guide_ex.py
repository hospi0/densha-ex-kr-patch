# -*- coding: utf-8 -*-
r"""안내 판넬(DR_B?X00.SZ3 항목 003) 한글화(2026-10-31) — 위쪽(판넬·힌트·화살표)은 5노선 같음, 아래 역 줄(448~495행)만 노선별
  글자 = 회색 단계 다듬은 꼴 + 옅은 회색 그림자(+1px) → 영역 안 줄을 자동으로 찾아(바탕 아닌 화소 있는 행 묶음)
  줄마다 «바탕 아닌 화소» 전부 바탕색으로 지우고, 갈무리(굵기 지정)로 원본 줄 왼쪽 x·세로 가운데에 다시 그림 + 그림자.
  색 표시: {r:…} 빨강 · {b:…} 파랑 · 그 밖 검정(바탕이 노랑인 화살표는 기본 빨강).
  python tools/guide_ex.py lines → 영역별 찾은 줄 · python tools/guide_ex.py → work/gfx/prev_guide.png
"""
import os, sys, collections, re
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atlas, gfxjob as GJ

# 줄 = (위, 아래, 왼쪽 x, 오른쪽 한계, 꼴, 한국어) — 원본 줄을 확대 그림·find_lines 로 잼(말풍선 모서리 피함)
LINES = [
    (3, 16, 10, 132, 'B', '{r:가속할 땐}'), (18, 31, 19, 132, 'B', '브레이크{b:해제}'),                       # 加速時は / ブレーキ解除
    (106, 119, 8, 156, 'B', '① {b:알림등}{r:점등확인}'), (120, 128, 6, 156, 'G9', '문이 닫히면 켜집니다'),   # ①車内信号点灯確認 / 扉が閉まると点灯します
    (193, 208, 8, 134, 'B', '② 브레이크{b:해제}'),                                                         # ②ブレーキ解除
    (282, 296, 8, 134, 'B', '③ {b:마스콘}을'), (297, 312, 32, 134, 'B', '앞으로 당긴다'),                  # ③マスコンを / 手前に倒す
    (3, 17, 176, 288, 'G11', '{b:속도 60km/h}'), (19, 32, 174, 288, 'G11', '쯤까지 {r:가속}'), (35, 47, 174, 288, 'G11', '합니다.'),
    (53, 65, 173, 318, 'G11', '속도가 붙으면'), (67, 79, 171, 318, 'G11', '{r:마스콘을 끕니다.}'), (81, 93, 174, 318, 'G11', '이것이 {b:타력주행}입니다.'),
    (99, 110, 177, 288, 'G11', '브레이크를'), (112, 123, 177, 288, 'G11', '잘 써서'), (124, 137, 171, 288, 'G11', '{r:정지위치에 정차!}'),
    (146, 159, 175, 288, 'G11', '해제 표지까지'), (161, 175, 172, 288, 'G11', '제한 속도를 지킨다.'),
    (179, 191, 177, 258, 'G11', '경적은'), (194, 207, 177, 258, 'G11', '발 페달'),
    (210, 223, 173, 288, 'G11', '파란 신호까지'), (225, 239, 172, 288, 'G11', '제한 속도를 지킨다.'),
]
WHITE = 0x20


def dark_mask(d):
    """글자 몸통 색: 밝기 낮거나(검정·짙은 회색) 채도 높은(빨강·파랑) 색 — 옅은 회색 그림자·흰 바탕 제외"""
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    r, g, b = pal & 31, pal >> 5 & 31, pal >> 10 & 31
    lum = (r + g + b) / 3; sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    return (lum < 14) | (sat > 12)


def find_lines(C, zone, bg, dm=None):
    x0, y0, x1, y1 = zone
    t = dm[C[y0:y1, x0:x1]] if dm is not None else C[y0:y1, x0:x1] != bg
    rows = [r for r in range(t.shape[0]) if t[r].any()]
    if not rows: return []
    ls = []; cur = [rows[0]]
    for r in rows[1:]:
        if r - cur[-1] > 1: ls.append(cur); cur = [r]
        else: cur.append(r)
    ls.append(cur); out = []
    for L in ls:
        xs = np.nonzero(t[L[0]:L[-1] + 1].any(0))[0]
        out.append((y0 + L[0], y0 + L[-1] + 1, x0 + xs.min(), x0 + xs.max() + 1))
    return out


def load(n=4):
    d = open(os.path.join(ROOT, 'work', 'x', 'DR_B%dX00.SZ3' % n, '003.bin'), 'rb').read()
    return d, atlas.Atlas(d)


def segs(t):
    """'{r:가}나{b:다}' → [(글자, 색키)]"""
    out = []; i = 0
    for m in re.finditer(r'\{([rb]):([^}]*)\}|([^{]+)', t):
        if m.group(3): out += [(c, 'k') for c in m.group(3)]
        else: out += [(c, m.group(1)) for c in m.group(2)]
    return out


def pal_index(d, rgb):
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    r, g, b = pal & 31, pal >> 5 & 31, pal >> 10 & 31
    return int(np.argmin((r - rgb[0]) ** 2 + (g - rgb[1]) ** 2 + (b - rgb[2]) ** 2))


def draw_lines(A, d, lines, bg):
    C = A.can
    col = {'k': pal_index(d, (0, 0, 0)), 'r': pal_index(d, (31, 0, 0)), 'b': pal_index(d, (0, 0, 31))}
    shadow = pal_index(d, (24, 23, 23))
    dm = dark_mask(d)
    for (y0, y1, x0, xr, f, t) in lines:                                         # 줄 띠(그림자 포함) 지움 — 행마다 «흰 바탕 안쪽» 구간만(말풍선 테두리 보존)
        out = 0                                                                  # 말풍선 바깥 = 투명(0)
        band = C[y0 - 1:y1 + 2, max(0, x0 - 6):xr + 2]
        band[(band != bg) & (band != out)] = bg
    for (y0, y1, x0, xr, f, t) in lines:
        sg = segs(t); plain = ''.join(c for c, _ in sg)
        lay, total = GJ.layout(plain, f)
        assert x0 + total + 1 <= xr, ('넘침', t, x0 + total, xr)
        gh = max(g.shape[0] for _, _, g in lay); yy = y0 + (y1 - y0 - gh) // 2
        keys = [k for c, k in sg if c != ' ']
        for n, (ch, gx, g) in enumerate(lay):                                    # 그림자 먼저(+1,+1), 위에 글자
            sub = C[yy + gh - g.shape[0] + 1:yy + gh + 1, x0 + gx + 1:x0 + gx + g.shape[1] + 1]
            m = g[:sub.shape[0], :sub.shape[1]] > 0; sub[m & (sub == bg)] = shadow
        for n, (ch, gx, g) in enumerate(lay):
            sub = C[yy + gh - g.shape[0]:yy + gh, x0 + gx:x0 + gx + g.shape[1]]
            sub[g[:sub.shape[0], :sub.shape[1]] > 0] = col[keys[n]]


# 노란 화살표 글자: (x0, y0, x1, y1, 한국어, 세로쓰기) — 칸 안 빨강(0x13)·주황(0x18) 지우고 갈무리11 Bold 빨강, 가운데
ARROWS = [(0, 368, 100, 383, '속도계를 봐라!', False), (0, 401, 69, 415, '정지위치', False), (0, 432, 20, 511, '브레이크강약', True)]
YEL, RED, ORG = 0x1E, 0x13, 0x18


def draw_arrows(A):
    C = A.can
    for x0, y0, x1, y1, t, vert in ARROWS:
        reg = C[y0:y1, x0:x1]; reg[np.isin(reg, [RED, ORG])] = YEL
        if not vert:
            lay, total = GJ.layout(t, 'B'); gh = max(g.shape[0] for _, _, g in lay)
            assert total <= x1 - x0, ('넘침', t, total)
            xx = x0 + (x1 - x0 - total) // 2; yy = y0 + (y1 - y0 - gh) // 2
            for ch, gx, g in lay:
                sub = C[yy + gh - g.shape[0]:yy + gh, xx + gx:xx + gx + g.shape[1]]; sub[g > 0] = RED
        else:
            gs = [GJ.syl(ch, 'B') for ch in t]; step = 13; total = step * (len(gs) - 1) + gs[-1].shape[0]
            assert total <= y1 - y0, ('세로 넘침', t, total)
            yy = y0 + (y1 - y0 - total) // 2
            for i, g in enumerate(gs):
                xx = x0 + (x1 - x0 - g.shape[1]) // 2
                sub = C[yy + i * step:yy + i * step + g.shape[0], xx:xx + g.shape[1]]; sub[g > 0] = RED


# ── 아래 역 이름 줄(노선별): (점 가운데 x, 역 이름) — 한자 세로 쌓기 → 한글 세로 쌓기(갈무리9, 넘치면 7), 역 색 + 검정 테두리
STN_R = {1: '渋谷 恵比寿 目黒 五反田 大崎 品川 田町 浜松町 新橋 有楽町 東京', 2: '品川 大井町 大森 蒲田 川崎 鶴見 新子安 東神奈川 横浜',
         3: '京都 西大路 向日町 長岡京 高槻 茨木 新大阪 大阪', 4: '亀岡 馬堀 保津峡 嵯峨嵐山 太秦 花園 二条 丹波口 京都',
         7: '高槻 摂津富田 茨木 千里丘 岸辺 吹田 東淀川 新大阪 大阪'}
STN_X = {1: list(range(136, 377, 24)), 2: list(range(160, 353, 24)), 3: [136, 160, 184, 208, 256, 304, 352, 376],
         4: list(range(160, 353, 24)), 7: list(range(160, 353, 24))}
STN_BLACK, STN_MARK, STN_TOP = 0xAF, 0xAE, 457
STN_DIC = os.path.join(ROOT, '..', 'densha-pro-kr-patch', 'work', 'text', 'stations.tsv')


def stn_dict():
    D = {}
    for f in (STN_DIC, os.path.join(os.path.dirname(STN_DIC), 'stn_board_kr.tsv')):
        for ln in open(f, encoding='utf-8'):
            c = ln.rstrip('\n').split('\t')
            if len(c) >= 2 and c[0] not in D: D[c[0]] = c[1]
    return D


def draw_stations(A, n):
    C = A.can; D = stn_dict(); names = STN_R[n].split(); xs = STN_X[n]
    assert len(names) == len(xs)
    for cx, jp in zip(xs, names):
        kr = D[jp]; x0, x1 = cx - 9, cx + 9; bot = 495 if cx == 136 else 511
        reg = A.orig[STN_TOP:bot, x0:x1]; cnt = collections.Counter(reg.ravel().tolist())
        fill = next(c for c, _ in cnt.most_common() if c not in (0, STN_BLACK, STN_MARK))
        er0 = bot
        bot = min(bot, STN_TOP + 40)                                                      # ★게임은 역 이름 줄을 40줄까지만 잘라 씀(하스피 «역 이름 아래 잘림», 원본 최장 39줄)
        C[STN_TOP:er0, x0:x1][np.isin(C[STN_TOP:er0, x0:x1], [fill, STN_BLACK])] = 0
        er = C[STN_TOP:bot, x0:x1]
        cols = 1
        for f, step in (('G9', 10), ('G9', 9), ('G7', 8), ('G7', 7)):
            gs = [GJ.syl(ch, f) for ch in kr]
            if step * (len(gs) - 1) + gs[-1].shape[0] + 2 <= bot - STN_TOP: break
        else:                                                                             # 7글자 역(사가아라시야마 등) → 두 줄 세로(오른쪽 줄 먼저 = 세로쓰기 순서)
            f, step, cols = 'G7', 8, 2; gs = [GJ.syl(ch, f) for ch in kr]
            per = (len(gs) + 1) // 2
            assert step * (per - 1) + gs[-1].shape[0] + 2 <= bot - STN_TOP, ('세로 넘침', kr)
        ink = np.zeros((bot - STN_TOP, x1 - x0), bool)
        for i, g in enumerate(gs):
            if cols == 1: gx = (x1 - x0 - g.shape[1]) // 2; gy = 1 + i * step
            else: col, j = divmod(i, per); gx = (9 if col == 0 else 1); gy = 1 + j * step
            ink[gy:gy + g.shape[0], gx:gx + g.shape[1]] |= g > 0
        p = np.pad(ink, 1); ring = np.zeros_like(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): ring |= np.roll(np.roll(p, dy, 0), dx, 1)
        ring = ring[1:-1, 1:-1] & ~ink
        er[ring & (er == 0)] = STN_BLACK; er[ink] = fill


def build(n):
    d, A = load(n)
    draw_lines(A, d, LINES, WHITE)
    draw_arrows(A)
    draw_stations(A, n)
    new = A.save()
    return d, A, new


if __name__ == '__main__':
    rows = []
    for n in (1, 2, 3, 4, 7):
        d, A, new = build(n); print(n, '새 셀', A.added)
        if n == 4:
            a = GJ.rgb(A.orig[0:512, 0:330], d); b = GJ.rgb(A.can[0:512, 0:330], d)
            sh = np.concatenate([a, np.full((512, 4, 3), 255, np.uint8), b], 1)
            p = os.path.join(ROOT, 'work', 'gfx', 'prev_guide.png')
            Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(p); print(p)
        a = GJ.rgb(A.orig[444:512, 126:392], d); b = GJ.rgb(A.can[444:512, 126:392], d)
        rows.append(np.concatenate([a, np.full((68, 4, 3), 255, np.uint8), b], 1)); rows.append(np.full((3, 536, 3), 255, np.uint8))
    sh = np.concatenate(rows, 0); p = os.path.join(ROOT, 'work', 'gfx', 'prev_guide_stations.png')
    Image.fromarray(sh).resize((sh.shape[1] * 3, sh.shape[0] * 3), Image.NEAREST).save(p); print(p)
