# -*- coding: utf-8 -*-
r"""구간 팝업 시트의 파란 띠 역 문구 한글화(2026-11-01)
  고정 부분 모양(초록 글자 가면)으로 위치 찾기: «駅出発進行»(B1201 x65~168) · «駅停車»(B1201 x209~269) · «通過»(B3207 x225~263)
  출발 = [띠 시작, 進行 끝) → «A역출발진행» · 정차 = [進行 끝, 車 끝) → «B역정차» · 통과 = [띠 시작, 過 끝) → «○○통과»
  역 이름 = 파일 번호(노선 순서) 표 SEC · 통과 이름 = PASS(그림 읽어 정함). 같은 역 이름 그림이 시트끼리 같은지 검산(check).
  python tools/stn_ex.py check · python tools/stn_ex.py pass(통과 이름 그림 모으기)
"""
import os, sys, collections, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ
import popup_ex as P

R1 = '渋谷 恵比寿 目黒 五反田 大崎 品川 田町 浜松町 新橋 有楽町 東京'.split()
R2 = '品川 大井町 大森 蒲田 川崎 鶴見 新子安 東神奈川 横浜'.split()
R3 = '京都 西大路 向日町 長岡京 高槻 茨木 新大阪 大阪'.split()
R4 = '亀岡 馬堀 保津峡 嵯峨嵐山 太秦 花園 二条 丹波口 京都'.split()
R7 = '京都 西大路 向日町 長岡京 高槻 摂津富田 茨木 千里丘 岸辺 吹田 東淀川 新大阪 大阪'.split()


def sec_table():
    T = {}
    for pre, R in (('DR_B12', R1), ('DR_B52', R1), ('DR_B22', R2), ('DR_B62', R2), ('DR_B42', R4), ('DR_B82', R4)):
        for i in range(len(R) - 1): T['%s%02X' % (pre, i)] = (R[i], R[i + 1])
    # 東海道(B3): 고속 구간 몇 개는 같은 구간 변형(난이도별) — 띠에서 읽은 것(lines.png)
    T.update({'DR_B3200': ('京都', '西大路'), 'DR_B3201': ('西大路', '向日町'), 'DR_B3202': ('向日町', '長岡京'),
              'DR_B3203': ('長岡京', '高槻'), 'DR_B3204': ('長岡京', '高槻'), 'DR_B3205': ('高槻', '茨木'), 'DR_B3206': ('高槻', '茨木')})
    for k in ('DR_B3207', 'DR_B3208', 'DR_B3209', 'DR_B320A', 'DR_B320B'): T[k] = ('茨木', '新大阪')
    T['DR_B320C'] = ('新大阪', '大阪')
    # 東海道 EXTRA(B7): lines/secs 대조로 읽음(2026-11-01) — 7204 는 高槻→茨木(B3205 와 같음), 그 뒤 한 칸씩
    for k, v in {'DR_B7200': ('京都', '西大路'), 'DR_B7201': ('西大路', '向日町'), 'DR_B7202': ('向日町', '長岡京'), 'DR_B7203': ('長岡京', '高槻'),
                 'DR_B7204': ('高槻', '茨木'), 'DR_B7205': ('高槻', '摂津富田'), 'DR_B7206': ('摂津富田', '茨木'), 'DR_B7207': ('茨木', '千里丘'),
                 'DR_B7208': ('千里丘', '岸辺'), 'DR_B7209': ('岸辺', '吹田'), 'DR_B720A': ('吹田', '東淀川'), 'DR_B720B': ('東淀川', '新大阪'),
                 'DR_B720C': ('新大阪', '大阪')}.items(): T[k] = v
    for k in ('DR_B8202', 'DR_B8203', 'DR_B8204', 'DR_B8205', 'DR_B8206'): T[k] = ('保津峡', '嵯峨嵐山')        # 山陰 B8: 다섯 장 같은 구간
    return T


SEC = sec_table()
DEP = ('DR_B1201', (65, 128, 168, 144))
ARR = ('DR_B1201', (209, 128, 269, 144))
PAS = ('DR_B3207', (225, 240, 263, 256))
DIC = None


def green_of(pal):
    return np.array([(v >> 5 & 31) >= 16 and (v & 31) < 12 for v in pal])


def navy_of(pal):
    return np.array([(v >> 10 & 31) >= 10 and (v & 31) < 6 and (v >> 5 & 31) < 6 for v in pal])


def tmpl(src):
    sh, (x0, y0, x1, y1) = src
    d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
    return green_of(pal)[A.orig[y0:y1, x0:x1]]


_T = {}


def find(G, t, tol=0.97):
    h, w = t.shape; H_, W_ = G.shape[0] - h + 1, G.shape[1] - w + 1
    pts = np.argwhere(t); y0, x0 = pts[0]
    ok = G[y0:y0 + H_, x0:x0 + W_].copy()
    for y, x in pts[::max(1, len(pts) // 50)]: ok &= G[y:y + H_, x:x + W_]
    out = []
    for y, x in np.argwhere(ok):
        r = G[y:y + h, x:x + w]
        if r[t].mean() >= 0.95 and (~r[~t]).mean() >= 0.95: out.append((int(x), int(y)))   # 초록도 빈 곳도 각각 95%
    return out


def bar_start(N, x, y, h=16, G=None):
    """띠 왼쪽 끝: 그 열에 남색이나 초록 글자가 하나라도 있으면 띠 안(글자 검정 테두리 때문에 남색만 세면 일찍 멈춤)"""
    while x > 0 and (N[y:y + h, x - 1].any() or (G is not None and G[y:y + h, x - 1].any())): x -= 1
    return x


def items(A, pal):
    """→ [('dep'|'arr'|'pas', x0, y, x1, 이름 영역(x0, x1))]"""
    for k, src in (('dep', DEP), ('arr', ARR), ('pas', PAS)):
        if k not in _T: _T[k] = tmpl(src)
    G = green_of(pal)[A.orig]; N = navy_of(pal)[A.orig]
    out = []
    deps = find(G, _T['dep']); arrs = find(G, _T['arr']); pas = find(G, _T['pas'])
    for x, y in deps:
        xs = bar_start(N, x, y, G=G); out.append(('dep', xs, y, x + 103, (xs, x)))
        nx = [a for a in arrs if abs(a[1] - y) <= 1 and a[0] > x]
        if nx:
            ax, ay = min(nx); out.append(('arr', x + 103, y, ax + 60, (x + 103, ax)))
    for x, y in arrs:
        if not any(o[0] == 'arr' and abs(o[2] - y) <= 1 and abs(o[3] - (x + 60)) <= 1 for o in out):
            xs = bar_start(N, x, y, G=G); out.append(('arr', xs, y, x + 60, (xs, x)))       # 출발 없이 정차만 있는 줄
    for x, y in pas:
        xs = bar_start(N, x, y, G=G)
        # 앞에 정차 문구가 붙어 있으면(같은 띠) 그 끝부터
        prev = [o for o in out if o[0] == 'arr' and abs(o[2] - y) <= 1 and o[3] <= x]
        if prev: xs = max(xs, max(o[3] for o in prev))
        out.append(('pas', xs, y, x + 38, (xs, x)))
    return out


def name_img(A, pal, item):
    k, x0, y, x1, (a, b) = item
    return green_of(pal)[A.orig[y:y + 16, a:b]]


if __name__ == '__main__' and sys.argv[1:] == ['check']:
    seen = collections.defaultdict(dict); miss = []
    for sh in P.FILES:
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        its = items(A, pal)
        kinds = collections.Counter(i[0] for i in its)
        if sh not in SEC: print(sh, '구간표 없음', dict(kinds)); continue
        a, b = SEC[sh]
        for it in its:
            if it[0] == 'pas': continue
            nm = a if it[0] == 'dep' else b
            img = name_img(A, pal, it); k = hashlib.md5(np.packbits(img).tobytes() + str(img.shape).encode()).hexdigest()[:8]
            seen[nm][k] = seen[nm].get(k, []) + [sh + it[0][0]]
        if kinds['dep'] != 1 or kinds['arr'] != 1: miss.append((sh, dict(kinds)))
    for nm, v in seen.items():
        if len(v) > 1: print('역 그림 여러 벌', nm, {k: s[:4] for k, s in v.items()})
    print('출발/정차 1개씩 아닌 시트', miss)

if __name__ == '__main__' and sys.argv[1:] == ['pass']:
    from PIL import ImageDraw
    U = collections.OrderedDict()
    for sh in P.FILES:
        d = open(os.path.join(P.DISC, sh + '.BIN'), 'rb').read(); A = atlas.Atlas(d); pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int)
        for it in items(A, pal):
            if it[0] != 'pas': continue
            img = name_img(A, pal, it); k = hashlib.md5(np.packbits(img).tobytes() + str(img.shape).encode()).hexdigest()[:8]
            if k not in U: U[k] = (sh, it, GJ.rgb(A.orig[it[2]:it[2] + 16, it[1]:it[3]], d))
    cv = Image.new('RGB', (900, 40 * len(U) + 10), (255, 255, 255)); dr = ImageDraw.Draw(cv)
    for i, (k, (sh, it, im)) in enumerate(U.items()):
        dr.text((4, i * 40 + 12), '%d %s %s' % (i, sh[-4:], k), fill=(255, 0, 0))
        cv.paste(Image.fromarray(im).resize((im.shape[1] * 2, im.shape[0] * 2), Image.NEAREST), (200, i * 40))
    cv.save(os.path.join(P.ROOT, 'work', 'popup', 'pass.png')); print('통과 이름', len(U))
    json.dump({k: v[0] for k, v in U.items()}, open(os.path.join(P.ROOT, 'work', 'popup', 'pass.json'), 'w'))


# 통과 이름(pass.png 읽음, 2026-11-01) — 그림 키 → 한국어(강 = ○○강, 역 = 사전)
PASS = {'633b8077': '타마강', 'a67b64fc': '츠루미강', '92f5782e': '카츠라강', 'f631ec07': '야마자키역', '9b36cab4': '셋츠톤다역',
        '46f2279a': '아이강', '523bdf37': '센리오카역', '8bd23525': '키시베역', '56a7e8d2': '스이타역', 'e6d12a23': '칸자키강',
        '25092fa5': '히가시요도가와역', 'ad1b0f91': '요도강', 'a66258eb': '호즈강'}


def kr_dict():
    global DIC
    if DIC is None:
        DIC = {}
        base = os.path.join(P.ROOT, '..', 'densha-pro-kr-patch', 'work', 'text')
        for f in ('stations.tsv', 'stn_board_kr.tsv'):
            for ln in open(os.path.join(base, f), encoding='utf-8'):
                c = ln.rstrip('\n').split('\t')
                if len(c) >= 2 and c[0] not in DIC: DIC[c[0]] = c[1]
    return DIC


def apply(A, d, sheet):
    """시트의 역 문구(출발·정차·통과) 바꾸기 → [(종류, 한국어, x0, y)]"""
    pal = np.frombuffer(d[0x40:0x240], '>u2').astype(int); D = kr_dict(); done = []
    if sheet not in SEC: return done
    a, b = SEC[sheet]
    gm = green_of(pal); nv = navy_of(pal)
    for it in items(A, pal):
        k, x0, y, x1, (na, nb) = it
        if k == 'dep': t = D[a] + '역출발진행'
        elif k == 'arr': t = D[b] + '역정차'
        else:
            img = name_img(A, pal, it); key = hashlib.md5(np.packbits(img).tobytes() + str(img.shape).encode()).hexdigest()[:8]
            assert key in PASS, ('모르는 통과 이름', sheet, key)
            t = PASS[key] + '통과'
        N_ = nv[A.orig]; G_ = gm[A.orig]
        while k != 'dep' and x1 < A.orig.shape[1] and (N_[y:y + 16, x1].any() or G_[y:y + 16, x1].any()): x1 += 1   # 띠 오른쪽 끝까지(車 끝 획 잔재 — 하스피 «역정차 제대로 안 잘림»)
        reg = A.orig[y:y + 16, x0:x1]
        fills = collections.Counter(reg[gm[reg]].tolist()); fill = fills.most_common(1)[0][0]
        bgc = collections.Counter(reg[nv[reg]].tolist()); bg = bgc.most_common(1)[0][0] if bgc else None
        dark = collections.Counter(c for c in reg.ravel().tolist() if not gm[c] and not nv[c] and (pal[c] & 31) + (pal[c] >> 5 & 31) + (pal[c] >> 10 & 31) < 12)
        ring = dark.most_common(1)[0][0] if dark else None
        cv = A.can[y:y + 16, x0:x1]
        if bg is not None:                                                      # 띠 위: 남색으로 지움
            cv[~nv[reg]] = bg
        else:                                                                   # 띠 없는 통과 문구(바둑판 위): 셀 안 메움
            m = gm[reg] | (np.isin(reg, [ring]) if ring is not None else False)
            A.erase_cells(x0, y, x1 - x0, 16, m)
        for fn in ('B', 'G11', 'G9'):
            try:
                lv = GJ.word(t, x1 - x0, 16, fn, 'ring', 'c'); break                   # 하스피: 원본 파란 띠 가운데
            except AssertionError:
                continue
        else:
            raise AssertionError(('넘침', t, x1 - x0))
        if ring is None: lv[lv == 1] = 0
        A.put(x0, y, lv, fill, ring if ring is not None else fill)
        done.append((k, t, x0, y))
    return done
