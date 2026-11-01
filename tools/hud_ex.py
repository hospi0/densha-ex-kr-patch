# -*- coding: utf-8 -*-
r"""운전 HUD(DR_B?X00.SZ3 항목 001, 다섯 노선 같음) 그림 글자 한글화(2026-10-31, 하스피 꼴 B 결정)
  화면 판 = 아틀라스 조각 조합(tools/hudmap.py 로 확인):
    정지 위치 판 9칸 = [글자 16px][막대 칸 16px — 막대 높이별 프레임마다 글자 사본][글자 2개 40px] → 한글 음절 1:1
    계기 상자(비상·해제·끔·마스콘) = 상자 색마다 사본, 글자 = 속 + 오른쪽 아래 그림자
  글자 사본 = 본보기 속 모양으로 아틀라스 전체 검색(색 무관) → 사본마다 속 색 그대로, 테두리/그림자 색은 주변에서 자동.
  지우기 = 속 + 그 둘레(테두리/그림자 색) 화소를 8×8 셀 단위로 2칸 주기 바탕에서 메움(셀 공유 깨지 않음, 새 셀 0 목표).
  꼴: B = 갈무리11 Bold(16px 칸) · G9 = 갈무리9(작은 상자) · G7 = 갈무리7(아주 작은 칸) — 축소 없음·중간 색 없음.
  python tools/hud_ex.py            → work/gfx/prev_hud_*.png (스테이트 화면 원본|한글 4배 + 아틀라스 전후)
  python tools/hud_ex.py --out FILE → 새 001 바이트 저장
"""
import os, sys, shutil, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atlas, pixfont as PF, vdp2render as R

SRC = os.path.join(ROOT, 'work', 'x', 'DR_B4X00.SZ3', '001.bin')

# 본보기: (x, y, w, h) 속 색, 한국어, 꼴, 둘레('ring' 8방향 1px / 'shadow' 오른쪽·아래), 맞춤
JOBS = [
    dict(r=(0, 48, 16, 16), c=0x1D, t='정', f='B', s='ring'),             # 停
    dict(r=(272, 48, 16, 16), c=0x1D, t='지', f='B', s='ring'),           # 止 (막대 프레임)
    dict(r=(32, 48, 40, 16), c=0x1D, t='위치', f='B', s='ring'),          # 位置
    dict(r=(72, 32, 16, 16), c=0x1D, t='합', f='B', s='ring'),            # 合
    dict(r=(416, 32, 16, 16), c=0x1D, t='격', f='B', s='ring'),           # 格 (막대 프레임)
    dict(r=(104, 32, 40, 16), c=0x1D, t='범위', f='B', s='ring'),         # 範囲
    dict(r=(72, 112, 16, 16), c=0x06, t='오', f='B', s='ring'),           # オ
    dict(r=(160, 112, 16, 16), c=0x06, t='버', f='B', s='ring'),          # ー (막대 프레임)
    dict(r=(104, 112, 40, 16), c=0x06, t='런', f='B', s='ring', a='l'),   # ーラン
    dict(r=(0, 64, 16, 16), c=0x1D, t='남은', f='G7', s='ring'),          # あと
    dict(r=(34, 163, 26, 12), c=0x17, t='비상', f='G9', s='shadow'),      # 非常 (상자 안쪽만)
    dict(r=(34, 235, 26, 12), c=0x1C, t='해제', f='G9', s='shadow'),      # 解除
    dict(r=(324, 163, 24, 12), c=0x1D, t='끔', f='G9', s='shadow'),       # 切
    dict(r=(322, 209, 26, 7), c=0x17, t='마스콘', f='G7', s='shadow'),    # マスコン
]


def syl(ch, f):
    if f == 'B': return PF.cell(ch, 11, bold=True)
    return PF.cell(ch, 9 if f == 'G9' else 7)


def word(text, w, h, f, style, align='c'):
    pitch = {'B': 13, 'G9': 10, 'G7': 8}[f]
    gs = [syl(c, f) for c in text]
    total = pitch * (len(gs) - 1) + gs[-1].shape[1]
    gh = max(g.shape[0] for g in gs)
    assert total <= w + 2 and gh <= h + 1, ('넘침', text, total, w, gh, h)
    ink = np.zeros((h, w), bool)
    x0 = 1 if align == 'l' else (w - total) // 2
    y0 = max(0, (h - gh) // 2 - (1 if style == 'shadow' and (h - gh) % 2 == 0 and h - gh > 0 else 0))
    for i, g in enumerate(gs):
        sub = ink[y0:y0 + g.shape[0], max(0, x0 + i * pitch):x0 + i * pitch + g.shape[1]]
        gg = g[:sub.shape[0], g.shape[1] - sub.shape[1]:] if x0 + i * pitch < 0 else g[:sub.shape[0], :sub.shape[1]]
        sub |= gg > 0
    p = np.pad(ink, 1); edge = np.zeros_like(p)
    nb = [] if style == 'plain' else ([(1, 0), (0, 1), (1, 1)] if style == 'shadow' else [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    for dy, dx in nb:
        edge |= np.roll(np.roll(p, dy, 0), dx, 1)
    lv = np.zeros((h, w), np.uint8); lv[edge[1:-1, 1:-1]] = 1; lv[ink] = 3
    return lv


def edge_color(A, x, y, w, h, col, style):
    """속 둘레에서 가장 많은 색(속 색 제외)"""
    r = A.orig[y:y + h, x:x + w]; f = r == col
    nb = [(1, 0), (0, 1), (1, 1)] if style == 'shadow' else [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    cnt = collections.Counter()
    for yy, xx in np.argwhere(f):
        for dy, dx in nb:
            Y, X = yy + dy, xx + dx
            if 0 <= Y < h and 0 <= X < w and r[Y, X] != col: cnt[int(r[Y, X])] += 1
    return cnt.most_common(1)[0][0]


def inner_colors(A, x, y, w, h, col, ec):
    """획 안 하이라이트 색: 칸 안 화소의 80% 이상이 속 색과 4방향으로 붙은 색(테두리·바탕 제외)"""
    r = A.orig[y:y + h, x:x + w]; f = r == col; p = np.pad(f, 1)
    adj = (np.roll(p, 1, 0) | np.roll(p, -1, 0) | np.roll(p, 1, 1) | np.roll(p, -1, 1))[1:-1, 1:-1]
    out = set()
    for c in set(r.ravel().tolist()) - {col, ec, 0}:
        mk = r == c
        if mk.sum() and (mk & adj).sum() >= 0.8 * mk.sum() and mk.sum() <= f.sum() // 3: out.add(c)
    return out


def apply(A):
    done = []
    for j in JOBS:
        x, y, w, h = j['r']; c = j['c']
        if c is None:                                       # 속 색 = 본보기 칸 안 바탕 다음으로 많은 색
            cnt = collections.Counter(A.orig[y:y + h, x:x + w].ravel()).most_common(); c = cnt[1][0]
        tm = A.orig[y:y + h, x:x + w] == c
        hits = A.find(tm)
        assert hits, ('사본 없음', j['t'])
        for X, Y, col in hits:
            ec = edge_color(A, X, Y, w, h, col, j['s'])
            fills = {col} | inner_colors(A, X, Y, w, h, col, ec)
            m = A.glyph_mask(X, Y, w, h, fills, {ec})
            if j['s'] == 'shadow':                        # 그림자는 오른쪽·아래만
                f = A.orig[Y:Y + h, X:X + w] == col; p = np.pad(f, 1); sh = np.zeros_like(p)
                for dy, dx in ((1, 0), (0, 1), (1, 1)): sh |= np.roll(np.roll(p, dy, 0), dx, 1)
                m = f | (sh[1:-1, 1:-1] & (A.orig[Y:Y + h, X:X + w] == ec))
            if j['s'] == 'ring':
                A.erase_mixed(X, Y, w, h, m)
            else:                                           # 상자 글자 = 바탕 한 색 → 그 색으로(틀 색 끌어오지 않음)
                r = A.orig[Y:Y + h, X:X + w]
                bg = collections.Counter(r[~m].ravel().tolist()).most_common(1)[0][0]
                A.can[Y:Y + h, X:X + w][m] = bg
            A.put(X, Y, word(j['t'], w, h, j['f'], j.get('ds', j['s']), j.get('a', 'c')), col, ec)   # ds = 그릴 때만 다른 둘레(지우기는 s)
            done.append((j['t'], X, Y, col, ec))
    return done


def build():
    d = open(SRC, 'rb').read(); A = atlas.Atlas(d); done = apply(A); new = A.save()
    if A.added:                                            # 열 메우기가 셀 공유를 깼으면 → 전부 셀 안 메우기로
        global COLUMN
        print('열 메우기로 새 셀 %d → 셀 안 메우기로 다시' % A.added)
        atlas.Atlas.erase_column = lambda self, x, y, w, h, m, reach=24: self.erase_cells(x, y, w, h, m)
        A = atlas.Atlas(d); done = apply(A); new = A.save()
    return d, A, done, new


def screen(st, new, box):
    A2 = atlas.Atlas(new)
    src = os.path.join(ROOT, 'work', 'mem', st); tmp = os.path.join(ROOT, 'work', 'mem', '_prev')
    shutil.rmtree(tmp, ignore_errors=True); shutil.copytree(src, tmp)
    v = bytearray(open(os.path.join(src, 'VDP2_VRAM.bin'), 'rb').read())
    cb = A2.cells.astype(np.uint8).tobytes(); v[0x20000:0x20000 + len(cb)] = cb
    open(os.path.join(tmp, 'VDP2_VRAM.bin'), 'wb').write(v)
    a = np.array(R.render(st, 1)[0]); b = np.array(R.render('_prev', 1)[0])
    shutil.rmtree(tmp, ignore_errors=True)
    pa, pb = a[box], b[box]
    return np.concatenate([pa, np.full((pa.shape[0], 4, 3), 255, np.uint8), pb], 1)


def preview():
    d, A, done, new = build()
    print('사본', len(done), '새 셀', A.added)
    for t, X, Y, col, ec in done: pass
    out = os.path.join(ROOT, 'work', 'gfx'); os.makedirs(out, exist_ok=True)
    shots = [('s40', (slice(140, 228), slice(248, 328)), 'stop'), ('s48', (slice(140, 228), slice(248, 328)), 'over'),
             ('s40', (slice(150, 228), slice(70, 100)), 'mascon'), ('s48', (slice(0, 120), slice(270, 320)), 'notch')]
    for st, box, nm in shots:
        sh = screen(st, new, box)
        p = os.path.join(out, 'prev_hud_%s.png' % nm)
        Image.fromarray(sh).resize((sh.shape[1] * 4, sh.shape[0] * 4), Image.NEAREST).save(p); print(p)
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)

    def rgb(C):
        e = pal[C]; im = np.stack([(e & 31) << 3, (e >> 5 & 31) << 3, (e >> 10 & 31) << 3], -1).astype(np.uint8); im[C == 0] = 40; return im
    at = np.concatenate([rgb(A.orig[:256]), np.full((4, 512, 3), 255, np.uint8), rgb(A.can[:256])], 0)
    p = os.path.join(out, 'prev_hud_atlas.png')
    Image.fromarray(at).resize((at.shape[1] * 2, at.shape[0] * 2), Image.NEAREST).save(p); print(p)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--out']:
        d, A, done, new = build(); assert A.added == 0, A.added
        open(sys.argv[2], 'wb').write(new); print(sys.argv[2], len(new))
    else:
        preview()
