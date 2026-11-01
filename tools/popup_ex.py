# -*- coding: utf-8 -*-
r"""구간 팝업 시트(DR_B?2??.BIN 84장) 한글화(2026-11-01) — 장마다 배치가 달라 «문구 칸 통째 바이트 검색»
  PHR: (본보기 시트, 정확한 칸 x0,y0,x1,y1, 한국어[, 꼴]) — 칸 테두리 1px 에 10% 넘게 나오는 색 = 바탕색들, 나머지 = 글자.
  다른 시트에서 칸 바이트가 똑같은 곳을 찾아 같은 처리(지우기: 바탕 한 색이면 그 색 / 바둑판이면 셀 안 2칸 주기 메움).
  다시 그리기: 테두리 = 바탕과 맞닿은 글자 화소에서 가장 많은 색, 속 = 줄별 «테두리 아닌 글자 색» 최다(그라데이션 유지), 갈무리.
  꼴 = 칸 높이로(≥21 'A' 갈무리7 2배 · ≥14 'B' 갈무리11 Bold · 그 밖 'G9'), 넘치면 한 단계 작게. 숫자·영문·그림은 그대로.
  python tools/popup_ex.py [시트…] → work/gfx/prev_popup_<시트>.png (원본|한글)
"""
import os, sys, glob, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atlas, gfxjob as GJ

DISC = os.path.join(ROOT, 'work', 'disc0')
FILES = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DISC, 'DR_B[1-9A]2??.BIN')))
S = 'DR_B1201'
# (본보기, 칸, 한국어, 바탕 종류 R 빨간 상자·C 바둑판·G 초록 상자·B 파란 상자[, 꼴])
PHR = [
    (S, (0, 0, 164, 15), '열차를 진행시켜 주세요', 'R', 'G11'),
    (S, (166, 0, 312, 15), '정지 위치 앞입니다.', 'R', 'G11'),
    (S, (312, 0, 482, 15), '선행열차가까움', 'R'),
    (S, (406, 16, 498, 31), '경적과다', 'R'),
    (S, (2, 42, 142, 70), 'ATS작동', 'R'),
    (S, (4, 74, 110, 100), '시간초과', 'R'),
    (S, (352, 70, 378, 88), '초', 'C', 'G14B', {'fill': 18, 'ring': 36, 'strict': 1, 'here': 1, 'clear': 1}), (S, (352, 88, 378, 103), '초', 'C', 'G14B', {'fill': 61, 'ring': 54, 'strict': 1, 'here': 1, 'clear': 1}),
    (S, (0, 104, 144, 128), '표지·신호무시', 'R'),
    (S, (280, 104, 362, 120), '출발진행', 'G'),   # 원본 글자 104~118행(게임이 그 범위만 씀 — 103행부터면 위 잘림)
    (S, (368, 104, 512, 119), '역진입속도초과', 'R'),   # 빨간 상자 104행·368열부터(밖은 투명 — 칠하면 게임에서 위가 잘려 보임)
    (S, (368, 119, 418, 136), '제한', 'R'), (S, (476, 119, 512, 136), '까지', 'R'),   # まで 만(Km/h 는 그대로)
    (S, (0, 199, 84, 216), '진행신호', 'C'), (S, (78, 191, 164, 207), '주의신호', 'C'), (S, (158, 199, 246, 216), '정지신호', 'C'),
    (S, (230, 191, 316, 207), '서행예고', 'C'), (S, (328, 191, 392, 207), '서행', 'C'), (S, (392, 191, 490, 207), '서행해제', 'C'),
    (S, (0, 255, 82, 272), '속도제한', 'C'), (S, (80, 255, 164, 272), '속도제한', 'C'), (S, (88, 272, 152, 289), '해제', 'C'),
    (S, (2, 443, 136, 461), '급브레이크', 'R'), (S, (2, 465, 136, 484), '정차역통과', 'R'),
    (S, (146, 443, 286, 461), '제한속도초과', 'R'), (S, (146, 465, 286, 484), '알림등무시', 'R'),
    (S, (290, 442, 430, 486), '일시정지', 'B', 'G14B'),   # 파란 상자(288~431×440~487) 가운데
    (S, (0, 488, 104, 504), '운전계속?', 'C'), (S, (104, 488, 210, 504), '운전중지', 'C'),
    (S, (210, 488, 308, 504), '운전종료', 'C'), (S, (308, 488, 420, 504), '운전재개', 'C'),   # 원본 488행부터(위는 일시정지 상자)
    (S, (78, 205, 106, 223), '속도', 'C', 'G9'), (S, (318, 205, 346, 223), '속도', 'C', 'G9'), (S, (0, 271, 26, 289), '속도', 'C', 'G9'),
    (S, (0, 343, 82, 368), '평지', 'C', 'G14B'),
    (S, (144, 40, 228, 56), '보너스', ('F', {0x3A})), (S, (148, 56, 224, 72), '감점', ('F', {0x34})),
    ('DR_B2205', (318, 200, 402, 225), '오르막', 'C', 'G14B'),
    ('DR_B8207', (318, 200, 402, 222), '내리막', 'C', 'G14B'),
    ('DR_B2205', (240, 366, 402, 386), '비상브레이크 써라', ('F', 'R')),
    ('DR_B8207', (242, 264, 348, 288), '차막이충돌', ('F', 'Y')),   # 원본 ！(353~355열)는 그대로
    ('DR_B2203', (158, 269, 242, 289), '경적울려', 'C'),
    ('DR_B4201', (0, 263, 80, 283), '경적울려', 'C'),   # 산인본선 판(X 표지 아래, 다른 자리·모양) — 하스피 스샷
    (S, (448, 61, 479, 76), '알림등', ('F', {0x23}), 'G9'), (S, (480, 61, 511, 76), '알림등', ('F', {0x23}), 'G9'),
    ('DR_B9200', (340, 176, 444, 189), '승차권을', 'M', 'G11'), ('DR_B9200', (340, 189, 444, 203), '사 주세요', 'M', 'G11'),
    ('DR_B9200', (340, 216, 440, 231), '운전종료', 'M'),
]
HUE = {'R': (31, 0, 0), 'Y': (31, 31, 0)}


def fill_by_hue(sheet, box, hue):
    """본보기 칸 안 20화소 넘는 색 중 hue 에 가장 가까운 번호"""
    d0 = open(os.path.join(DISC, sheet + '.BIN'), 'rb').read(); A0 = atlas.Atlas(d0)
    pal0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int); x0, y0, x1, y1 = box
    cnt = collections.Counter(A0.orig[y0:y1, x0:x1].ravel().tolist()); tr, tg, tb = HUE[hue]
    return {min((c for c, n in cnt.items() if n >= 20), key=lambda c: ((pal0[c] & 31) - tr) ** 2 + ((pal0[c] >> 5 & 31) - tg) ** 2 + ((pal0[c] >> 10 & 31) - tb) ** 2)}
BGK = {'R': {0x12}, 'C': {0x0, 0x1}, 'G': {0x3D}, 'B': {0x47}, 'M': None}      # M = 칸에서 가장 많은 색 한 가지


def quant(rgb):
    """RGB555 → 채널마다 >>2(8단계) 묶음 — 시트마다 한두 단계 다른 같은 색(0x3FF/0x3DF)을 같게"""
    return ((rgb & 31) >> 2) | (((rgb >> 5 & 31) >> 2) << 3) | (((rgb >> 10 & 31) >> 2) << 6)


def analyse(C, pal, box, kind):
    """바탕 = 종류별 색 · 그 밖 밝은 색(밝기 합 > 20, 3화소 이상) = 글자 속 · 속에 붙은 가장 어두운 비바탕 색(바둑판은 1 허용) = 테두리"""
    x0, y0, x1, y1 = box; reg = C[y0:y1, x0:x1]
    cnt = collections.Counter(reg.ravel().tolist())
    lum = lambda c: (pal[c] & 31) + (pal[c] >> 5 & 31) + (pal[c] >> 10 & 31)
    if isinstance(kind, tuple) and kind[0] == 'K':                           # 이 시트 팔레트로 옮긴 바탕 종류
        kind = kind[1]; bgc = BGK_T[kind] if BGK_T.get(kind) is not None else {cnt.most_common(1)[0][0]}
        fills = {c for c, n in cnt.items() if c not in bgc and n >= 3 and lum(c) > 20}
    elif isinstance(kind, tuple):                                            # ('F', 속 색들) — 불꽃 그림 위 글자
        blk_i = min(cnt, key=lambda c: lum(c)); fills = set(kind[1]); bgc = set(cnt) - fills - {blk_i}; kind = 'C'
    else:
        bgc = BGK[kind] if BGK[kind] is not None else {cnt.most_common(1)[0][0]}
        fills = {c for c, n in cnt.items() if c not in bgc and n >= 3 and lum(c) > 20}
    f = np.isin(reg, list(fills))
    if not f.any(): return None
    p = np.pad(f, 1); nb = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): nb |= np.roll(np.roll(p, dy, 0), dx, 1)
    near = nb[1:-1, 1:-1] & ~f
    rc = collections.Counter(reg[near].tolist())
    for c in list(rc):
        if c in bgc and not (kind == 'C' and lum(c) < 8): rc.pop(c)             # 바둑판의 검정은 테두리로 허용
    ring = min(rc, key=lambda c: lum(c)) if rc else None
    if ring is not None and lum(ring) > 40: ring = None
    txt = f | (near & (reg == ring)) if ring is not None else f
    if kind != 'C':                                                          # 상자 바탕이면 바탕색 아닌 것 전부(하이라이트·그림자 포함)
        txt = ~np.isin(reg, list(bgc))
    ramp = []
    for yy in range(reg.shape[0]):
        r = reg[yy][f[yy]]
        ramp.append(collections.Counter(r.tolist()).most_common(1)[0][0] if len(r) else None)
    known = [v for v in ramp if v is not None]; last = known[0]
    for i in range(len(ramp)):
        if ramp[i] is None: ramp[i] = last
        else: last = ramp[i]
    q = quant(pal[reg]); qm = collections.Counter(q[f].tolist()).most_common(1)[0][0]
    fm = f & (q == qm)                                                       # 비교용 = 주된 글자색 화소만(칸에 걸친 옆 문구 색 제외)
    return dict(bg=set(bgc) if kind == 'C' else bgc, txt=txt, f=fm, ring=ring, ramp=ramp, kind=kind)


def find_masked(C, blk, m, tol=0.05):
    """blk 의 m(속) 화소가 95% 이상 같은(묶은 색) 자리 — 겹치는 후보는 가장 잘 맞는 것 하나"""
    C = quant(C); blk = quant(blk)
    pts = np.argwhere(m); vals = blk[m]; h, w = blk.shape
    H_, W_ = C.shape[0] - h + 1, C.shape[1] - w + 1
    step = max(1, len(pts) // 60); sp = pts[::step]; sv = vals[::step]
    score = np.zeros((H_, W_), np.int32)
    for (y, x), v in zip(sp, sv): score += (C[y:y + H_, x:x + W_] == v)
    cand = np.argwhere(score >= len(sp) * min(0.85, 0.9 - tol))
    res = []
    for y, x in cand:
        good = np.mean(C[y:y + h, x:x + w][m] == vals)
        if good >= 1 - tol: res.append((good, float(np.mean(C[y:y + h, x:x + w] == blk)), int(x), int(y)))   # 같으면 칸 전체 일치도로
    res.sort(reverse=True); out = []
    for g, g2, x, y in res:
        if all(abs(x - a) >= w // 2 or abs(y - b) >= h // 2 for a, b in out): out.append((x, y))
    return out


def font_for(h, f=None):
    order = ['B2', 'G14B', 'B', 'G9', 'G7']                                    # 2026-11-01 하스피 «저해상도» → 갈무리7 2배(A) 대신 B2·갈무리14
    if f: return [f] + [o for o in order if order.index(o) > order.index(f if f in order else 'B')]
    start = 'B2' if h >= 24 else ('G14B' if h >= 14 else ('B' if h >= 11 else 'G9'))
    return order[order.index(start):]


def apply(A, d, phr):
    done = []; pal_t = np.frombuffer(d[0x40:0x240], '>u2').astype(int); seen = []
    for sheet, box, kr, kind, *f in phr:
        opt = dict(f.pop()) if f and isinstance(f[-1], dict) else {}            # ★복사(PHR 표 원본을 지우면 두 번째 시트부터 옵션이 빠짐)
        strict = here = clear = 0
        if opt:
            p0 = np.frombuffer(open(os.path.join(DISC, sheet + '.BIN'), 'rb').read()[0x40:0x240], '>u2').astype(int)
            idx = lambda c: next((i for i in range(256) if int(pal_t[i]) == int(p0[c])), None)
            strict = opt.pop('strict', 0); here = opt.pop('here', 0); clear = opt.pop('clear', 0); opt = {k: idx(v) for k, v in opt.items()}
            if strict:                                                           # 秒: 칸 전체가 본보기와 70% 넘게 같아야(엉뚱한 자리 오검출 막기)
                A0 = atlas.Atlas(open(os.path.join(DISC, sheet + '.BIN'), 'rb').read()); bx0, by0, bx1, by1 = box
                tq = quant(p0[A0.orig[by0:by1, bx0:bx1]])
        for (X, Y), info, blk in phr_hits(A, sheet, box, kind, pal_t):
            x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
            if opt and 'tq' in dir() and strict and np.mean(quant(pal_t[A.orig[Y:Y + h, X:X + w]]) == tq) < 0.7: continue
            if opt and here and (X, Y) != (x0, y0): continue                                # 秒 = 본보기 자리에서만(산인본선 시트에서 엉뚱한 세 자리에 그려짐)
            if any(t == kr and abs(X - a) < w // 2 and abs(Y - b) < h // 2 for t, a, b in seen): continue   # 같은 문구 겹침 = 한 번만
            seen.append((kr, X, Y))
            reg = A.can[Y:Y + h, X:X + w]; txt = info['txt']
            if clear: txt = A.orig[Y:Y + h, X:X + w] != 0                                    # 秒 칸: 투명 아닌 것 전부(그림자 덩어리까지) 지움
            if info['kind'] != 'C':
                txt = txt & (A.orig[Y:Y + h, X:X + w] != 0)                                 # 투명(0)은 그대로 — 상자 밖을 칠하지 않음
                reg[txt] = next(iter(info['bg']))
            elif not isinstance(kind, tuple) and (lambda o: (o[~txt] == 0).mean() >= 0.9 if (~txt).any() else False)(A.orig[Y:Y + h, X:X + w]):   # 거의 투명 바탕일 때만(검정 1 로 칠하면 검은 상자 — 하스피 «내리막»)
                reg[txt] = 0                                                                 # 투명
            elif isinstance(kind, tuple):                                                  # 불꽃 위 글자 → 글자(+2px) 자리를 주변 화소로 안쪽부터 메움
                o_ = A.orig[Y:Y + h, X:X + w]; v_ = pal_t[o_]; r_, g_, b_ = v_ & 31, v_ >> 5 & 31, v_ >> 10 & 31
                flame = (r_ >= 24) & (g_ < 22) & (b_ < 8) & ~((r_ > 26) & (g_ > 26))         # 빨강~주황 불꽃
                txt = txt | (~flame & (o_ != 0))                                             # 불꽃·투명 아닌 것 = 글자(노랑 단계·초록·테두리 전부)
                mm = txt.copy()
                for _ in range(2):
                    p_ = np.pad(mm, 1); mm = mm | p_[:-2, 1:-1] | p_[2:, 1:-1] | p_[1:-1, :-2] | p_[1:-1, 2:]
                big = np.zeros(A.can.shape, bool); big[Y:Y + h, X:X + w] = mm; C_ = A.can
                def fl_ok(c):                                                                 # 메움 재료 = 불꽃 색·투명만(아래 숫자 노랑 끌어오지 않음)
                    v = int(pal_t[c]); r2, g2, b2 = v & 31, v >> 5 & 31, v >> 10 & 31
                    return c == 0 or (r2 >= 24 and g2 < 22 and b2 < 8)
                left = 0
                while big.any():
                    nxt = big.copy()
                    for yy, xx in zip(*np.nonzero(big)):
                        nb = [C_[y2, x2] for y2, x2 in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1))
                              if 0 <= y2 < C_.shape[0] and 0 <= x2 < C_.shape[1] and not big[y2, x2] and fl_ok(C_[y2, x2])]
                        if nb: C_[yy, xx] = collections.Counter(nb).most_common(1)[0][0]; nxt[yy, xx] = False
                    if (nxt == big).all(): break
                    big = nxt
                C_[big] = 0                                                                   # 못 메운 칸(불꽃 없는 곳) = 투명
            elif (np.isin(A.orig[Y:Y + h, X:X + w], [0, 1]) | txt).mean() < 0.97:
                A.erase_cells(X, Y, w, h, txt)                                               # 그림 위(바둑판 아님) = 셀 안 메움(예전대로)
            else:                                                                          # 바둑판(0/1) 바탕: 홀짝 자리별 원래 값으로 메움(옆 그림 끌어오지 않음)
                ro = A.orig[Y:Y + h, X:X + w]; par = (np.add.outer(np.arange(Y, Y + h), np.arange(X, X + w)) % 2).astype(bool)
                bgm = np.isin(ro, [0, 1])
                v = {}
                for pv in (False, True):
                    cnt = collections.Counter(ro[bgm & (par == pv)].tolist()); v[pv] = cnt.most_common(1)[0][0] if cnt else 0
                fillv = np.where(par, v[True], v[False]).astype(reg.dtype)
                reg[txt] = fillv[txt]
            tm = info['txt'] & (A.orig[Y:Y + h, X:X + w] > 1); ri = np.nonzero(tm.any(1))[0]; rj = np.nonzero(tm.any(0))[0]
            by0, by1, bx0, bx1 = (ri[0], ri[-1] + 1, rj[0], rj[-1] + 1) if len(ri) and not isinstance(kind, tuple) else (0, h, 0, w)   # 불꽃(F) 위 글자는 칸 그대로   # ★원본 글자 범위(게임은 이 범위만 잘라 씀)
            bw, bh = bx1 - bx0, by1 - by0
            for fn in font_for(bh, f[0] if f else None) + ['G9', 'G7']:
                try:
                    lay_, tw_ = GJ.layout(kr, fn); assert tw_ <= bw and max(g.shape[0] for _, _, g in lay_) <= bh   # 글자는 범위 안(테두리 바깥 1px 은 잘림 허용 — 범위 밖으로는 안 나감)
                    lv0 = GJ.word(kr, bw, bh, fn, 'ring'); break
                except AssertionError:
                    continue
            else:
                raise AssertionError(('넘침', kr, bw, bh))
            lv = np.zeros((h, w), np.uint8); lv[by0:by1, bx0:bx1] = lv0
            if opt.get('fill') is not None: info = dict(info, ramp=[opt['fill']] * h, ring=opt.get('ring', info['ring']))
            else:                                                                            # 줄 색 중 주된 글자색과 동떨어진 것(이웃 글자·바탕색) → 주된 색(하스피 «정지신호 노란 줄·알림등무시 빨간 줄»)
                rp = list(info['ramp']); rgb_ = lambda c: np.array([pal_t[c] & 31, pal_t[c] >> 5 & 31, pal_t[c] >> 10 & 31])
                bgs = set(info['bg']) if isinstance(info['bg'], set) else set()
                cand = collections.Counter(c for c in rp if c not in (0, 1) and c not in bgs)       # 투명·검정·바탕은 글자색 후보에서 뺌(하스피 «시간초과 검은색»)
                mc = cand.most_common(1)[0][0] if cand else rp[0]
                rp = [mc if (c in bgs or c in (0, 1) or np.abs(rgb_(c) - rgb_(mc)).sum() > 18) else c for c in rp]
                info = dict(info, ramp=rp)
            if info['ring'] is None: lv[lv == 1] = 0                                    # 테두리 없는 원본 → 테두리 없이
            A.put(X, Y, lv, info['ramp'], info['ring'] if info['ring'] is not None else 0)
            if info['ring'] is not None:                                                     # 획 사이 1px 틈(양옆 또는 위아래가 테두리) → 테두리색(바탕 빨강이 줄처럼 비치지 않게)
                rg = A.can[Y:Y + h, X:X + w]; rc_ = lv == 1; ink_ = lv > 0                     # 새로 그린 테두리만(바둑판 검정과 번호가 같아도)
                p_ = np.pad(rc_, 1); gap = ((p_[1:-1, :-2] & p_[1:-1, 2:]) | (p_[:-2, 1:-1] & p_[2:, 1:-1])) & ~ink_
                inb = np.zeros_like(gap); inb[by0:by1, bx0:bx1] = True
                rg[gap & inb] = info['ring']
            done.append((kr, X, Y))
    return done


_cache = {}


def phr_hits(A, sheet, box, kind, pal_t):
    """본보기 글자 화소의 «실제 색»이 같은 자리 → 그 시트 자기 팔레트로 다시 분석"""
    if isinstance(kind, tuple) and isinstance(kind[1], str): kind = ('F', fill_by_hue(sheet, box, kind[1]))
    k = (sheet, box)
    if k not in _cache:
        d0 = open(os.path.join(DISC, sheet + '.BIN'), 'rb').read(); A0 = atlas.Atlas(d0)
        pal0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int)
        x0, y0, x1, y1 = box; info = analyse(A0.orig, pal0, box, kind)
        _cache[k] = (pal0[A0.orig[y0:y1, x0:x1]], info)
    rgb, info = _cache[k]
    if info is None: return []
    out = []
    for X, Y in find_masked(pal_t[A.orig], rgb, info['f']):              # 속 화소만 비교(바둑판 위상 무관)
        x0, y0, x1, y1 = box
        if kind == 'M' and (X, Y) != (x0, y0): continue                         # M(아케이드 전용) = 본보기 자리만
        kk = kind
        if isinstance(kind, tuple):                                              # 불꽃: 속 색을 이 시트 번호로
            want = {int(pal_t.tolist().index(int(c))) for c in set(rgb[info['txt'] & (rgb != 0x421)].tolist())} if False else None
            fills_rgb = set(pal0_fill(sheet, kind))
            kk = ('F', {i for i in range(256) if int(pal_t[i]) in fills_rgb})
        mk = map_kind(kk, pal_t, sheet)
        if not isinstance(kk, tuple) and BGK_T.get(kind) is not None:            # 바탕 확인: 속 아닌 화소의 40% 이상이 그 종류 바탕색
            reg = A.orig[Y:Y + y1 - y0, X:X + x1 - x0]; bgm = np.isin(reg, list(BGK_T[kind]))
            if bgm[~info['txt']].mean() < 0.4: continue
        inf = analyse(A.orig, pal_t, (X, Y, X + x1 - x0, Y + y1 - y0), mk)
        if inf is not None: out.append(((X, Y), inf, None))
    return out


def pal0_fill(sheet, kind):
    d0 = open(os.path.join(DISC, sheet + '.BIN'), 'rb').read(); pal0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int)
    return [int(pal0[c]) for c in kind[1]]


def map_kind(kind, pal_t, sheet):
    """바탕 종류의 색 번호를 이 시트 팔레트로(본보기 시트 번호 → 색 값 → 이 시트 번호)"""
    if isinstance(kind, tuple): return kind
    if BGK[kind] is None: BGK_T[kind] = None; return ('K', kind)
    d0 = open(os.path.join(DISC, sheet + '.BIN'), 'rb').read(); pal0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int)
    vals = {int(pal0[c]) for c in BGK[kind]}
    BGK_T[kind] = {i for i in range(256) if int(pal_t[i]) in vals}
    return ('K', kind)


BGK_T = {}


KIN = ('DR_B2205', (0, 342, 402, 363))        # 緊急停止 ×5 애니메이션 줄(글자 자리 20px × 20)


def kinkyu(A, d):
    """緊急停止 줄: 글자 자리마다 켜짐(밝은 빨강)/꺼짐(어두운 빨강) 판정 → «긴급정지» 같은 밝기로"""
    pal_t = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    if 'kin' not in _cache:
        d0 = open(os.path.join(DISC, KIN[0] + '.BIN'), 'rb').read(); A0 = atlas.Atlas(d0); p0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int)
        x0, y0, x1, y1 = KIN[1]; rgb = p0[A0.orig[y0:y1, x0:x1]]
        _cache['kin'] = (rgb, np.isin(rgb, [0x000E, 0x001F]))
    rgb, m = _cache['kin']; done = []
    lit_c = [i for i in range(256) if pal_t[i] == 0x001F]; dim_c = [i for i in range(256) if pal_t[i] == 0x000E]
    blk = [i for i in range(256) if pal_t[i] == 0x0421]
    if not lit_c or not dim_c: return done
    for X, Y in find_masked(pal_t[A.orig], rgb, m, tol=0.15):
        for k in range(20):
            cx, cy = X + 20 * k, Y + 2; reg = A.orig[cy:cy + 17, cx:cx + 20]
            nl = np.isin(reg, lit_c).sum(); nd = np.isin(reg, dim_c).sum()
            col = lit_c[0] if nl > nd else dim_c[0]
            mk = np.isin(reg, lit_c + dim_c)
            A.erase_cells(cx, cy, 20, 17, mk)
            lv = GJ.word('긴급정지'[k % 4], 20, 17, 'B', 'ring')
            A.put(cx, cy, lv, col, blk[0] if blk else col)
        done.append(('긴급정지', X, Y))
    return done


ZEN = ('DR_B8207', (236, 218, 406, 251))      # 全区間走破 금속 글자(아래 ALL ROUND CLEAR 제외)


def zenkukan(A, d):
    """全区間走破 → «전구간완주»: 갈무리11 Bold 2.2배, 줄별 원본 금속 회색, 검정 1px + 빨강 1px 테두리"""
    pal_t = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    lum = lambda c: (pal_t[c] & 31) + (pal_t[c] >> 5 & 31) + (pal_t[c] >> 10 & 31)
    if 'zen' not in _cache:
        d0 = open(os.path.join(DISC, ZEN[0] + '.BIN'), 'rb').read(); A0 = atlas.Atlas(d0); p0 = np.frombuffer(d0[0x40:0x240], '>u2').astype(int)
        x0, y0, x1, y1 = ZEN[1]; rgb = p0[A0.orig[y0:y1, x0:x1]]
        r_, g_, b_ = rgb & 31, rgb >> 5 & 31, rgb >> 10 & 31
        metal = (abs(r_ - b_) < 4) & (abs(r_ - g_) < 4) & (r_ + g_ + b_ > 24) & (rgb != 0x7FFF)
        metal[:4] = False                                                        # 위 4줄은 옆 그림이 걸침
        _cache['zen'] = (rgb, metal)                                             # 비교 = 금속 회색 화소만
    rgb, m = _cache['zen']; done = []
    gray = lambda c: abs((pal_t[c] & 31) - (pal_t[c] >> 10 & 31)) < 4 and abs((pal_t[c] & 31) - (pal_t[c] >> 5 & 31)) < 4 and 8 < lum(c) < 93
    for X, Y in find_masked(pal_t[A.orig], rgb, m, tol=0.2):
        h, w = rgb.shape; reg = A.orig[Y:Y + h, X:X + w].copy()
        bgm = np.isin(pal_t[reg], [0x7000, 0x7FFF])
        ramp = []
        for yy in range(h):
            g = [c for c in reg[yy].tolist() if gray(c)]
            ramp.append(collections.Counter(g).most_common(1)[0][0] if g else None)
        last = next(v for v in ramp if v is not None)
        for i in range(h):
            if ramp[i] is None: ramp[i] = last
            else: last = ramp[i]
        red = collections.Counter(c for c in reg.ravel().tolist() if pal_t[c] == 0x001F).most_common(1)
        blk = collections.Counter(c for c in reg.ravel().tolist() if pal_t[c] == 0x0421).most_common(1)
        par = (np.add.outer(np.arange(Y, Y + h), np.arange(X, X + w)) % 2).astype(bool)   # 파란 판 무늬(홀짝)로 메움 — 셀 메움은 회색 네모가 남음(하스피)
        pv = {}
        for q in (False, True):
            c_ = collections.Counter(reg[bgm & (par == q)].tolist()); pv[q] = c_.most_common(1)[0][0] if c_ else 0
        panel_rows = np.nonzero(bgm.mean(1) > 0.2)[0]
        er = np.zeros((h, w), bool)
        if len(panel_rows): er[panel_rows[0]:, :] = ~bgm[panel_rows[0]:, :]
        cvp = A.can[Y:Y + h, X:X + w]; cvp[er] = np.where(par, pv[True], pv[False])[er]
        for yy in (Y + h, Y + h + 1):                                                    # 칸 바로 아래 2줄의 원래 글자 끄트머리(금속·검정·잔점) → 판 무늬(하스피 «주 오른쪽 밑 찌꺼기»)
            for xx in range(X, X + w):
                if pal_t[A.can[yy, xx]] not in (0x7000, 0x7FFF): A.can[yy, xx] = pv[bool((yy + xx) % 2)]
        # 아래 2줄(그림자 빨강 끝): ALL ROUND CLEAR 글자색과 그에 붙은 화소는 남기고 나머지 비바탕 지움
        lo = A.orig[Y + h:Y + h + 2, X:X + w]; lp = pal_t[lo]
        arc = np.isin(lp, [0x023F, 0x02FF, 0x019F, 0x341F]) | (((lp & 31) > 20) & ((lp >> 5 & 31) > 10))
        p = np.pad(arc, 1); near = np.zeros_like(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): near |= np.roll(np.roll(p, dy, 0), dx, 1)
        near = near[1:-1, 1:-1]
        lm = ~np.isin(lp, [0x7000, 0x7FFF]) & ~near
        if lm.any(): A.erase_cells(X, Y + h, w, 2, lm)
        import pixfont as PF
        gs = [np.kron(PF.cell(ch, 11, bold=True), np.ones((1, 1))) for ch in '전구간완주']
        mrows = np.nonzero(np.array([sum(1 for c in reg[yy].tolist() if gray(c)) for yy in range(h)]) > 2)[0]   # ★원본 금속 글자 행 범위(게임은 파란 판 안만 씀 — 위로 나가면 잘림, 하스피)
        top, bot = (mrows[0], mrows[-1]) if len(mrows) else (0, h - 1)
        avail = bot - top + 1 - 2                                                       # 바깥 테두리 2px(검정+빨강) 몫 빼고
        for sc in (2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5):
            out = []
            for g in gs:
                H2, W2 = int(round(g.shape[0] * sc)), int(round(g.shape[1] * sc))
                yi = (np.arange(H2) / sc).astype(int); xi = (np.arange(W2) / sc).astype(int); out.append(g[yi][:, xi] > 0)
            gh = max(g.shape[0] for g in out)
            if gh <= avail: break
        gap = 4; total = sum(g.shape[1] for g in out) + gap * (len(out) - 1)
        ink = np.zeros((h, w), bool); x = (w - total) // 2; yy0 = top + 1 + (avail - gh) // 2
        for g in out:
            ink[yy0:yy0 + g.shape[0], x:x + g.shape[1]] |= g; x += g.shape[1] + gap
        def dil(b):
            p = np.pad(b, 1); r = np.zeros_like(p)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1): r |= np.roll(np.roll(p, dy, 0), dx, 1)
            return r[1:-1, 1:-1]
        r1 = dil(ink) & ~ink; r2 = dil(ink | r1) & ~(ink | r1)
        cv = A.can[Y:Y + h, X:X + w]
        if red: cv[r2] = red[0][0]
        if blk: cv[r1] = blk[0][0]
        for yy in range(h): cv[yy][ink[yy]] = ramp[yy]
        # 글자 아래 줄(새 테두리 밖)의 원래 빨간 그림자 잔재 → 2줄 위·아래 같은 열의 바둑판 바탕색으로(하스피: 밑에 노이즈)
        mine = ink | r1 | r2; cvb = A.can; bgv = [i for i in range(256) if pal_t[i] in (0x7000, 0x7FFF)]
        for yy in range(Y + h - 6, min(Y + h + 3, cvb.shape[0])):
            for xx in range(X, X + w):
                v = int(pal_t[cvb[yy, xx]]); reddish = (v & 31) > 12 and (v >> 5 & 31) < 8 and (v >> 10 & 31) < 8
                if not reddish or (yy < Y + h and mine[yy - Y, xx - X]): continue
                for alt in (yy - 2, yy + 2, yy - 4, yy + 4, yy - 6, yy + 6, yy - 8):
                    if 0 <= alt < cvb.shape[0] and cvb[alt, xx] in bgv and not (Y <= alt < Y + h and mine[alt - Y, xx - X]):
                        cvb[yy, xx] = cvb[alt, xx]; break
        done.append(('전구간완주', X, Y))
    return done


ARC_LINES = [   # 아케이드 보조 시트 말풍선(guide_ex.draw_lines 형식)
    (268, 280, 6, 206, 'G11', '{b:속도 60km/h}쯤까지'), (281, 292, 6, 206, 'G11', '{r:가속}합니다.'),
    (269, 280, 214, 414, 'G11', '속도가 붙으면 {r:마스콘을}'), (281, 292, 214, 414, 'G11', '{r:끕니다.} 이것이 {b:타력주행}입니다.'),
    (300, 312, 8, 188, 'G11', '브레이크를 잘 써서'), (313, 324, 7, 188, 'G11', '{r:정지위치에 정차!}'),
]


def arcade(A, d, sheet):
    if sheet not in ('DR_B9200', 'DR_B9201', 'DR_BA200', 'DR_BA201'): return []
    import guide_ex
    bg = collections.Counter(A.orig[262:292, 20:180].ravel().tolist()).most_common(1)[0][0]
    guide_ex.draw_lines(A, d, ARC_LINES, bg)
    return [('말풍선', 0, 0)] * len(ARC_LINES)


def build(sheet):
    import stn_ex
    d = open(os.path.join(DISC, sheet + '.BIN'), 'rb').read(); A = atlas.Atlas(d)
    done = apply(A, d, PHR) + stn_ex.apply(A, d, sheet) + kinkyu(A, d) + zenkukan(A, d) + arcade(A, d, sheet); new = A.save()
    return d, A, done, new


def survey():
    """84장 × 문구 → 찾은 수 표"""
    import collections as _c
    tab = _c.defaultdict(dict)
    for sh in FILES:
        d = open(os.path.join(DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal_t = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        for i, (sheet, box, kr, kind, *f) in enumerate(PHR):
            tab[i][sh] = len(phr_hits(A, sheet, box, kind, pal_t))
    for i, ph in enumerate(PHR):
        v = tab[i]; z = [k for k, n in v.items() if n == 0]
        print('%-14s 찾음 %2d장  없음 %2d장 %s' % (ph[2], sum(1 for n in v.values() if n), len(z), ' '.join(z[:6])))


def build_all():
    """84장 전부 → work/build/popup/<시트>.BIN + 결과 모음(work/gfx/prev_popup_all_N.png)"""
    od = os.path.join(ROOT, 'work', 'build', 'popup'); os.makedirs(od, exist_ok=True)
    thumbs = []; bad = []
    for sh in FILES:
        d, A, done, new = build(sh)
        if A.added: bad.append((sh, A.added))
        open(os.path.join(od, sh + '.BIN'), 'wb').write(new)
        B = atlas.Atlas(new); assert np.array_equal(B.can, A.can), sh
        thumbs.append((sh, len(done), GJ.rgb(A.can, d)))
        print(sh, len(done), A.added, len(new) - len(d))
    from PIL import ImageDraw
    for part in range(0, len(thumbs), 12):
        grp = thumbs[part:part + 12]; cv = Image.new('RGB', (4 * 516, 3 * 528), (255, 255, 255)); dr = ImageDraw.Draw(cv)
        for i, (sh, n, im) in enumerate(grp):
            x, y = (i % 4) * 516, (i // 4) * 528
            cv.paste(Image.fromarray(im), (x, y + 14)); dr.text((x + 2, y + 1), '%s (%d)' % (sh, n), fill=(255, 0, 0))
        cv.save(os.path.join(ROOT, 'work', 'gfx', 'v4', 'prev_popup_all_%d.png' % (part // 12)))
    print('새 셀 생긴 시트', bad)


if __name__ == '__main__' and sys.argv[1:] == ['all']:
    build_all(); sys.exit()


if __name__ == '__main__' and sys.argv[1:] == ['survey']:
    survey(); sys.exit()
if __name__ == '__main__':
    for sheet in (sys.argv[1:] or ['DR_B1201', 'DR_B2205', 'DR_B8207', 'DR_B3207']):
        d, A, done, new = build(sheet)
        print(sheet, '바꾼 곳', len(done), '새 셀', A.added)
        a = GJ.rgb(A.orig, d); b = GJ.rgb(A.can, d)
        sh = np.concatenate([a, np.full((a.shape[0], 4, 3), 255, np.uint8), b], 1)
        p = os.path.join(ROOT, 'work', 'gfx', 'prev_popup_%s.png' % sheet)
        Image.fromarray(sh).save(p); print(p)
