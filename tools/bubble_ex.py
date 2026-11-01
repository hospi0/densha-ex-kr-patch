# -*- coding: utf-8 -*-
r"""마스코트 말풍선(DR_B?X00.SZ3 항목 002, 다섯 노선 같음) 한글화(2026-10-31)
  말풍선 7개 = x 0~128, y 8+64k ~ +48. 원본 글자 = 회색 단계 다듬은 검정 → 줄 범위 안 «흰색(0x1A)·바깥(0x00) 아닌 화소» 전부 흰색으로 지우고
  갈무리(2줄 = 11, 3줄 = 9) 가장 진한 검정 0x19 한 색으로, 원본 줄의 왼쪽 x·세로 가운데에 맞춤. {…} = 원본 빨강(危険).
  python tools/bubble_ex.py → work/gfx/prev_bubble.png (원본|한글, 3배)
"""
import os, sys, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import atlas, gfxjob as GJ

SRC = os.path.join(ROOT, 'work', 'x', 'DR_B4X00.SZ3', '002.bin')
WHITE, OUT, INK = 0x1A, 0x00, 0x19
BUBBLES = [   # (꼴, [한국어 줄…]) — 원본 줄 수와 같게
    ('G11', ['정차역은', '지켜 주세요.']),
    ('G11', ['브레이크가', '너무 강합니다.']),
    ('G11', ['신호는', '지켜 주세요.']),
    ('G11', ['전차는 갑자기', '못 섭니다.']),
    ('G11', ['타력주행을', '써 주세요.']),
    ('G9', ['건널목 무리한 횡단은', '매우 {위험}합니다.', '안전 확인, 일단 정지!']),
    ('G9', ['스타트 버튼을', '눌러 주세요.', '(컨티뉴 스타트)']),
]


def lines_of(C, k):
    y0 = 8 + 64 * k; t = ((C[y0:y0 + 48, 0:128] != WHITE) & (C[y0:y0 + 48, 0:128] != OUT))[:, 6:120]
    rows = [r for r in range(4, 44) if t[r].any()]; ls = []; cur = [rows[0]]
    for r in rows[1:]:
        if r - cur[-1] > 1: ls.append(cur); cur = [r]
        else: cur.append(r)
    ls.append(cur); out = []
    for L in ls:
        xs = np.nonzero(t[L[0]:L[-1] + 1].any(0))[0]; out.append((y0 + L[0], y0 + L[-1] + 1, 6 + xs.min(), 6 + xs.max() + 1))
    return out


def red_index(C):
    """6번 말풍선(危険) 안 가장 많은 «검정·흰색 아닌 진한 색»"""
    return 0x0C


def build():
    d = open(SRC, 'rb').read(); A = atlas.Atlas(d); C = A.can
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    reds = [i for i in range(256) if (pal[i] & 31) >= 20 and ((pal[i] >> 5) & 31) < 10 and ((pal[i] >> 10) & 31) < 10]
    for k, (f, texts) in enumerate(BUBBLES):
        ls = lines_of(A.orig, k); assert len(ls) == len(texts), (k, ls)
        reg = A.orig[8 + 64 * k:8 + 64 * k + 48, 0:128]
        red = max(reds, key=lambda i: int((reg == i).sum())) if reds else INK
        for (y0, y1, x0, x1), t in zip(ls, texts):
            box = C[y0:y1, x0 - 1:x1 + 1]; box[(box != WHITE) & (box != OUT)] = WHITE
            plain = t.replace('{', '').replace('}', '')
            lay, total = GJ.layout(plain, f)
            assert x0 + total <= 122, ('넘침', t, total)
            gh = max(g.shape[0] for _, _, g in lay); yy = y0 + (y1 - y0 - gh) // 2
            # 빨강 구간(글자 순번)
            reds_i = set(); i = 0; on = False
            for ch in t:
                if ch == '{': on = True; continue
                if ch == '}': on = False; continue
                if ch != ' ':
                    if on: reds_i.add(i)
                    i += 1
            for n, (ch, gx, g) in enumerate(lay):
                sub = C[yy + gh - g.shape[0]:yy + gh, x0 + gx:x0 + gx + g.shape[1]]
                sub[g[:sub.shape[0], :sub.shape[1]] > 0] = red if n in reds_i else INK
    GJ.apply(A, OTHERS)
    for X, Y in logo_instances(A): put_logo(A, X, Y)
    A.logos = len(logo_instances(A))
    new = A.save()
    return d, A, new


# 오른쪽 글자(작업 목록, tools/gfxjob.py)
OTHERS = [
    dict(r=(233, 19, 22, 13), c=0x9, t='남은', f='G9', s='plain', e='nonbg', all=False),        # あと (빨강 알약, 숫자 칸 왼쪽)
    dict(r=(265, 19, 30, 13), c=0x9, t='코인', f='G9', s='plain', e='nonbg', all=False),        # コイン
    dict(r=(224, 63, 80, 17), c=0x1B, t='승무완료', f='AB', s='plain'),                          # 乗務完了 (두 벌)
    dict(r=(224, 145, 82, 13), c=0x16, t='남은시간주의!', f='G9', s='ring', e='nonbg', all=False),  # 持ち時間注意!
]


# ── 작은 로고 «電車でGO!» → «전차로GO!» (2026-10-31 하스피: 작은 로고 바꿔) — PS1 판 logo_kr.small_logo 방식
LOGO_INK = {0x16, 0x15, 0x13, 0x12, 0x0F, 0x09, 0x08, 0x24, 0x0A, 0x2E, 0x2D, 0x2C, 0x2B, 0x25, 0x27, 0x14, 0x11, 0x0E}   # 로고 노랑~빨강·갈색
OUTLINE = 0x19
BRIGHT = {0x16, 0x13, 0x09}                                   # 전차로 줄 색 후보(노랑 0x33F·주황 0x239·빨강 0xDF)
GO_REL = (52, 7, 31, 16)          # 본보기 GO! 칸(로고 왼쪽 x 기준 상대: x+52 … ) — 사본 찾기용
LOGO0 = (124, 40)                 # 본보기 로고 왼쪽 위(전차로 칸 x 128~176, 행 44~63)


def logo_instances(A):
    x0, y0 = LOGO0; gx, gy, gw, gh = GO_REL
    tm = A.orig[y0 + gy:y0 + gy + gh, x0 + gx:x0 + gx + gw] == 0x16
    return [(X - gx, Y - gy) for X, Y, c in A.find(tm, 0x16)]


def logo_glyph():
    import pixfont as PF
    g = np.concatenate([np.pad(PF.cell(c, 11, bold=True), ((0, 0), (0, 1))) for c in '전차로'], 1)[:, :-1] > 0   # 글자 사이 1px
    ys = (np.arange(int(g.shape[0] * 1.5)) / 1.5).astype(int); m = g[ys]
    gh, gw = m.shape; it = np.zeros((gh, gw + gh // 8 + 1), bool)
    for y in range(gh):
        k = (gh - 1 - y) // 8; it[y, k:k + gw] = m[y]                                  # GO! 처럼 오른쪽으로 기울임
    return it


def put_logo(A, X, Y):
    """X, Y = 로고 왼쪽 위(본보기 124, 40 기준). 전차로 칸 = x X+4 … X+52, 행 Y+4 … Y+23"""
    C = A.can; o = A.orig
    x0, x1, y0, y1 = X + 4, X + 50, Y + 4, Y + 23          # で 끝 x+50 — 그 오른쪽은 G
    reg = o[y0:y1, x0:x1]; ink = np.isin(reg, list(LOGO_INK))
    p = np.pad(ink, 1); near = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): near |= np.roll(np.roll(p, dy, 0), dx, 1)
    rows_below = np.arange(y0, y1)[:, None] >= Y + 7                                  # 47행부터는 손 없음 → 검정도 전부 로고
    m = ink | ((reg == OUTLINE) & (near[1:-1, 1:-1] | rows_below))
    # で 오른쪽 위 끝 획(행 Y+4~Y+8, x X+50~X+53) — G 머리보다 위라 같이 지움
    top = o[Y + 4:Y + 9, X + 50:X + 54]; tk = np.isin(top, list(LOGO_INK)) | (top == OUTLINE)
    C[Y + 4:Y + 9, X + 50:X + 54][tk] = 0
    ramp = {}
    for yy in range(y0, y1):                                                           # 줄별 로고 속 색(가장 많은 노랑~빨강)
        r = reg[yy - y0][np.isin(reg[yy - y0], list(BRIGHT))]                       # 밝은 노랑·주황·빨강만(갈색 줄 막기, 하스피)
        if len(r): ramp[yy] = collections.Counter(r.tolist()).most_common(1)[0][0]
    C[y0:y1, x0:x1][m] = 0
    it = logo_glyph(); gh, gw = it.shape
    assert gw + 2 <= x1 - x0, ('전차로 폭', gw)
    by = Y + 22 - gh; bx = x1 - gw                                                      # 바닥 = GO! 바닥(행 Y+22), 오른쪽 = GO! 바로 앞
    big = np.zeros_like(C, bool); big[by:by + gh, bx:bx + gw] = it
    p = np.pad(big, 1); dil = np.zeros_like(p)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): dil |= np.roll(np.roll(p, dy, 0), dx, 1)
    ring = dil[1:-1, 1:-1] & ~big
    C[ring & ~np.isin(C, [0xC, 0x10, 0xB, 0x11, 0xD, 0x1A])] = OUTLINE                 # 손(살색) 위에는 테두리 안 덮음
    keys = sorted(ramp)
    for yy in range(by, by + gh):
        col = ramp.get(yy) or ramp[min(keys, key=lambda k: abs(k - yy))]
        C[yy][big[yy]] = col





if __name__ == '__main__':
    d, A, new = build(); print('새 셀', A.added, '로고', A.logos)
    a = GJ.rgb(A.orig[0:448, 0:480], d); b = GJ.rgb(A.can[0:448, 0:480], d)
    sh = np.concatenate([a, np.full((448, 4, 3), 255, np.uint8), b], 1)
    p = os.path.join(ROOT, 'work', 'gfx', 'prev_bubble.png')
    Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(p); print(p)
