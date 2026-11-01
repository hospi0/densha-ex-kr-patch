# -*- coding: utf-8 -*-
r"""구간 팝업 시트의 파란 띠 역 문구(○○駅出発進行△△駅停車 · ○○駅通過) 글자 인식(2026-11-01)
  띠 = 파란 바탕(0x7C00 근처) 줄 · 글자 = 초록 · 글자 사이 빈 열로 자름 → 고유 글자 모양 모음(work/popup/glyph_*.png, glyphs.json)
  python tools/stnbar.py scan → 띠 목록·고유 글자 · python tools/stnbar.py read → 시트별 문구(라벨 표 work/popup/glyph_labels.tsv 사용)
"""
import os, sys, json, glob, collections, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ
import popup_ex as P

OUT = os.path.join(ROOT, 'work', 'popup')


def bars(A, pal):
    """파란 바탕 행 묶음 → [(y0, y1, x0, x1)]"""
    blue = np.array([(v >> 10 & 31) >= 10 and (v & 31) < 6 and (v >> 5 & 31) < 6 for v in pal])
    bm = blue[A.orig]
    rows = bm.sum(1) > 30
    out = []; y = 0; H = len(rows)
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]: y += 1
            if y - y0 >= 10:
                band = bm[y0:y]; cols = np.nonzero(band.mean(0) > 0.1)[0]
                seg = []; st = cols[0]; p = cols[0]
                for c in cols[1:]:
                    if c - p > 6: seg.append((st, p + 1)); st = c
                    p = c
                seg.append((st, p + 1))
                for a, b in seg:
                    if b - a > 30: out.append((y0, y, a, b))
        else:
            y += 1
    return out


def glyphs(A, pal, bar):
    """띠 안 초록 글자 → 빈 열로 자른 글자 [(x0, x1, 비트맵)]"""
    y0, y1, x0, x1 = bar
    green = np.array([(v >> 5 & 31) >= 16 and (v & 31) < 12 for v in pal])
    g = green[A.orig[y0:y1, x0:x1]]
    cols = g.any(0); out = []; x = 0; W = g.shape[1]
    while x < W:
        if cols[x]:
            s = x
            while x < W and cols[x]: x += 1
            out.append((x0 + s, x0 + x, g[:, s:x]))
        else:
            x += 1
    return out


def key(bm):
    return hashlib.md5(np.packbits(bm).tobytes() + str(bm.shape).encode()).hexdigest()[:8]


if __name__ == '__main__' and sys.argv[1:] == ['scan']:
    os.makedirs(OUT, exist_ok=True)
    uniq = collections.OrderedDict(); rec = {}
    for sh in P.FILES:
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        rec[sh] = []
        for bar in bars(A, pal):
            ks = []
            for gx0, gx1, bm in glyphs(A, pal, bar):
                k = key(bm)
                if k not in uniq: uniq[k] = (bm, sh)
                ks.append(k)
            rec[sh].append((list(map(int, bar)), ks))
    # 고유 글자 시트
    n = len(uniq); W = 16; R = (n + W - 1) // W; cell = max(bm.shape[1] for bm, _ in uniq.values()) + 4; ch = max(bm.shape[0] for bm, _ in uniq.values())
    im = Image.new('RGB', (W * cell * 2, R * (ch + 10) * 2), (255, 255, 255))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    for i, (k, (bm, sh)) in enumerate(uniq.items()):
        g = Image.fromarray((~bm * 255).astype(np.uint8)).resize((bm.shape[1] * 2, bm.shape[0] * 2), Image.NEAREST)
        x = (i % W) * cell * 2; y = (i // W) * (ch + 10) * 2
        im.paste(g, (x, y + 16)); dr.text((x, y), str(i), fill=(255, 0, 0))
    im.save(os.path.join(OUT, 'glyphs.png'))
    json.dump(dict(keys=list(uniq.keys()), rec=rec), open(os.path.join(OUT, 'glyphs.json'), 'w'))
    print('띠 시트', sum(1 for v in rec.values() if v), '고유 글자', n)
    for sh in P.FILES[:3]: print(sh, [(b, len(k)) for b, k in rec[sh]])


def lines_of(A, pal):
    """같은 행 띠 조각을 한 줄로 → [(y0, y1, [(gx0, gx1, 비트맵)…])]"""
    by = collections.OrderedDict()
    for bar in bars(A, pal):
        y0, y1, x0, x1 = bar
        by.setdefault((y0, y1), []).extend(glyphs(A, pal, bar))
    return [(y0, y1, sorted(gs, key=lambda g: g[0])) for (y0, y1), gs in by.items() if gs]


# 고정 글자(B1201 恵比寿駅出発進行目黒駅停車 에서 딴 키)
def fixed_keys():
    d = open(os.path.join(P.DISC, 'DR_B1201.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    (y0, y1, gs), = [l for l in lines_of(A, pal) if len(l[2]) == 13]
    ks = [key(g[2]) for g in gs]
    return dict(zip('恵比寿駅出発進行目黒駅停車', ks))


if __name__ == '__main__' and sys.argv[1:] == ['names']:
    F = fixed_keys(); EKI, SHU, HATSU, SHIN, KOU, TEI, SHA = F['駅'], F['出'], F['発'], F['進'], F['行'], F['停'], F['車']
    names = collections.OrderedDict(); per = {}
    for sh in P.FILES:
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        per[sh] = []
        for y0, y1, gs in lines_of(A, pal):
            ks = [key(g[2]) for g in gs]
            per[sh].append((y0, ks))
            # 역 이름 조각: 駅 앞까지 / 進行 뒤 ~ 駅停車 앞
            cuts = []
            i = 0
            while i < len(ks):
                if ks[i] == EKI: cuts.append(i)
                i += 1
            prev = 0
            for c in cuts:
                seg = ks[prev:c]
                if seg and seg[0] in (SHU,): seg = seg[5 - 1:]
                if seg[:4] == [SHU, HATSU, SHIN, KOU]: seg = seg[4:]
                if seg:
                    t = tuple(seg)
                    if t not in names: names[t] = (sh, y0, gs[prev][0], gs[c - 1][1], y1)
                prev = c + 1
    json.dump(dict(names=[[list(k), [str(v[0])] + [int(t) for t in v[1:]]] for k, v in names.items()]), open(os.path.join(OUT, 'stn_names.json'), 'w'))
    # 그림
    from PIL import ImageDraw
    rows = []
    for i, (k, (sh, y0, x0, x1, y1)) in enumerate(names.items()):
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d)
        im = GJ.rgb(A.orig[y0:y1, x0:x1], d); rows.append((i, sh, im))
    W = 2; cw = max(r[2].shape[1] for r in rows) + 60; chh = max(r[2].shape[0] for r in rows) + 4
    canvas = Image.new('RGB', (W * cw * 2, ((len(rows) + W - 1) // W) * chh * 2), (255, 255, 255)); dr = ImageDraw.Draw(canvas)
    for j, (i, sh, im) in enumerate(rows):
        x = (j % W) * cw * 2; y = (j // W) * chh * 2
        dr.text((x, y + 8), '%d %s' % (i, sh[-4:]), fill=(255, 0, 0))
        canvas.paste(Image.fromarray(im).resize((im.shape[1] * 2, im.shape[0] * 2), Image.NEAREST), (x + 110, y))
    canvas.save(os.path.join(OUT, 'stn_names.png')); print('역 이름 그림', len(names))


# stn_names.png 를 보고 읽은 글자(2026-11-01) — 번호 순
READ = ['渋谷', '出発進行恵比寿', '恵比寿', '出発進行目黒', '出発進行五反田', '出発進行大崎', '出発進行品川', '出発進行田町',
        '出発進行浜松町', '出発進行新橋', '出発進行大井町', '出発進行大森', '出発進行蒲田', '出発進行川崎', '出発進行鶴見',
        '出発進行新子安', '出発進行東神奈川', '京都', '出発進行西大路', '向日町', '出発進行長岡京', '高槻', '出発進行茨木',
        '出発進行新大阪', '嵯峨嵐山', '出発進行太秦', '出発進行二条', '出発進行丹波口', '丹波口', '出発進行京都',
        '出発進行摂津富田', '出発進行千里丘', '出発進行岸辺', '吹田', '出発進行東淀川', '出発進行大阪']


def glyph_table():
    J = json.load(open(os.path.join(OUT, 'stn_names.json')))
    T = {}; bad = []
    for (ks, info), txt in zip(J['names'], READ):
        if len(ks) != len(txt): bad.append((txt, len(ks))); continue
        for k, c in zip(ks, txt):
            if k in T and T[k] != c: bad.append(('충돌', k, T[k], c))
            T[k] = c
    F = fixed_keys()
    for c, k in F.items(): T.setdefault(k, c)
    return T, bad


def read_lines(sh, T):
    d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    out = []
    for y0, y1, gs in lines_of(A, pal):
        txt = ''.join(T.get(key(g[2]), '?') for g in gs)
        out.append((y0, y1, gs[0][0], gs[-1][1], txt))
    return out


if __name__ == '__main__' and sys.argv[1:] == ['read']:
    T, bad = glyph_table(); print('글자표', len(T), '문제', bad)
    unk = collections.Counter()
    for sh in P.FILES:
        ls = read_lines(sh, T)
        print(sh, [l[4] for l in ls])
        for l in ls: unk.update(ch for ch in l[4] if ch == '?')
    print('모르는 글자 수', unk)


def line_boxes(A, pal):
    """파란 띠 한 줄 = 같은 행 띠 조각 합친 사각형(y0, y1, x0, x1)"""
    by = collections.OrderedDict()
    for y0, y1, x0, x1 in bars(A, pal):
        if (y1 - y0) > 20: continue                                         # 一時停止 파란 상자 제외
        a = by.get((y0, y1)); by[(y0, y1)] = (min(a[0], x0), max(a[1], x1)) if a else (x0, x1)
    return [(int(y0), int(y1), int(x0), int(x1)) for (y0, y1), (x0, x1) in by.items()]


if __name__ == '__main__' and sys.argv[1:] == ['uniq']:
    from PIL import ImageDraw
    U = collections.OrderedDict(); where = collections.defaultdict(list)
    for sh in P.FILES:
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        for (y0, y1, x0, x1) in line_boxes(A, pal):
            rgb = pal[A.orig[y0:y1, x0:x1]]; k = hashlib.md5(rgb.tobytes()).hexdigest()[:10]
            if k not in U: U[k] = (sh, (y0, y1, x0, x1), GJ.rgb(A.orig[y0:y1, x0:x1], d))
            where[k].append((sh, (y0, y1, x0, x1)))
    json.dump(dict(order=list(U.keys()), where=where, first={k: [v[0], list(v[1])] for k, v in U.items()}), open(os.path.join(OUT, 'lines.json'), 'w'))
    rows = list(U.items()); W = 2; cw = max(v[2].shape[1] for _, v in rows) + 70; ch = 20
    cv = Image.new('RGB', (W * cw * 2, ((len(rows) + W - 1) // W) * ch * 2), (255, 255, 255)); dr = ImageDraw.Draw(cv)
    for i, (k, (sh, b, im)) in enumerate(rows):
        x = (i % W) * cw * 2; y = (i // W) * ch * 2
        dr.text((x, y + 10), '%d %s' % (i, sh[-4:]), fill=(255, 0, 0))
        cv.paste(Image.fromarray(im).resize((im.shape[1] * 2, im.shape[0] * 2), Image.NEAREST), (x + 120, y))
    cv.save(os.path.join(OUT, 'lines.png')); print('고유 줄', len(rows), cv.size)
