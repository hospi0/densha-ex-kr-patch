# -*- coding: utf-8 -*-
"""압축 형식 판별용(2026-10-31) — SZ3 깃발 LZSS 변형을 차례로 대 보고 풀린 크기·내용으로 판정"""
import struct, sys, itertools


def lzss(src, pos, outsize, *, lsb=True, lit1=True, ref='okumura', N=4096, F=18, init=0xFEE, fill=0x20, th=2):
    """ref: 'okumura'(b0 = off lo, b1 = off hi4<<4 | len) · 'hi'(b0 = off hi4<<4|len … 반대) · 'rel'(상대 거리)"""
    win = bytearray([fill] * N); r = init; out = bytearray(); i = pos
    while len(out) < outsize and i < len(src):
        flags = src[i]; i += 1
        order = range(8) if lsb else range(7, -1, -1)
        for b in order:
            if len(out) >= outsize or i >= len(src): break
            bit = (flags >> b) & 1
            if bit == (1 if lit1 else 0):
                c = src[i]; i += 1; out.append(c); win[r] = c; r = (r + 1) % N
            else:
                if i + 1 >= len(src): return out, i
                b0, b1 = src[i], src[i + 1]; i += 2
                if ref == 'okumura':
                    off = b0 | ((b1 & 0xF0) << 4); ln = (b1 & 0x0F) + th + 1
                    for k in range(ln):
                        c = win[(off + k) % N]; out.append(c); win[r] = c; r = (r + 1) % N
                elif ref == 'be':
                    off = (b0 << 4) | (b1 >> 4); ln = (b1 & 0x0F) + th + 1
                    for k in range(ln):
                        c = win[(off + k) % N]; out.append(c); win[r] = c; r = (r + 1) % N
                elif ref in ('rel', 'rel2'):
                    if ref == 'rel': d = ((b0 << 4) | (b1 >> 4)) + 1; ln = (b1 & 0xF) + th + 1
                    else: d = (b0 | ((b1 & 0xF0) << 4)) + 1; ln = (b1 & 0xF) + th + 1
                    for k in range(ln):
                        c = out[-d] if d <= len(out) else 0; out.append(c)
    return out, i


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    size = struct.unpack('>I', d[4:8])[0]; pos = 16
    for lsb, lit1, ref, init in itertools.product([True, False], [True, False], ['okumura', 'be', 'rel', 'rel2'], [0xFEE, 0, 0xFF0]):
        if ref.startswith('rel') and init: continue
        try:
            o, i = lzss(d, pos, size, lsb=lsb, lit1=lit1, ref=ref, init=init)
        except Exception as e:
            continue
        ok = o[:8] == b'DARC0090'
        cnt = struct.unpack('>I', o[12:16])[0] if len(o) >= 16 else -1
        print('lsb=%d lit1=%d %-7s init=%04x out=%6d/%d end=%6d/%d DARC=%s cnt=%d' % (lsb, lit1, ref, init, len(o), size, i, len(d), ok, cnt))
