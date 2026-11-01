# -*- coding: utf-8 -*-
r"""VDP2 그림 형식(tools/v2img.py) «아틀라스» 글자 고치기 공용(2026-10-31)
  Atlas(바이트) → .can (맵대로 펼친 색인 그림, 2워드 8×8 / 1워드 16×16) · .find(모양) · .erase() · .put() · .save() → 새 바이트
  다시 싸기: 맵 칸마다 원하는 8×8(뒤집기 되돌려서) 모음 → 셀마다 모든 사용처가 같으면 제자리 덮기,
             다르면 «원래 그대로인 사용처»에 원래 셀을 남기고 나머지는 새 셀을 뒤에 붙임(기존 셀 번호 불변).
  글자 지우기: 글자 속 색(fill) 화소 + 그 8방향 1px 안의 테두리 색(ring) 화소 → 2칸 주기 바탕(바둑판·막대)에서 메움.
"""
import struct
import numpy as np
import v2img


class Atlas:
    def __init__(self, d):
        self.d = bytes(d); H = self.H = v2img.parse(d)
        assert H, '그림 형식 아님'
        self.one = bool(H['one'])
        c = d[H['cell']:H['cell'] + H['cellsz']]
        self.cells = np.frombuffer(c, np.uint8).reshape(-1, 8, 8).copy()
        mp = d[H['map']:H['map'] + H['mapsz']]
        self.ents = []                                   # (화면 x, y, 셀 번호들[(셀, 좌우, 상하)])
        if self.one:
            n = len(mp) // 2; W = 32
            for k in range(n):
                v = struct.unpack_from('>H', mp, k * 2)[0]
                self.ents.append(('1', k, v))
            self.can = np.zeros(((n + W - 1) // W * 16, W * 16), np.uint8)
        else:
            n = len(mp) // 4; W = 64
            for k in range(n):
                w0, w1 = struct.unpack_from('>HH', mp, k * 4)
                self.ents.append(('2', k, (w0, w1)))
            self.can = np.zeros(((n + W - 1) // W * 8, W * 8), np.uint8)
        self.W = W
        for blk, (x, y), (ci, hf, vf) in self.blocks():
            if ci < len(self.cells):
                self.can[y:y + 8, x:x + 8] = self._flip(self.cells[ci], hf, vf)
        self.orig = self.can.copy()

    @staticmethod
    def _flip(px, hf, vf):
        if hf: px = px[:, ::-1]
        if vf: px = px[::-1]
        return px

    def blocks(self):
        """→ [(맵 칸 번호·부분, (x, y), (셀, 좌우, 상하))] 8×8 단위"""
        out = []
        for kind, k, v in self.ents:
            if kind == '2':
                w0, w1 = v; x, y = k % 64 * 8, k // 64 * 8
                out.append(((k, 0), (x, y), ((w1 & 0x7FFF) // 2, w0 >> 14 & 1, w0 >> 15 & 1)))
            else:
                base = (v & 0x3FF) * 2; hf, vf = v >> 10 & 1, v >> 11 & 1   # ★글자 번호 × 0x80 바이트 = 64B 셀 2개 단위(v2img 와 같음)
                X, Y = k % 32 * 16, k // 32 * 16
                order = [(0, 0), (8, 0), (0, 8), (8, 8)]
                for j, (dx, dy) in enumerate(order):
                    # 뒤집힌 16×16 글자 안에서 셀 j 가 놓이는 자리
                    px = (8 - dx) if hf else dx; py = (8 - dy) if vf else dy
                    out.append(((k, j), (X + px, Y + py), (base + j, hf, vf)))
        return out

    # ── 찾기 ─────────────────────────────────────────────
    def find(self, tmpl, color=None):
        """tmpl = bool 배열(글자 속 모양) → [(x, y, 색)] — color 없으면 첫 속 화소 색으로"""
        h, w = tmpl.shape; C = self.orig                     # ★원본에서 찾기(앞 작업이 고친 그림이 검색을 방해하지 않게)
        fy, fx = np.argwhere(tmpl)[0]; pts = np.argwhere(tmpl); neg = np.argwhere(~tmpl)
        Hh, Ww = C.shape[0] - h + 1, C.shape[1] - w + 1
        A = C[fy:fy + Hh, fx:fx + Ww]
        ok = (A != 0) if color is None else (A == color)
        for (y, x) in pts: ok &= C[y:y + Hh, x:x + Ww] == A
        for (y, x) in neg: ok &= C[y:y + Hh, x:x + Ww] != A
        return [(int(x), int(y), int(A[y, x])) for y, x in np.argwhere(ok)]

    # ── 지우기·그리기 ────────────────────────────────────
    def glyph_mask(self, x, y, w, h, fill, ring):
        r = self.can[y:y + h, x:x + w]
        f = np.isin(r, list(fill))
        p = np.pad(f, 1); near = np.zeros_like(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= np.roll(np.roll(p, dy, 0), dx, 1)
        near = near[1:-1, 1:-1]
        return f | (near & np.isin(r, list(ring)))

    def erase(self, x, y, w, h, fill, ring, mask=None):
        """글자 화소를 2칸 주기 바탕으로 메움(바둑판·막대 무늬 유지)"""
        m = self.glyph_mask(x, y, w, h, fill, ring) if mask is None else mask
        if mask is None and x % 8 == 0 and y % 8 == 0 and w % 8 == 0 and h % 8 == 0:
            for by in range(0, h, 8):                    # ★8×8 셀 단위로 따로 메움 — 셀이 여러 사본에 공유돼도 결과 같음
                for bx in range(0, w, 8):
                    sub = m[by:by + 8, bx:bx + 8]
                    if sub.any(): self.erase(x + bx, y + by, 8, 8, fill, ring, mask=sub.copy())
            return m
        reg = self.can[y:y + h, x:x + w]                 # ★칸 안 화소만 참고 — 같은 원본 칸은 언제나 같은 결과(셀 공유 깨지 않음)
        todo = sorted((int(a), int(b)) for a, b in np.argwhere(m)); bad = set(todo)
        cand = [(2, 0), (-2, 0), (4, 0), (-4, 0), (6, 0), (-6, 0),          # (dy, dx) 위아래 먼저 — 막대·띠는 세로로 같은 무늬
                (0, 2), (0, -2), (2, 2), (-2, -2), (2, -2), (-2, 2), (0, 4), (0, -4), (4, 4), (-4, -4), (0, 6), (0, -6)]
        for _ in range(16):
            if not todo: break
            nxt = []; upd = {}
            for (yy, xx) in todo:
                got = []                                  # 2칸 주기 이웃 후보 앞 6개 다수결(같으면 앞선 후보) — 띠 가장자리에서 엉뚱한 무늬 막기
                for dy, dx in cand:
                    Y, X = yy + dy, xx + dx
                    if 0 <= Y < h and 0 <= X < w and (Y, X) not in bad:
                        got.append(int(reg[Y, X]))
                        if len(got) == 6: break
                if got:
                    cnt = {}
                    for g in got: cnt[g] = cnt.get(g, 0) + 1
                    upd[(yy, xx)] = max(got, key=lambda g: (cnt[g], -got.index(g)))
                else:
                    nxt.append((yy, xx))
            for (yy, xx), val in upd.items(): reg[yy, xx] = val; bad.discard((yy, xx))
            todo = nxt
        for (yy, xx) in todo: reg[yy, xx] = 0
        return m

    def erase_column(self, x, y, w, h, m, reach=24):
        """지울 화소를 «같은 열 위아래(2칸 주기, 셀 밖까지)»의 가장 가까운 안 지울 화소로 — 세로 띠·막대 가장자리용.
        고친 셀 목록을 돌려줌(셀 공유가 깨지면 save 전에 erase_cells 로 되돌릴 것)"""
        full = np.zeros(self.can.shape, bool); full[y:y + h, x:x + w] = m
        src = self.can.copy(); H_ = self.can.shape[0]; miss = []
        for yy, xx in np.argwhere(full):
            best = None
            for k in range(2, reach + 1, 2):
                for Y in (yy + k, yy - k):
                    if 0 <= Y < H_ and not full[Y, xx]: best = src[Y, xx]; break
                if best is not None: break
            if best is None: miss.append((yy, xx))
            else: self.can[yy, xx] = best
        return miss

    def refs(self):
        if not hasattr(self, '_refs'):
            import collections
            self._refs = collections.Counter(ci for _, _, (ci, _, _) in self.blocks())
            self._cellat = {(xx, yy): ci for _, (xx, yy), (ci, _, _) in self.blocks()}
        return self._refs, self._cellat

    def erase_mixed(self, x, y, w, h, m):
        """셀마다: 한 곳에서만 쓰이는 셀 = 열 메우기(셀 밖 위아래), 여러 곳 공유 셀 = 셀 안 메우기"""
        refs, at = self.refs()
        full = np.zeros(self.can.shape, bool); full[y:y + h, x:x + w] = m
        col = np.zeros_like(full)
        for by in range(y // 8 * 8, y + h, 8):
            for bx in range(x // 8 * 8, x + w, 8):
                sub = full[by:by + 8, bx:bx + 8]
                if not sub.any(): continue
                if refs[at[(bx, by)]] == 1: col[by:by + 8, bx:bx + 8] = sub
                else: self.erase(bx, by, 8, 8, None, None, mask=sub.copy())
        if col.any():
            ys, xs = np.nonzero(col); y0, x0 = ys.min(), xs.min()
            miss = self.erase_column(x0, y0, xs.max() - x0 + 1, ys.max() - y0 + 1, col[y0:ys.max() + 1, x0:xs.max() + 1])
            for yy, xx in miss: self.can[yy, xx] = 0

    def erase_cells(self, x, y, w, h, m):
        """임의 사각형의 지울 화소 m → 아틀라스 8×8 격자 셀마다 따로 메움(셀 공유 깨지 않음)"""
        full = np.zeros(self.can.shape, bool); full[y:y + h, x:x + w] = m
        for by in range(y // 8 * 8, y + h, 8):
            for bx in range(x // 8 * 8, x + w, 8):
                sub = full[by:by + 8, bx:bx + 8]
                if sub.any(): self.erase(bx, by, 8, 8, None, None, mask=sub.copy())

    def put(self, x, y, lv, fill, ring, keep_bg=True):
        """lv: 0 바탕 / 1 테두리 / 3 속 — fill 은 색 하나 또는 줄별 색 목록"""
        h, w = lv.shape; reg = self.can[y:y + h, x:x + w]
        for yy in range(h):
            fc = fill[yy] if isinstance(fill, (list, tuple)) else fill
            row = reg[yy]
            row[lv[yy] == 3] = fc
            row[lv[yy] == 1] = ring

    # ── 다시 싸기 ────────────────────────────────────────
    def save_one(self):
        """1워드(16×16 글자 = 셀 4개 묶음, 번호 v → 셀 2v…2v+3) 다시 싸기 — 묶음 단위로, 셀 수 그대로(빈 묶음 재활용)"""
        H = self.H; cells = [c.copy() for c in self.cells]; n0 = len(cells)
        mp = bytearray(self.d[H['map']:H['map'] + H['mapsz']])
        want = {}
        for kind, k, v in self.ents:
            base = (v & 0x3FF) * 2; hf, vf = v >> 10 & 1, v >> 11 & 1
            if base + 3 >= n0: continue
            X, Y = k % 32 * 16, k // 32 * 16
            blk = self.can[Y:Y + 16, X:X + 16]
            if hf: blk = blk[:, ::-1]
            if vf: blk = blk[::-1]
            q = [blk[0:8, 0:8], blk[0:8, 8:16], blk[8:16, 0:8], blk[8:16, 8:16]]
            want.setdefault(base, []).append((k, v, np.stack(q)))
        orig = lambda b: np.stack(self.cells[b:b + 4])
        assign = {}; extra = []
        for base, lst in want.items():
            vs = []
            for k, v, q in lst:
                for j, vq in enumerate(vs):
                    if np.array_equal(vq[0], q): vq[1].append((k, v)); break
                else:
                    vs.append([q, [(k, v)]])
            keep = next((j for j, vq in enumerate(vs) if np.array_equal(vq[0], orig(base))), 0)
            for i in range(4): cells[base + i] = vs[keep][0][i]
            for j, (q, users) in enumerate(vs):
                if j != keep: extra.append((q, users))
        self.added = 0
        if extra:
            content = {}
            for base in sorted(want):
                content.setdefault(np.stack(cells[base:base + 4]).tobytes(), base)
            used = set(want)
            free = [b for b in sorted(want) if content[np.stack(cells[b:b + 4]).tobytes()] != b]
            # ★묶음 번호는 셀 2개 단위라 이웃 묶음과 셀이 반씩 겹친다(2026-11-01 CFG_001 «아» 사라짐) → 남이 쓰는 셀과 안 겹치는 빈 묶음만 재활용
            occ = set()
            for b in want:
                if b not in free: occ.update(range(b, b + 4))
            free = [b for b in free if not occ.intersection(range(b, b + 4))]
            # 내용이 다른 묶음과 같아진 묶음 → 그 묶음으로 돌리고 비움
            redirect = {b: content[np.stack(cells[b:b + 4]).tobytes()] for b in free}; moved = set()
            for q, users in extra:
                b = q.tobytes()
                if b in content: tgt = content[b]
                elif free:
                    tgt = free.pop(0); [cells.__setitem__(tgt + i, q[i]) for i in range(4)]; content[b] = tgt
                    occ.update(range(tgt, tgt + 4)); free = [f for f in free if not occ.intersection(range(f, f + 4))]
                else:
                    tgt = len(cells); tgt += (-tgt) % 4; cells += [np.zeros((8, 8), np.uint8)] * (tgt - len(cells)) + [q[i] for i in range(4)]
                    content[b] = tgt; self.added += 4
                for k, v in users: struct.pack_into('>H', mp, k * 2, (v & ~0x3FF) | (tgt // 2)); moved.add(k)
            for kind, k, v in self.ents:                                     # 비운 묶음을 쓰던 칸 → 같은 내용 묶음으로
                base = (v & 0x3FF) * 2; cur = struct.unpack_from('>H', mp, k * 2)[0]
                if k not in moved and cur == v and base in redirect and redirect[base] != base:   # ★새 내용으로 옮긴 칸은 제외(빈 묶음 자리를 재활용해 번호가 같아도)
                    struct.pack_into('>H', mp, k * 2, (v & ~0x3FF) | (redirect[base] // 2))
        cb = b''.join(c.astype(np.uint8).tobytes() for c in cells)
        hd = bytearray(self.d[:H['cell']])
        struct.pack_into('>I', hd, 28, len(cb)); struct.pack_into('>I', hd, 40, H['cell'] + len(cb))
        out = bytes(hd) + cb + bytes(mp) + self.d[H['map'] + H['mapsz']:]
        chk = Atlas(out).orig; bad = int((chk != self.can[:chk.shape[0], :chk.shape[1]]).sum())
        assert bad == 0, ('다시 싸기 검산 실패(펼친 그림이 다름)', bad)
        return out

    def save(self):
        if self.one: return self.save_one()
        H = self.H; cells = [c for c in self.cells]; n0 = len(cells)
        want = {}
        bl = self.blocks()
        for key, (x, y), (ci, hf, vf) in bl:
            if ci >= n0: continue
            blk = self._flip(self.can[y:y + 8, x:x + 8], hf, vf)
            want.setdefault(ci, []).append((key, blk))
        remap = {}; extra = []                            # extra = (셀, 변형, 그 변형을 쓰는 키들) — 원래 자리에 못 둔 것
        for ci, lst in want.items():
            variants = []; users = []
            for key, blk in lst:
                for j, vb in enumerate(variants):
                    if np.array_equal(vb, blk): users[j].append(key); break
                else:
                    variants.append(blk.copy()); users.append([key])
            # 원래 셀 자리 = 원본과 같은 변형이 있으면 그것, 없으면 첫 변형
            orig = self.cells[ci]; keepj = next((j for j, vb in enumerate(variants) if np.array_equal(vb, orig)), 0)
            cells[ci] = variants[keepj]
            for key in users[keepj]: remap[key] = ci
            for j, vb in enumerate(variants):
                if j != keepj: extra.append((ci, vb, users[j]))
        if extra:
            # ★셀 늘리지 않기: 내용이 «다른 셀과 똑같아진» 셀은 그 셀로 합치고 자리를 비워 재활용
            content = {}
            for i in range(n0):
                content.setdefault(cells[i].tobytes(), i)
            free = []
            for i in range(n0):
                j = content[cells[i].tobytes()]
                if j != i and i in want:                 # i 의 모든 사용처를 j 로
                    for key, v in remap.items():
                        if v == i: remap[key] = j
                    free.append(i)
            for ci, vb, keys in extra:
                b = vb.tobytes()
                if b in content: tgt = content[b]
                elif free: tgt = free.pop(0); cells[tgt] = vb; content[b] = tgt
                else: tgt = len(cells); cells.append(vb); content[b] = tgt
                for key in keys: remap[key] = tgt
            self.freed_left = len(free)
        mp = bytearray(self.d[H['map']:H['map'] + H['mapsz']])
        for kind, k, v in self.ents:
            if kind == '2':
                w0, w1 = v; nc = remap.get((k, 0))
                if nc is not None: struct.pack_into('>HH', mp, k * 4, w0, (w1 & 0x8000) | nc * 2)
            else:
                ns = [remap.get((k, j)) for j in range(4)]
                if all(q is None for q in ns): continue
                base = (v & 0x3FF) * 2
                if ns == [base, base + 1, base + 2, base + 3]: continue
                raise RuntimeError('1워드 16×16 글자가 셀 4개 묶음을 깨야 함(칸 %d) — 따로 처리 필요' % k)
        cb = b''.join(c.astype(np.uint8).tobytes() for c in cells)
        self.added = len(cells) - n0
        hd = bytearray(self.d[:H['cell']])
        struct.pack_into('>I', hd, 28, len(cb)); struct.pack_into('>I', hd, 40, H['cell'] + len(cb))
        return bytes(hd) + cb + bytes(mp) + self.d[H['map'] + H['mapsz']:]
