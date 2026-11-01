# -*- coding: utf-8 -*-
r"""스테이트 화면 출처 찾기(2026-10-31): VDP2 NBG0~3 셀 / VDP1 텍스처 바이트를 디스크(SZ3·DARC 풀어서) 에서 검색
  python tools/srcfind.py <스테이트이름 ...>"""
import os, sys, glob, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import vdp2render as R, arc


def corpus():
    res = []

    def walk(name, d, depth):
        res.append((name, d))
        if d[:8] == b'DARC0090' and depth < 3:
            for k, o, b in arc.darc(d): walk('%s/%03d' % (name, k), b, depth + 1)
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'disc0', '*'))):
        d = open(p, 'rb').read()
        if d[:4] == b'SZ3\0': d = arc.sz3(d)
        walk(os.path.basename(p), d, 0)
    return res


if __name__ == '__main__':
    C = corpus(); top = [(n, d) for n, d in C if '/' not in n]
    for st in sys.argv[1:]:
        v = open(os.path.join(ROOT, 'work', 'mem', st, 'VDP2_VRAM.bin'), 'rb').read()
        _, reg, _ = R.load(st)
        for n in range(4):
            I = R.info(reg, n)
            if not I['on']: continue
            if I['bmen']: print(st, 'NBG%d 비트맵' % n); continue
            im, I = R.render(st, n)
            used = [c for c in sorted(set(int(x) for x in I['cells'].ravel())) if len(set(v[c * 32:c * 32 + 64])) > 1]
            hit = collections.Counter(); miss = 0
            for c in used:
                blk = v[c * 32:c * 32 + 64]; f = [nm for nm, d in top if blk in d]
                if f: hit[f[0]] += 1
                else: miss += 1
            print(st, 'NBG%d' % n, I['colors'], '셀', len(used), '못찾음', miss, hit.most_common(4))
        v1 = open(os.path.join(ROOT, 'work', 'mem', st, 'VDP1_VRAM.bin'), 'rb').read()
        v1 = bytes(b for i in range(0, len(v1), 2) for b in (v1[i + 1], v1[i]))   # ⚠️이 게임 VDP1 덤프는 u16 뒤집힘
        # VDP1 텍스처 = 그림 형식 셀을 래스터로 옮긴 것 → 8 B 줄 표본을 (풀린) 디스크 전체에서 검색
        hit = collections.Counter(); tot = 0
        for a in range(0x8000, len(v1), 0x100):
            blk = v1[a:a + 8]
            if len(set(blk)) < 5: continue
            tot += 1; f = [nm for nm, d in C if blk in d and '/' in nm or blk in d and nm.endswith(('.BIN', '.SZ3'))]
            if f: hit[f[-1]] += 1
        print(st, 'VDP1 표본', tot, hit.most_common(6))
