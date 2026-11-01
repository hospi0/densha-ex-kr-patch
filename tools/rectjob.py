# -*- coding: utf-8 -*-
r"""칸 단위 문구 바꾸기 공용(2026-11-01, popup_ex 방식을 아무 그림에나) — tools/atlas.py 위에서
  작업 = dict(r=(x0,y0,x1,y1), t=한국어, k=바탕('T' 투명 0 · 'M' 칸에서 가장 많은 색 · 번호 직접), f=꼴(없으면 높이로),
              ink=True(흰 바탕 한 색 글자 — 테두리 없음), s=둘레('auto' 테두리 있으면 ring · 'shadow' 오른쪽 아래), a=맞춤, all=같은 그림 안 사본도(주된 글자색 모양 검색), keep=[행…])
  글자 = 칸 안 바탕 아닌 화소 전부 · 테두리 = 바탕과 맞닿은 글자 화소의 가장 어두운 색 · 속 = 줄별 «테두리 아닌» 최다 색(그라데이션)
  지우기 = 바탕 한 색으로 · 그리기 = 갈무리(넘치면 한 단계 작게)
"""
import collections
import numpy as np
import gfxjob as GJ


def lum(pal, c):
    v = int(pal[c]); return (v & 31) + (v >> 5 & 31) + (v >> 10 & 31)


def analyse(C, pal, box, k):
    x0, y0, x1, y1 = box; reg = C[y0:y1, x0:x1]
    cnt = collections.Counter(reg.ravel().tolist())
    if isinstance(k, tuple):                                                  # ('F', 속 색들) — 그림(불꽃) 위 글자: 속 + 붙은 어두운 테두리만
        f = np.isin(reg, list(k[1])); p = np.pad(f, 1); nb = np.zeros_like(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): nb |= np.roll(np.roll(p, dy, 0), dx, 1)
        near = nb[1:-1, 1:-1] & ~f
        rc = collections.Counter(reg[near].tolist()); dark = [c for c in rc if lum(pal, c) < 30]
        ring = max(dark, key=lambda c: rc[c]) if dark else None
        txt = f | (near & (reg == ring)) if ring is not None else f
        ramp = []
        for yy in range(reg.shape[0]):
            r = reg[yy][f[yy]]; ramp.append(collections.Counter(r.tolist()).most_common(1)[0][0] if len(r) else None)
        known = [v for v in ramp if v is not None]; last = known[0]
        for i in range(len(ramp)):
            if ramp[i] is None: ramp[i] = last
            else: last = ramp[i]
        return dict(bg=None, txt=txt, ring=ring, ramp=ramp, main=known[0])
    per = np.concatenate([reg[0], reg[-1], reg[:, 0], reg[:, -1]])          # M = 칸 둘레 1px 최다 색(글자 빽빽해도 바탕)
    bg = 0 if k == 'T' else (collections.Counter(per.tolist()).most_common(1)[0][0] if k == 'M' else int(k))
    txt = reg != bg
    if not txt.any(): return None
    p = np.pad(~txt, 1); nb = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): nb |= np.roll(np.roll(p, dy, 0), dx, 1)
    edge = txt & nb[1:-1, 1:-1]
    ec = collections.Counter(reg[edge].tolist())
    dark = [c for c in ec if lum(pal, c) < 30]
    ring = max(dark, key=lambda c: ec[c]) if dark else None
    ramp = []
    for yy in range(reg.shape[0]):
        r = reg[yy][txt[yy] & (reg[yy] != ring)]
        ramp.append(collections.Counter(r.tolist()).most_common(1)[0][0] if len(r) else None)
    known = [v for v in ramp if v is not None]
    if not known:                                                             # 글자가 한 색(어두운 색)뿐 → 테두리 없음, 그 색으로
        c = collections.Counter(reg[txt].tolist()).most_common(1)[0][0]
        return dict(bg=bg, txt=txt, ring=None, ramp=[c] * reg.shape[0], main=c)
    last = known[0]
    for i in range(len(ramp)):
        if ramp[i] is None: ramp[i] = last
        else: last = ramp[i]
    main = collections.Counter(reg[txt & (reg != ring)].tolist()).most_common(1)[0][0]
    return dict(bg=bg, txt=txt, ring=ring, ramp=ramp, main=main)


def font_for(h):
    start = 'B3' if h >= 34 else 'A' if h >= 20 else 'G14' if h >= 16 else ('B' if h >= 13 else ('G9' if h >= 10 else 'G7'))
    order = ['B3', 'A', 'G14', 'B', 'G11', 'G9', 'G7']
    return order[order.index(start):]


def apply(A, d, jobs):
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int); done = []
    for j in jobs:
        x0, y0, x1, y1 = j['r']; w, h = x1 - x0, y1 - y0
        info = analyse(A.orig, pal, j['r'], j.get('k', 'T'))
        assert info, ('글자 없음', j['t'], j['r'])
        spots = [(x0, y0, info)]
        if j.get('all'):
            tm = A.orig[y0:y1, x0:x1] == info['main']
            for X, Y, col in A.find(tm):
                if (X, Y) == (x0, y0): continue
                inf = analyse(A.orig, pal, (X, Y, X + w, Y + h), j.get('k', 'T'))
                if inf: spots.append((X, Y, inf))
        if j.get('ink'):                                                    # 흰 바탕 검은 글자(통지표) — 테두리 없이 한 색
            for X, Y, inf in spots:
                ic = collections.Counter(A.orig[Y:Y + h, X:X + w][inf['txt']].tolist()).most_common(1)[0][0] if j['ink'] is True else j['ink']
                inf.update(ring=None, ramp=[ic] * h, main=ic)
        if j.get('minlum'):                                                 # 그라데이션 글자 — 줄별 색은 밝은 색만(어두운 그림자 줄 막기)
            for X, Y, inf in spots:
                o = A.orig[Y:Y + h, X:X + w]; rp = []
                rows = [[c for c in o[yy][inf['txt'][yy]].tolist() if lum(pal, c) >= j['minlum']] for yy in range(h)]
                full = max(len(r) for r in rows) if rows else 0
                for r in rows:                                                   # dense: 획이 적은 줄(위아래 끝·탁점)은 버리고 이웃 줄 색
                    ok = r and (not j.get('dense') or len(r) >= 0.35 * full)
                    rp.append(collections.Counter(r).most_common(1)[0][0] if ok else None)
                kn = [v for v in rp if v is not None]
                if not kn: continue                                              # 밝은 색 없음 → 원래 줄 색 그대로
                last = kn[0]
                for i in range(h):
                    if rp[i] is None: rp[i] = last
                    else: last = rp[i]
                inf['ramp'] = rp
        if j.get('fill') is not None:                                                     # 속 한 색(타일 공유 늘리기)
            for X, Y, inf in spots: inf['ramp'] = list(j['fill']) if isinstance(j['fill'], (list, tuple)) else [j['fill']] * h
        if 'rc' in j:                                                       # 테두리·그림자 색 직접
            for X, Y, inf in spots: inf['ring'] = j['rc']
        for X, Y, inf in spots:
            reg = A.can[Y:Y + h, X:X + w]; m = inf['txt'].copy()
            for kk in j.get('keep', []): m[kk] = False
            if inf['bg'] is None and j.get('inpaint'):                          # 그림 위 글자 = 이웃 화소로 안쪽부터 메움(바깥 1px 넓혀)
                mm = m.copy()
                for _ in range(int(j['inpaint'])):                                  # inpaint=N → N px 넓혀 메움
                    p_ = np.pad(mm, 1); mm = mm | p_[:-2, 1:-1] | p_[2:, 1:-1] | p_[1:-1, :-2] | p_[1:-1, 2:]
                big = np.zeros(A.can.shape, bool); big[Y:Y + h, X:X + w] = mm
                while big.any():
                    nxt = big.copy(); C_ = A.can
                    for yy, xx in zip(*np.nonzero(big)):
                        nb = [C_[y2, x2] for y2, x2 in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1))
                              if 0 <= y2 < C_.shape[0] and 0 <= x2 < C_.shape[1] and not big[y2, x2]]
                        if nb: C_[yy, xx] = collections.Counter(nb).most_common(1)[0][0]; nxt[yy, xx] = False
                    if (nxt == big).all(): break
                    big = nxt
            elif inf['bg'] is None: A.erase_cells(X, Y, w, h, m)                   # 그림 위 글자 = 셀 안 메움
            else: reg[m] = inf['bg']
            style = j.get('s', 'auto')
            if style == 'auto': style = 'ring' if inf['ring'] is not None else 'plain'
            for fn in ([j['f']] if j.get('f') else []) + font_for(h):
                try:
                    lv = GJ.word(j['t'], w, h, fn, style, j.get('a', 'c'), j.get('dy', 0)); break
                except AssertionError:
                    continue
            else:
                raise AssertionError(('넘침', j['t'], w, h))
            if inf['ring'] is None: lv[lv == 1] = 0
            if j.get('stretch'):                                               # 원본 글자 세로 범위의 색 줄을 새 글자 높이에 맞춰 늘이고 줄임(무지개)
                orow = np.nonzero(inf['txt'].any(1))[0]; nrow = np.nonzero((lv > 0).any(1))[0]
                o0, o1, n0, n1 = orow[0], orow[-1], nrow[0], nrow[-1]; rp = list(inf['ramp'])
                inf['ramp'] = [rp[min(o1, max(o0, o0 + round((yy - n0) * (o1 - o0) / max(1, n1 - n0))))] for yy in range(h)]
                if j.get('smooth'):                                               # 이웃 줄보다 확 어두운 줄(가로 노이즈) → 위 줄 색
                    rr = inf['ramp']
                    for _ in range(2):
                        for i in range(1, h - 1):
                            if lum(pal, rr[i]) < 0.8 * min(lum(pal, rr[i - 1]), lum(pal, rr[i + 1])): rr[i] = rr[i - 1]   # 양옆보다 어두운 외톨이 줄만
            A.put(X, Y, lv, inf['ramp'], inf['ring'] if inf['ring'] is not None else 0)
            done.append((j['t'], X, Y))
    return done
