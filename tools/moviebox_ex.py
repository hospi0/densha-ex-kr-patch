# -*- coding: utf-8 -*-
r"""열차 소개 동영상(DE_C0200~0500.CPK, 320×224 cinepak 띠 2개 15fps, 71프레임) 설명 상자 한글화(2026-11-01)
  프레임 3~66 에 흰 글자 설명(제목 + 3~5줄)이 박혀 있다 → 글자 범위 안 «흰 화소(+1px)»를 이웃 화소로 안쪽부터 메우고
  갈무리11(제목 Bold) 로 한국어를 원래 줄 자리에 그림. 글자 밝기 = 프레임마다 원래 흰 글자 밝기(페이드인 따라감).
  굽기 = tools/movenc.py(벌크 슬래시) — 바뀐 키 구간만 cinepak 재굽기, 구간마다 원래 바이트 이하 → work/build/files/DE_C0?00.CPK
  python tools/moviebox_ex.py [0200 …] [--noenc]   미리보기 = work/gfx/prev_movie_<번호>.png (원본|한글 3장)
"""
import os, sys, glob, shutil, subprocess, tempfile
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import gfxjob as GJ

FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'
DISC = os.path.join(ROOT, 'work', 'disc0'); OUT = os.path.join(ROOT, 'work', 'build', 'files')
# 번호: (지울 범위 x0, y0, x1, y1, 왼쪽 x, 제목 위 y, 첫 줄 위 y, 줄 간격, 제목, [줄…])
MOVIES = {
    '0200': (193, 161, 319, 224, 197, 165, 179, 11, '205계', ['대도시 통근형 전차.', '경량 스테인리스 차체', '볼스터리스 대차 장착.']),
    '0300': (4, 148, 138, 224, 8, 151, 165, 12, '209계', ['신형 통근형 전차.', 'FRP 마스크가 특징.', '비용 절반·수명 절반을', '콘셉트로 개발.', 'VVVF 인버터 탑재']),
    '0400': (183, 10, 312, 86, 185, 12, 27, 12, '221계', ['신예 근교형 전차.', '전환 크로스시트의', '어메니티 라이너.', '1990년도 로렐상', '수상.']),
    '0500': (183, 10, 312, 86, 185, 12, 27, 12, '키하58계', ['비전화 구간의 스타.', '디젤 엔진 2기 탑재.', '힘찬 엔진음을 울리며', '전국 각지에서 활약.']),
}
FRAMES = range(3, 67)          # 1부터 — 상자 나오는 프레임


def inpaint(a, m):
    a = a.astype(float); m = m.copy()
    while m.any():
        k = ~m; s = np.zeros_like(a); c = np.zeros(m.shape)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            ks = np.roll(np.roll(k, dy, 0), dx, 1); s += np.roll(np.roll(a, dy, 0), dx, 1) * ks[..., None]; c += ks
        f = m & (c > 0)
        if not f.any(): break
        a[f] = s[f] / c[f][:, None]; m &= ~f
    return a


def draw(a, x, y, t, f, col):
    lay, total = GJ.layout(t, f); gh = max(g.shape[0] for _, _, g in lay)
    for dx, dy, c in ((1, 1, None), (0, 0, col)):                                  # 오른쪽 아래 1px 그림자(배경 0.35배) 먼저
        for ch, gx, g in lay:
            sub = a[y + dy + gh - g.shape[0]:y + dy + gh, x + dx + gx:x + dx + gx + g.shape[1]]; m = g[:sub.shape[0], :sub.shape[1]] > 0
            sub[m] = sub[m] * 0.35 if c is None else c
    return total


def frame(img, spec):
    x0, y0, x1, y1, lx, ty, ly, pitch, title, lines = spec
    a = np.asarray(img.convert('RGB')).astype(float); reg = a[y0:y1, x0:x1]
    mn = reg.min(2)
    if (mn > 150).sum() < 20: return None                                          # 상자 없음
    col = np.percentile(reg[mn > 150], 90, axis=0)                                # 원래 글자 밝기(페이드인)
    m = mn > min(150, np.median(mn) + 45)                                         # 바탕보다 꽤 밝은 화소 = 글자(번진 가장자리 포함)
    mm = m.copy()
    for _ in range(2): mm = mm | np.roll(mm, 1, 0) | np.roll(mm, -1, 0) | np.roll(mm, 1, 1) | np.roll(mm, -1, 1)
    a[y0:y1, x0:x1] = inpaint(reg, mm)
    for x, y, t, f in [(lx, ty, title, 'B')] + [(lx, ly + pitch * i, t, 'G9') for i, t in enumerate(lines)]:
        w = draw(a, x, y, t, f, col); assert x + w <= x1 + 1, ('넘침', t, x + w, x1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main(nums, enc=True):
    import movenc
    os.makedirs(OUT, exist_ok=True)
    for n in nums:
        spec = MOVIES[n]; src = os.path.join(DISC, 'DE_C%s.CPK' % n)
        tmp = tempfile.mkdtemp(prefix='dexmv_'); fr = os.path.join(tmp, 'fr'); kr = os.path.join(tmp, 'kr'); os.makedirs(fr); os.makedirs(kr)
        try:
            subprocess.run([FF, '-v', 'error', '-i', src, '-fps_mode', 'passthrough', os.path.join(fr, 'f%04d.png')], check=True)
            shots = []
            for i in FRAMES:
                im = Image.open(os.path.join(fr, 'f%04d.png' % i)); new = frame(im, spec)
                if new is None: continue
                new.save(os.path.join(kr, 'f%04d.png' % i))
                if i in (6, 35, 66): shots.append(np.concatenate([np.asarray(im.convert('RGB')), np.full((224, 4, 3), 255, np.uint8), np.asarray(new)], 1))
            Image.fromarray(np.concatenate(shots, 0)).save(os.path.join(ROOT, 'work', 'gfx', 'prev_movie_%s.png' % n))
            if enc:
                movenc.TMP = os.path.join(tmp, '_gop'); movenc.STRIPS = 2
                movenc.reencode(src, fr, kr, os.path.join(OUT, 'DE_C%s.CPK' % n), os.path.getsize(src))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args or list(MOVIES), '--noenc' not in sys.argv)
