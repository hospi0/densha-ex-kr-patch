# -*- coding: utf-8 -*-
r"""그림 글자 «작업 목록» 공용(2026-10-31, hud_ex.py 에서 뽑음) — 아틀라스(tools/atlas.py) 위에서 지우고 갈무리로 다시 그림
  작업 dict:
    r=(x,y,w,h) 본보기 칸 · c=속 색 · t=한국어 · f=꼴('B' 갈무리11 Bold · 'B10' 그것에서 같은 줄 하나 뺀 10줄 · 'G9' · 'G7' · 'A' 갈무리7 2배 · 'A9' 갈무리9 2배)
    s=둘레('ring' 8방향 1px · 'shadow' 오른쪽·아래 · 'shadowR' 오른쪽만 · 'plain' 없음) · a=맞춤('c'·'l'·'r')
    e=지우기('auto': ring → 셀별 혼합 / 그 밖 → 칸 바탕 한 색 · 'nonbg': 칸 안 바탕 아닌 화소 전부(keep 행 제외) · {색…}: 그 색 전부)
    dy=세로 밀기(+ 아래) · keep=[행…] 지우지 않고 다시 그린 뒤에도 원본으로 되돌릴 칸 안 행(분할선 등) · all=False 면 본보기 한 곳만(검색 안 함)
  한글 = 고정 간격(꼴별), 그 밖 글자(숫자·영문) = 글자 폭 + 1.
"""
import collections
import numpy as np
import pixfont as PF

PITCH = {'B3': 36, 'AB': 17, 'G11': 12, 'B': 13, 'B10': 13, 'G9': 10, 'G7': 8, 'A': 16, 'A9': 20, 'G14': 15, 'G14B': 16, 'G14W': 22, 'AW': 23, 'G14P': 16, 'G28': 30, 'B2': 26, 'B15': 20, 'G14BB': 16}


def syl(ch, f):
    if f == 'B': return PF.cell(ch, 11, bold=True)
    if f == 'B3':                                     # 갈무리11 Bold 정확히 3배(아주 큰 글자 — 事故)
        return np.kron(PF.cell(ch, 11, bold=True), np.ones((3, 3)))
    if f == 'B10':                                   # 갈무리11 Bold 에서 «바로 아래와 같은 줄» 하나 빼 10줄(PS1 판 glyph10 방식) — 가운데에 가까운 줄
        g = PF.cell(ch, 11, bold=True); h = g.shape[0]
        same = [i for i in range(1, h - 1) if np.array_equal(g[i], g[i + 1])]
        i = min(same, key=lambda k: abs(k - h // 2)) if same else h // 2
        return np.delete(g, i, 0)
    if f == 'AB':                                     # 갈무리7 2배 + 가로 1px 굵게(획 3px — 乗務完了 같은 굵은 원본)
        g = syl(ch, 'A'); g2 = np.zeros((g.shape[0], g.shape[1] + 1)); g2[:, :-1] = g; g2[:, 1:] = np.maximum(g2[:, 1:], g)
        return g2
    if f in ('A', 'A9'):
        g = PF.cell(ch, 7 if f == 'A' else 9); xs = np.nonzero(g.max(0))[0]
        g = g[:, :xs.max() + 1] if len(xs) else g
        return np.kron(g, np.ones((2, 2)))
    if f == 'G11': return PF.cell(ch, 11)
    if f in ('G14', 'G14P'): return PF.cell(ch, 14)
    if f == 'G14BB':                                  # 갈무리14 가로·세로 1px 굵게(1px 틈은 남김) — 15줄 굵은 원본(秒)
        g = syl(ch, 'G14B') > 0; h, w = g.shape; o = np.zeros((h + 1, w), bool); o[:h] = g
        for y in range(h):
            below2 = g[y + 2] if y + 2 < h else np.zeros(w, bool)
            o[y + 1] |= g[y] & ~below2
        return o.astype(float)
    if f == 'B15':                                    # 갈무리11 Bold 1.5배(12→18줄, 획 2→3px 고르게) — 18줄 띠 글자(연결 실패)
        g = PF.cell(ch, 11, bold=True); yi = (np.arange(int(g.shape[0] * 1.5)) / 1.5).astype(int); xi = (np.arange(int(g.shape[1] * 1.5)) / 1.5).astype(int)
        return g[yi][:, xi]
    if f == 'B2': return np.kron(PF.cell(ch, 11, bold=True), np.ones((2, 2)))   # 갈무리11 Bold 2배(획 4px — 무지개 큰 제목)
    if f == 'G28': return np.kron(PF.cell(ch, 14), np.ones((2, 2)))        # 갈무리14 2배(무지개 큰 제목)
    if f == 'AW':                                     # 갈무리7 세로 2배·가로 3배 — 넓적하고 굵은 큰 제목(運転終了·乗務完了)
        g = PF.cell(ch, 7); xs = np.nonzero(g.max(0))[0]; g = g[:, :xs.max() + 1] if len(xs) else g
        return np.kron(g, np.ones((2, 3)))
    if f == 'G14W':                                   # 갈무리14 가로 4/3 배(열 3개마다 하나 겹침) + 굵게 — 넓적한 큰 제목(運転終了)
        g = PF.cell(ch, 14); cols = [i for i in range(g.shape[1]) for _ in range(2 if i % 3 == 1 else 1)]
        g = g[:, cols]; g2 = np.zeros((g.shape[0], g.shape[1] + 1)); g2[:, :-1] = g; g2[:, 1:] = np.maximum(g2[:, 1:], g)
        return g2
    if f == 'G14B':                                   # 갈무리14 + 가로 1px 굵게(運転評価 같은 굵은 16px 원본)
        g = PF.cell(ch, 14); g2 = np.zeros((g.shape[0], g.shape[1] + 1)); g2[:, :-1] = g; g2[:, 1:] = np.maximum(g2[:, 1:], g)
        return g2
    return PF.cell(ch, 9 if f == 'G9' else 7)


def layout(text, f):
    """→ [(글자, x, 글리프)], 전체 폭 — 한글 고정 간격, 그 밖 글자 폭+1, 공백 = 간격 절반"""
    pitch = PITCH[f]; out = []; x = 0
    for ch in text:
        if ch == ' ':
            x += pitch // 2; continue
        g = syl(ch, f); cols = np.nonzero(g.max(0))[0]
        if not is_hangul(ch) and len(cols): g = g[:, cols.min():cols.max() + 1]
        out.append((ch, x, g)); x += pitch if is_hangul(ch) else g.shape[1] + (2 if f in ('A', 'A9', 'AB', 'AW') else 1)
    return out, (out[-1][1] + out[-1][2].shape[1] if out else 0)


def is_hangul(ch):
    return 0xAC00 <= ord(ch) <= 0xD7A3


def word(text, w, h, f, style, align='c', dy=0):
    pitch = PITCH[f]; xs = []; x = 0; gs = []
    for ch in text:
        if ch == ' ':
            x += pitch // 2; continue                                      # 공백 = 반 칸(G14P 도 — 하스피 «키 컨피그 벌어짐»)
        g = syl(ch, f)
        cols = np.nonzero(g.max(0))[0]
        if f == 'G14P':
            gs.append(g); xs.append(x); x += pitch; continue
        if not is_hangul(ch) and len(cols): g = g[:, cols.min():cols.max() + 1]
        gs.append(g); xs.append(x)
        x += pitch if is_hangul(ch) else g.shape[1] + (2 if f in ('A', 'A9', 'AB', 'AW') else 1)
    total = xs[-1] + gs[-1].shape[1]
    gh = max(g.shape[0] for g in gs)
    assert total <= w + 2 and gh <= h + 1, ('넘침', text, total, w, gh, h)
    ink = np.zeros((h, w), bool)
    x0 = (0 if f == 'G14P' else 1) if align == 'l' else (w - 1 - total if align == 'r' else (w - total) // 2)
    y0 = min(max(0, (h - gh) // 2 + dy), h - gh)
    for g, gx in zip(gs, xs):
        gy = y0 + (gh - g.shape[0])
        sub = ink[gy:gy + g.shape[0], max(0, x0 + gx):x0 + gx + g.shape[1]]
        sub |= g[:sub.shape[0], :sub.shape[1]] > 0
    nb = {'ring': [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)], 'oring': [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)], 'shadow': [(1, 0), (0, 1), (1, 1)],
          'shadowR': [(0, 1)], 'plain': []}[style]
    p = np.pad(ink, 1); edge = np.zeros_like(p)
    for dy, dx in nb:
        edge |= np.roll(np.roll(p, dy, 0), dx, 1)
    lv = np.zeros((h, w), np.uint8); lv[edge[1:-1, 1:-1]] = 1; lv[ink] = 3
    if style == 'oring':                                     # 바깥 테두리만 — 글자 속 구멍(ㅇ·ㅁ 안)은 비워 둠(4방향으로 바깥과 이어진 빈칸만)
        out = np.zeros((h + 2, w + 2), bool); free = ~np.pad(ink, 1); out[0, :] = out[-1, :] = out[:, 0] = out[:, -1] = True
        while True:
            n = out.copy()
            n[1:] |= out[:-1]; n[:-1] |= out[1:]; n[:, 1:] |= out[:, :-1]; n[:, :-1] |= out[:, 1:]
            n &= free
            if (n == out).all(): break
            out = n
        lv[(lv == 1) & ~out[1:-1, 1:-1]] = 0
        pi = np.pad(ink, 1); sand = (pi[:-2, 1:-1] & pi[2:, 1:-1]) | (pi[1:-1, :-2] & pi[1:-1, 2:])   # 1px 틈(위아래·좌우 모두 글자)은 비워 획 구분
        lv[(lv == 1) & sand] = 0
    return lv


NB = {'ring': [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx], 'shadow': [(1, 0), (0, 1), (1, 1)],
      'shadowR': [(0, 1)], 'plain': []}


def edge_color(r, col, style):
    if style == 'plain': return None
    h, w = r.shape; cnt = collections.Counter()
    for yy, xx in np.argwhere(r == col):
        for dy, dx in NB[style]:
            Y, X = yy + dy, xx + dx
            if 0 <= Y < h and 0 <= X < w and r[Y, X] != col: cnt[int(r[Y, X])] += 1
    return cnt.most_common(1)[0][0] if cnt else None


def inner_colors(r, col, ec):
    f = r == col; p = np.pad(f, 1)
    adj = (np.roll(p, 1, 0) | np.roll(p, -1, 0) | np.roll(p, 1, 1) | np.roll(p, -1, 1))[1:-1, 1:-1]
    out = set()
    for c in set(r.ravel().tolist()) - {col, ec, 0}:
        mk = r == c
        if mk.sum() and (mk & adj).sum() >= 0.8 * mk.sum() and mk.sum() <= f.sum() // 3: out.add(c)
    return out


def apply(A, jobs):
    done = []
    for j in jobs:
        x, y, w, h = j['r']; c = j['c']; style = j.get('s', 'ring'); mode = j.get('e', 'auto')
        tm = j['tm'] if 'tm' in j else A.orig[y:y + h, x:x + w] == c      # tm = 다른 그림에서 딴 본보기 모양
        if 'tm' in j: h, w = tm.shape
        hits = A.find(tm) if j.get('all', True) else [(x, y, c)]
        if not hits and j.get('opt'): continue                               # opt = 없어도 됨(그 장에 없는 문구)
        assert hits, ('사본 없음', j['t'])
        for X, Y, col in hits:
            r = A.orig[Y:Y + h, X:X + w]
            ec = edge_color(r, col, style)
            fills = {col} | inner_colors(r, col, ec)
            f = np.isin(r, list(fills))
            if mode == 'nonbg':
                bg = j['bg'] if 'bg' in j else collections.Counter(r.ravel().tolist()).most_common(1)[0][0]   # bg = 바탕 번호 직접 지정 가능
                m = r != bg
            elif isinstance(mode, (set, frozenset)):         # 이 색들 전부 지움
                m = np.isin(r, list(mode))
                bg = collections.Counter(r[~m].ravel().tolist()).most_common(1)[0][0]
            else:
                p = np.pad(f, 1); near = np.zeros_like(p)
                for dy, dx in NB[style]:
                    near |= np.roll(np.roll(p, dy, 0), dx, 1)
                m = f | (near[1:-1, 1:-1] & (r == ec)) if ec is not None else f
                bg = collections.Counter(r[~m].ravel().tolist()).most_common(1)[0][0]
            for k in j.get('keep', []): m[k] = False
            ramp = None
            if j.get('ramp'):                                   # 줄별 원본 글자 색(그라데이션) — 테두리·바탕 색 빼고 가장 많은 색
                ramp = []
                for yy in range(h):
                    rr = r[yy][m[yy] & (r[yy] != ec)]
                    ramp.append(collections.Counter(rr.tolist()).most_common(1)[0][0] if len(rr) else None)
                known = [v for v in ramp if v is not None] or [col]
                for i in range(h):
                    if ramp[i] is None: ramp[i] = known[min(range(len(known)), key=lambda k: 0)] if not any(ramp[:i]) else next(v for v in reversed(ramp[:i]) if v is not None)
            if j.get('inpaint'):
                A.erase_cells(X, Y, w, h, m)
            elif style == 'ring' and mode == 'auto':  # noqa
                A.erase_mixed(X, Y, w, h, m)
            else:
                A.can[Y:Y + h, X:X + w][m] = bg
            lv = word(j['t'], w, h, j['f'], style, j.get('a', 'c'), j.get('dy', 0))
            A.put(X, Y, lv, ramp if ramp else col, ec if ec is not None else col)
            for k in j.get('keep', []): A.can[Y + k, X:X + w] = r[k]
            done.append((j['t'], X, Y, col, ec))
    return done


def rgb(C, d):
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    e = pal[C]; im = np.stack([(e & 31) << 3, (e >> 5 & 31) << 3, (e >> 10 & 31) << 3], -1).astype(np.uint8)
    im[C == 0] = 40
    return im
