# -*- coding: utf-8 -*-
r"""구간 팝업 시트(DR_B?2??.BIN 84장) 상자 뽑기·묶기(2026-10-31)
  상자 = 투명(0) 아닌 화소의 8방향 연결 덩어리(작은 틈 2px 메워 붙임) → 사각형 바이트로 «같은 상자» 묶음
  python tools/popup_scan.py → work/popup/boxes.json + work/popup/u_<번호>.png (고유 상자 그림)
"""
import os, sys, glob, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ
import cv2

FILES = sorted(glob.glob(os.path.join(ROOT, 'work', 'disc0', 'DR_B[1-9A]2??.BIN')))


def boxes(A):
    m = (A.can != 0).astype(np.uint8)
    m2 = cv2.dilate(m, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m2, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h = stats[i][:4]
        sub = m[y:y + h, x:x + w] & (lab[y:y + h, x:x + w] == i); ys, xs = np.nonzero(sub)
        if not len(ys): continue
        out.append((int(x + xs.min()), int(y + ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)))
    return out


if __name__ == '__main__':
    od = os.path.join(ROOT, 'work', 'popup'); os.makedirs(od, exist_ok=True)
    uniq = {}; rec = {}
    for f in FILES:
        d = open(f, 'rb').read(); A = atlas.Atlas(d); nm = os.path.basename(f)
        pal = np.frombuffer(d[0x40:0x240], '>u2')
        rec[nm] = []
        for (x, y, w, h) in boxes(A):
            reg = A.can[y:y + h, x:x + w]
            key = hashlib.md5(reg.tobytes() + pal[np.unique(reg)].tobytes() + str((w, h)).encode()).hexdigest()[:10]
            if key not in uniq:
                uniq[key] = dict(n=len(uniq), w=w, h=h, first=nm, at=(x, y), files=[])
                Image.fromarray(GJ.rgb(reg, d)).resize((w * 2, h * 2), Image.NEAREST).save(os.path.join(od, 'u_%03d.png' % uniq[key]['n']))
            uniq[key]['files'].append(nm); rec[nm].append((x, y, w, h, key))
    json.dump(dict(uniq=uniq, rec=rec), open(os.path.join(od, 'boxes.json'), 'w'), ensure_ascii=False)
    print('파일', len(FILES), '고유 상자', len(uniq))
    import collections
    print(collections.Counter(min(len(v['files']), 99) for v in uniq.values()).most_common(20))
