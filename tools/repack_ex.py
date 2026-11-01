# -*- coding: utf-8 -*-
r"""그림 한글화 결과 → 디스크 파일 단위로 다시 싸기(2026-11-01) — 디스크 이미지는 만들지 않음(빌드는 하스피 허락 후)
  python tools/repack_ex.py → work/build/files/<디스크 파일 이름> + 보고(원래/새 크기, 왕복 검산)
  · DR_B?X00.SZ3: SZ3(DARC) — 000 hudtop_ex(노선별) · 001 hud_ex · 002 bubble_ex · 003 guide_ex(노선별) · 004 screens_ex(승객 急制動)
  · DR_H?002.SZ3: 001 judge_ex · 002 bonus_ex BONUS_02
  · 통째 그림 BIN: BONUS · DR_TUUTI·DR_JIKO·DR_START·DR_WARP(misc_ex) · CFG_000/001·CTRL·MSC_TES1(screens_ex)
  · 오버레이 BIN 안 CHR 그림(GO_*): 원래 압축 자리에 다시 압축해 넣고 남는 칸은 0 — 압축이 원래보다 크면 멈춤
  · 구간 팝업 DR_B?2??.BIN 은 popup_ex 가 work/build/popup 에 이미 만듦 → 여기로 복사
  DARC 항목 크기는 전부 그대로(새 셀 0) → 제자리 교체. 크기가 다르면 멈춤.
"""
import os, sys, struct, shutil, hashlib, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import arc, lzenc, v2img

DISC = os.path.join(ROOT, 'work', 'disc0'); OUT = os.path.join(ROOT, 'work', 'build', 'files')
LINES = (1, 2, 3, 4, 7)


def put_item(darc_bytes, k, new):
    items = {kk: (o, b) for kk, o, b in arc.darc(darc_bytes)}
    o, b = items[k]
    assert len(b) == len(new), ('항목 크기 다름', k, len(b), len(new))
    return darc_bytes[:o] + new + darc_bytes[o + len(b):]


def same_item(name, k, ref):
    d = arc.sz3(open(os.path.join(DISC, name), 'rb').read())
    return {kk: b for kk, o, b in arc.darc(d)}[k] == ref


def sz3_file(name, repl):
    raw = open(os.path.join(DISC, name), 'rb').read(); d = arc.sz3(raw)
    for k, new in repl.items(): d = put_item(d, k, new)
    z = lzenc.sz3_enc(d, raw); assert arc.sz3(z) == d
    return raw, z


def embedded_file(name, blocks):
    """blocks = {오프셋: 새 풀린 바이트}"""
    raw = bytearray(open(os.path.join(DISC, name + '.BIN'), 'rb').read()); orig = bytes(raw)
    for off, new in blocks.items():
        t = raw[off]; u, c = struct.unpack_from('<II', raw, off + 2)
        z = lzenc.chr_enc(new, t); assert arc.chr_dec(z) == new
        assert len(z) <= 10 + c, ('압축 넘침', name, hex(off), len(z) - 10, c)
        assert len(new) == u, ('풀린 크기 다름', name, hex(off), u, len(new))
        raw[off:off + 10 + c] = z + bytes(10 + c - len(z))
    return orig, bytes(raw)


def main():
    os.makedirs(OUT, exist_ok=True); rep = []
    import hud_ex, hudtop_ex, bubble_ex, guide_ex, judge_ex, bonus_ex, misc_ex, screens_ex as S
    hud_new = hud_ex.build()[3]; hud_src = open(hud_ex.SRC, 'rb').read()
    bub_new = bubble_ex.build()[2]; bub_src = open(bubble_ex.SRC, 'rb').read()
    pas_e, _, _, pas_new = S.build('DR_B1X00.SZ3/004.bin', 0)
    for n in LINES:
        nm = 'DR_B%dX00.SZ3' % n
        assert same_item(nm, 1, hud_src) and same_item(nm, 2, bub_src) and same_item(nm, 4, pas_e), ('노선 공통 항목이 다름', nm)
        repl = {0: hudtop_ex.build(n)[3], 1: hud_new, 2: bub_new, 3: guide_ex.build(n)[2], 4: pas_new}
        rep.append((nm,) + sz3_file(nm, repl))
    jd = judge_ex.build(); bo = bonus_ex.build('BONUS_02', bonus_ex.BONUS02)
    for n in (1, 2, 3, 4):
        nm = 'DR_H%d002.SZ3' % n
        assert same_item(nm, 1, jd[0]) and same_item(nm, 2, bo[0]), ('H 공통 항목이 다름', nm)
        rep.append((nm,) + sz3_file(nm, {1: jd[3], 2: bo[3]}))
    raws = {'BONUS': bonus_ex.build('BONUS', bonus_ex.BONUS)[3]}
    for nm in ('DR_TUUTI', 'DR_JIKO', 'DR_START', 'DR_WARP'): raws[nm] = misc_ex.build(nm)[3]
    for nm in ('CFG_000', 'CFG_001', 'CTRL', 'MSC_TES1'): raws[nm] = S.build(nm, 0)[3]
    for nm, new in raws.items():
        orig = open(os.path.join(DISC, nm + '.BIN'), 'rb').read(); assert len(orig) == len(new), nm
        rep.append((nm + '.BIN', orig, new))
    emb = {}
    for (nm, off) in list(S.JOBS) + list(S.EXTRA):
        if nm.startswith(('GO_',)) and off: emb.setdefault(nm, {})[off] = S.build(nm, off)[3]
    for nm, blocks in emb.items(): rep.append((nm + '.BIN',) + embedded_file(nm, blocks))
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'build', 'popup', '*.BIN'))):
        nm = os.path.basename(p); rep.append((nm, open(os.path.join(DISC, nm), 'rb').read(), open(p, 'rb').read()))
    for nm, orig, new in rep:
        open(os.path.join(OUT, nm), 'wb').write(new)
        print('%-14s %8d → %8d %s %s' % (nm, len(orig), len(new), '같음' if orig == new else '바뀜', hashlib.md5(new).hexdigest()[:8]))
    print('파일', len(rep), '→', OUT)


if __name__ == '__main__':
    main()
