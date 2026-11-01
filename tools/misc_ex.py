# -*- coding: utf-8 -*-
r"""운전 중 보조 그림 한글화(2026-11-01) — DR_TUUTI(운전 평가 통지표)·DR_JIKO(사고)·DR_START(발차 안내)·DR_WARP(역 이름) — tools/rectjob.py
  python tools/misc_ex.py → work/gfx/prev_<이름>.png
"""
import os, sys, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ, rectjob as RJ

DISC = os.path.join(ROOT, 'work', 'disc0')
JOBS = {
    'DR_TUUTI': [
        dict(r=(92, 0, 230, 17), t='운전평가', k=2, ink=True, f='G14BB'),
        dict(r=(22, 20, 204, 36), t='역행·타행 사용법', k=2, ink=True, f='G14B', a='l'), dict(r=(22, 40, 204, 56), t='브레이크 사용법', k=2, ink=True, f='G14B', a='l'),
        dict(r=(22, 60, 204, 76), t='정지위치 정확성', k=2, ink=True, f='G14B', a='l'), dict(r=(22, 80, 204, 96), t='신호·표지 준수', k=2, ink=True, f='G14B', a='l'),
        dict(r=(100, 99, 190, 119), t='종합평가', k=2, ink=True, f='G14BB'), dict(r=(268, 99, 304, 119), t='점', k=2, ink=True, f='G14BB'),
    ],
    'DR_JIKO': [
        dict(r=(0, 32, 80, 48), t='보 너 스', k=('F', None), hue='G', f='G14B', inpaint=2), dict(r=(0, 48, 80, 64), t='감  점', k=('F', None), hue='Y', f='G14B', inpaint=2),
        dict(r=(230, 70, 282, 108), t='사', k=20, f='B3'), dict(r=(294, 70, 348, 108), t='고', k=20, f='B3'),
        dict(r=(230, 136, 282, 174), t='사', k=20, f='B3'), dict(r=(294, 136, 348, 174), t='고', k=20, f='B3'),
        dict(r=(226, 109, 350, 125), t='브레이크 지연', k=20), dict(r=(226, 174, 350, 190), t='과속', k=20),
        dict(r=(0, 118, 152, 138), t='위험회피합격!', k='T'),
        dict(r=(239, 0, 265, 16), t='초', k='T', f='G14W', s='ring'), dict(r=(239, 16, 265, 32), t='초', k='T', f='G14W', s='ring'),   # 숫자 줄 끝 秒
    ],
    'DR_START': [],
    'DR_WARP': [dict(r=(0, 16, 62, 31), t='탄바구치', k='M', a='l'), dict(r=(0, 32, 80, 47), t='사가아라시야마', k='M', a='l')],
}
HUE = {'G': (0, 31, 0), 'Y': (31, 31, 0)}


def resolve(d, A, jobs):
    """k=('F', None)+hue → 칸 안 20화소 넘는 색 중 hue 에 가장 가까운 번호"""
    import collections
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int); out = []
    for j in jobs:
        if isinstance(j.get('k'), tuple) and j['k'][1] is None:
            x0, y0, x1, y1 = j['r']; cnt = collections.Counter(A.orig[y0:y1, x0:x1].ravel().tolist()); tr, tg, tb = HUE[j['hue']]
            c = min((c for c, n in cnt.items() if n >= 20), key=lambda c: ((pal[c] & 31) - tr) ** 2 + ((pal[c] >> 5 & 31) - tg) ** 2 + ((pal[c] >> 10 & 31) - tb) ** 2)
            j = dict(j, k=('F', {c}))
        out.append(j)
    return out


STAMPS = ((0, '수'), (32, '우'), (64, '미'), (96, '양'))    # 통지표 도장 優·良·可·努 → 학교 성적 수우미양(위에서부터)


def stamps(A):
    """도장 = 바탕 0 위 빨간 타원(1px) 안 한자 → 타원만 남기고 속 지운 뒤 갈무리14 굵게 빨강"""
    y0, y1 = 120, 140
    for x0, t in STAMPS:
        reg = A.can[y0:y1, x0:x0 + 27]; o = A.orig[y0:y1, x0:x0 + 27] != 0
        rs = np.zeros_like(o); cs = np.zeros_like(o)
        for y in range(o.shape[0]):
            xs = np.nonzero(o[y])[0]
            if len(xs): rs[y, xs[0]:xs[-1] + 1] = True
        for x in range(o.shape[1]):
            ys = np.nonzero(o[:, x])[0]
            if len(ys): cs[ys[0]:ys[-1] + 1, x] = True
        inside = np.pad(rs & cs, 1); inn = inside.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): inn &= np.roll(np.roll(inside, dy, 0), dx, 1)
        inn = inn[1:-1, 1:-1]
        reg[inn] = 0; reg[~np.isin(reg, (0, 1, 11, 12))] = 0                  # 원에 붙은 분홍 잔점
        lv = GJ.word(t, 21, 16, 'G14B', 'plain')
        sub = A.can[y0 + 2:y0 + 18, x0 + 3:x0 + 24]; sub[(lv > 0) & inn[2:18, 3:24]] = 12


JIKO_LINES = [   # 사고 그림 말풍선 — 002 말풍선(bubble_ex, 하스피 통과)과 같은 문구·꼴 G9·검정 한 색·그림자 없음 (y0, y1, x0, 문장 — {}=빨강)
    (163, 173, 10, '건널목 무리한 횡단은'), (177, 187, 10, '매우 {위험}합니다.'), (191, 201, 10, '안전 확인, 일단 정지!'),
]


JIKO_LOGO = (128, 193)


def jiko_bubble(A, d, bg=10):
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int); C = A.can; o = A.orig
    reg = o[160:204, 4:126]; cols = [c for c in set(reg.ravel().tolist()) if c not in (bg, 0)]
    lum = lambda c: (pal[c] & 31) + (pal[c] >> 5 & 31) + (pal[c] >> 10 & 31)
    ink = min(cols, key=lum)
    reds = [c for c in cols if (pal[c] & 31) >= 20 and (pal[c] >> 5 & 31) < 10]
    red = max(reds, key=lambda c: int((reg == c).sum()))
    for y0, y1, x0, t in JIKO_LINES:
        box = C[y0 - 1:y1 + 1, 6:126]; box[(box != bg) & (box != 0)] = bg
    for y0, y1, x0, t in JIKO_LINES:
        plain = t.replace('{', '').replace('}', ''); lay, total = GJ.layout(plain, 'G9')
        assert x0 + total <= 124, ('넘침', t, total)
        flag = []; on = False
        for ch in t:
            if ch == '{': on = True
            elif ch == '}': on = False
            elif ch != ' ': flag.append(on)
        gh = max(g.shape[0] for _, _, g in lay); yy = y0 + (y1 - y0 - gh) // 2
        for n, (ch, gx, g) in enumerate(lay):
            sub = C[yy + gh - g.shape[0]:yy + gh, x0 + gx:x0 + gx + g.shape[1]]; sub[g > 0] = red if flag[n] else ink


def put_logo_any(A, d, X, Y):
    """작은 로고 «電車でGO!» → «전차로GO!» — 팔레트가 다른 시트용(bubble_ex.put_logo 를 색 분류로 일반화).
    X, Y = 002 본보기와 같은 기준(電車で 칸 = x X+4 … X+50, 행 Y+4 … Y+23)"""
    import bubble_ex as BX
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int); C = A.can; o = A.orig
    rgb = lambda c: (pal[c] & 31, pal[c] >> 5 & 31, pal[c] >> 10 & 31)
    warm = {c for c in range(256) if rgb(c)[0] >= 16 and rgb(c)[2] < 12 and c != 0}
    bright = {c for c in warm if rgb(c)[0] >= 24}
    skin = {c for c in range(256) if rgb(c)[0] >= 20 and rgb(c)[1] >= 14 and rgb(c)[2] >= 10}
    x0, x1, y0, y1 = X + 1, X + 50, Y + 4, min(Y + 26, C.shape[0])
    reg = o[y0:y1, x0:x1]; ink = np.isin(reg, list(warm))
    dark = collections.Counter(reg[~ink & (reg != 0)].tolist()); dark = [c for c in dark if sum(rgb(c)) < 15]
    outline = max(dark, key=lambda c: int((reg == c).sum()))
    p_ = np.pad(ink, 1); near = np.zeros_like(p_)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): near |= np.roll(np.roll(p_, dy, 0), dx, 1)
    m = ink | (np.isin(reg, dark) & near[1:-1, 1:-1])
    m |= (np.arange(y0, y1)[:, None] >= Y + 7) & (reg != 0) & ~np.isin(reg, list(skin))   # 손 아래 행은 로고뿐 — 어두운 갈색 잔점까지
    ramp = {}
    for yy in range(y0, y1):
        r = reg[yy - y0][np.isin(reg[yy - y0], list(bright))]
        if len(r): ramp[yy] = collections.Counter(r.tolist()).most_common(1)[0][0]
    C[y0:y1, x0:x1][m] = 0
    top = o[Y + 1:Y + 10, X + 50:X + 55]; C[Y + 1:Y + 10, X + 50:X + 55][np.isin(top, list(warm) + dark + [c for c in range(1, 256) if rgb(c)[2] < 3 and rgb(c)[0] >= 6])] = 0   # で 오른쪽 위 끝 획
    it = BX.logo_glyph(); gh, gw = it.shape
    by = Y + 22 - gh; bx = x1 - gw
    big = np.zeros_like(C, bool); big[by:by + gh, bx:bx + gw] = it
    p_ = np.pad(big, 1); dil = np.zeros_like(p_)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): dil |= np.roll(np.roll(p_, dy, 0), dx, 1)
    ring = dil[1:-1, 1:-1] & ~big
    C[ring & ~np.isin(C, list(skin))] = outline
    keys = sorted(ramp)
    for yy in range(by, by + gh):
        C[yy][big[yy]] = ramp.get(yy) or ramp[min(keys, key=lambda k: abs(k - yy))]


# 발차 안내 판(73×19, 가운데 가로줄 있는 플랩 판) — 빈 판(161,80)을 복사해 깨끗이 한 뒤 흰 글자(갈무리14 굵게)
EMPTY_PLATE = (161, 80)
PLATES = [((3, 80 + 24 * i), t) for i, t in enumerate(('도쿄', '쿄토', '요코하마', '오사카', '시부야', '카메오카'))] +          [((82, 80 + 24 * i), t) for i, t in enumerate(('쾌속', '보통', '키하58계', '209계', '221계', '205계'))] +          [((161, 176), '시나가와'), ((161, 200), '타카츠키')]


def plates(A, white=2):
    reg = A.can[3:18, 66:213]; reg[reg != 33] = 33                                     # 제목 띠 発車案内 → 발차안내(흰 속 + 회색 테두리)
    lv = GJ.word('발 차 안 내', 147, 15, 'G14B', 'ring'); A.put(66, 3, lv, white, 38)
    ex, ey = EMPTY_PLATE; empty = A.orig[ey:ey + 19, ex:ex + 73]
    for (x, y), t in PLATES:
        A.can[y:y + 19, x:x + 73] = empty
        for f in ('G14B', 'G14', 'B'):
            try: lv = GJ.word(t, 65, 16, f, 'plain'); break
            except AssertionError: continue
        sub = A.can[y + 2:y + 18, x + 4:x + 69]; sub[lv > 0] = white


def build(name):
    d = open(os.path.join(DISC, name + '.BIN'), 'rb').read(); A = atlas.Atlas(d)
    done = RJ.apply(A, d, resolve(d, A, JOBS[name]))
    if name == 'DR_TUUTI': stamps(A)
    if name == 'DR_START': plates(A)
    if name == 'DR_JIKO':
        jiko_bubble(A, d); put_logo_any(A, d, *JIKO_LOGO)
    new = A.save()
    return d, A, done, new


if __name__ == '__main__':
    for name in (sys.argv[1:] or list(JOBS)):
        d, A, done, new = build(name); print(name, '바꾼 곳', len(done), '새 셀', A.added)
        ys, xs = np.nonzero(A.orig); H, W = ys.max() + 1, xs.max() + 1
        a = GJ.rgb(A.orig[:H, :W], d); b = GJ.rgb(A.can[:H, :W], d)
        sh = np.concatenate([a, np.full((H, 4, 3), 255, np.uint8), b], 1)
        Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'prev_%s.png' % name))
