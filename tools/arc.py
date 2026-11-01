# -*- coding: utf-8 -*-
r"""전차로 GO! EX 묶음·압축(2026-10-31 조사로 확정)
  SZ3: 'SZ3\0' + u32 BE 풀린 크기 + 8 B 0 + 깃발 LZSS
       깃발 1바이트 MSB 먼저 · 1 = 날바이트 · 0 = 2바이트 참조 b0 b1: 거리 = b0 | (b1 & 0xF0) << 4(뒤로), 길이 = (b1 & 15) + 3
       ⚠️2026-10-31 정정: 처음 쓴 (b0<<4 | b1>>4)+1 도 크기는 맞지만 내용이 틀림(범위 밖 참조 → 0, DARC 표 쓰레기).
         새 해석 = SZ3 18개 모두 범위 밖 참조 0·DARC 오프셋 쓰레기 0
  DARC: 'DARC0090' + u32 0 + u32 BE 항목 수 n + u32 BE 오프셋 n개(0 = 빈 항목), 크기 = 다음 0 아닌 오프셋(마지막은 파일 끝)까지
  python tools/arc.py unpack   → work/x/<파일>/<번호>.bin (SZ3 는 먼저 풀고, 안의 DARC 도 한 단계 풂)"""
import os, struct, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sz3(d):
    assert d[:4] == b'SZ3\0', d[:4]
    size = struct.unpack('>I', d[4:8])[0]; out = bytearray(); i = 16
    while len(out) < size:
        fl = d[i]; i += 1
        for b in range(7, -1, -1):
            if len(out) >= size: break
            if fl >> b & 1:
                out.append(d[i]); i += 1
            else:
                b0, b1 = d[i], d[i + 1]; i += 2
                dist = b0 | ((b1 & 0xF0) << 4); ln = (b1 & 15) + 3
                assert 0 < dist <= len(out), (i, dist, len(out))
                for _ in range(ln): out.append(out[-dist])
    return bytes(out)


def chr_dec(d):
    """CHR 압축(D01~19.CHR·GO_TITL2/3.BIN) — 0.BIN 0x0600E8A0 풀개 그대로(2026-10-31 디스어셈 확정)
    머리: u8 종류 t(0~5) + u8 0 + u32 LE 풀린 크기 + u32 LE 압축 크기, 데이터 10~
    k = t + 2 · 링 N = 2^(16-k) 0 채움 · 쓰기 시작 = N - (2^k - 1 + 3)
    깃발 1바이트 LSB 먼저 · 1 = 날바이트 · 0 = b0 b1: 위치 = b0 | (b1 >> k) << 8, 길이 = (b1 & (2^k - 1)) + 3"""
    t = d[0]; size = struct.unpack_from('<I', d, 2)[0]
    k = t + 2; mask = (1 << k) - 1; N = 1 << (16 - k); r = N - (mask + 3)
    ring = bytearray(N); out = bytearray(); i = 10
    while len(out) < size:
        fl = d[i]; i += 1
        for b in range(8):
            if len(out) >= size: break
            if fl >> b & 1:
                c = d[i]; i += 1; out.append(c); ring[r] = c; r = (r + 1) % N
            else:
                b0, b1 = d[i], d[i + 1]; i += 2; p = b0 | (b1 >> k) << 8
                for j in range((b1 & mask) + 3):
                    c = ring[(p + j) % N]; out.append(c); ring[r] = c; r = (r + 1) % N
    return bytes(out)


def is_chr(d):
    return len(d) > 12 and d[0] < 6 and d[1] == 0 and struct.unpack_from('<I', d, 6)[0] == len(d) - 10


def darc(d):
    """→ [(번호, 오프셋, 바이트)] 빈 항목 뺌"""
    assert d[:8] == b'DARC0090', d[:8]
    n = struct.unpack('>I', d[12:16])[0]; offs = struct.unpack('>%dI' % n, d[16:16 + 4 * n])
    nz = sorted(set(o for o in offs if o))
    out = []
    for k, o in enumerate(offs):
        if not o: continue
        j = nz.index(o); e = nz[j + 1] if j + 1 < len(nz) else len(d)
        out.append((k, o, d[o:e]))
    return out


def load(name):
    d = open(os.path.join(ROOT, 'work', 'disc0', name), 'rb').read()
    return sz3(d) if d[:4] == b'SZ3\0' else chr_dec(d) if is_chr(d) else d


if __name__ == '__main__':
    if sys.argv[1] == 'unpack':
        n = 0
        for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'disc0', '*'))):
            nm = os.path.basename(p); d = open(p, 'rb').read()
            if d[:4] == b'SZ3\0': d = sz3(d)
            if d[:8] != b'DARC0090': continue
            out = os.path.join(ROOT, 'work', 'x', nm); os.makedirs(out, exist_ok=True)
            for k, o, b in darc(d):
                open(os.path.join(out, '%03d.bin' % k), 'wb').write(b); n += 1
        print(n, '항목 → work/x/')
