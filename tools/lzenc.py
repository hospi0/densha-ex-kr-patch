# -*- coding: utf-8 -*-
r"""전차로 GO! EX 압축기(2026-10-31) — tools/arc.py 의 sz3()·chr_dec() 와 짝
  SZ3: 깃발 MSB 먼저 · 1 = 날바이트 · 참조 b0 b1: 거리 = b0 | (b1 & 0xF0) << 4 (1~4095), 길이 = (b1 & 15) + 3 (3~18)
  CHR: 종류 t, k = t + 2 · 깃발 LSB 먼저 · 참조: 링 위치 = b0 | (b1 >> k) << 8, 길이 = (b1 & (2^k - 1)) + 3
       링 N = 2^(16-k), 쓰기 시작 N - (2^k + 2), 0 채움 → 거리 d(1~N-1) 를 링 위치로 바꿔 씀
  최적 분할(DP, 날바이트 9비트·참조 17비트) + 해시 사슬 후보.
  python tools/lzenc.py test   → 원본 SZ3/CHR 왕복·크기 비교
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import arc

CHAIN = 96


def _matches(d, maxd, maxlen):
    """위치마다 [(길이, 거리)] — 길이별 가장 가까운 거리(길이 3 이상)"""
    n = len(d); head = {}; prev = [-1] * n; res = [None] * n
    for i in range(n):
        cand = []
        if i + 3 <= n:
            key = d[i:i + 3]; j = head.get(key, -1); c = 0; best = 2
            lim = min(maxlen, n - i)
            while j >= 0 and i - j <= maxd and c < CHAIN:
                if d[j + best] == d[i + best] if i + best < n else False:
                    L = 3
                    while L < lim and d[j + L] == d[i + L]:
                        L += 1
                    if L > best:
                        cand.append((L, i - j)); best = L
                        if L == lim: break
                j = prev[j]; c += 1
            prev[i] = head.get(key, -1); head[key] = i
        res[i] = cand
    return res


def _parse(d, maxd, maxlen):
    """최적 분할 → [('L', 바이트) | ('R', 길이, 거리)]"""
    n = len(d); M = _matches(d, maxd, maxlen)
    INF = 1 << 60; cost = [INF] * (n + 1); cost[n] = 0; ch = [None] * n
    for i in range(n - 1, -1, -1):
        bc = cost[i + 1] + 9; bch = None
        lo = 3
        for L, dist in M[i]:                       # 거리 오름차순 = 길이 오름차순(후보는 더 길 때만 추가)
            for l in range(lo, L + 1):
                c = cost[i + l] + 17
                if c < bc: bc = c; bch = (l, dist)
            lo = L + 1
        cost[i] = bc; ch[i] = bch
    out = []; i = 0
    while i < n:
        if ch[i] is None: out.append(('L', d[i])); i += 1
        else: l, dist = ch[i]; out.append(('R', l, dist)); i += l
    return out


def sz3_enc(d, head=None):
    toks = _parse(d, 4095, 18)
    body = bytearray(); k = 0
    while k < len(toks):
        grp = toks[k:k + 8]; fl = 0; part = bytearray()
        for b, t in enumerate(grp):
            if t[0] == 'L':
                fl |= 0x80 >> b; part.append(t[1])
            else:
                l, dist = t[1], t[2]; part += bytes((dist & 0xFF, (dist >> 8) << 4 | (l - 3)))
        body.append(fl); body += part; k += 8
    h = bytearray(head[:16]) if head else bytearray(b'SZ3\0' + bytes(12))
    h[4:8] = struct.pack('>I', len(d))
    return bytes(h) + bytes(body)


def chr_enc(d, t):
    k = t + 2; mask = (1 << k) - 1; N = 1 << (16 - k); r0 = N - (mask + 3)
    toks = _parse(d, N - 1, mask + 3)
    body = bytearray(); pos = 0; i = 0
    while i < len(toks):
        grp = toks[i:i + 8]; fl = 0; part = bytearray()
        for b, tk in enumerate(grp):
            if tk[0] == 'L':
                fl |= 1 << b; part.append(tk[1]); pos += 1
            else:
                l, dist = tk[1], tk[2]; p = (r0 + pos - dist) % N
                part += bytes((p & 0xFF, (p >> 8) << k | (l - 3))); pos += l
        body.append(fl); body += part; i += 8
    return bytes((t, 0)) + struct.pack('<II', len(d), len(body)) + bytes(body)


if __name__ == '__main__' and sys.argv[1:] == ['test']:
    import glob, time
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'disc0', '*'))):
        raw = open(p, 'rb').read(); nm = os.path.basename(p)
        if raw[:4] == b'SZ3\0':
            d = arc.sz3(raw); t0 = time.time(); e = sz3_enc(d, raw)
            assert arc.sz3(e) == d, nm
        elif arc.is_chr(raw):
            d = arc.chr_dec(raw); t0 = time.time(); e = chr_enc(d, raw[0])
            assert arc.chr_dec(e) == d, nm
        else:
            continue
        print('%-14s 원본 %7d  새 %7d  (%+d)  %.1fs' % (nm, len(raw), len(e), len(e) - len(raw), time.time() - t0))
