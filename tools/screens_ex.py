# -*- coding: utf-8 -*-
r"""메뉴·화면 그림(BIN 안 CHR 압축 그림 = v2img.embedded) 한글화(2026-11-01) — tools/rectjob.py 위에서
  JOBS[(파일, 오프셋)] = rectjob 작업 목록 · EXTRA[(파일, 오프셋)] = 추가 함수(로고 등)
  python tools/screens_ex.py [이름…] → work/gfx/prev_<파일>_<오프셋>.png (원본|한글)
  build(파일, 오프셋) → (풀린 원본, Atlas, 바꾼 곳, 새 풀린 바이트) — 되돌려 넣기는 나중(허락 후) CHR 재압축
"""
import os, sys, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import atlas, gfxjob as GJ, rectjob as RJ, v2img

DISC = os.path.join(ROOT, 'work', 'disc0')

JOBS = {
    ('GO_CONF', 0x3BC): [
        dict(r=(44, 193, 310, 213), t='승차해 주셔서 감사합니다.', k=255, f='G14B', a='c', s='shadow', minlum=15),
        dict(r=(0, 246, 292, 267), t='스타트 버튼을 눌러 주세요.', k=255, f='G14B', a='c', s='shadow', minlum=15, rc=9),
    ],
    ('GO_OVER', 0x52C): [
        dict(r=(4, 3, 94, 20), t='운 전 종 료', k=0, f='G14B', s='oring', minlum=25), dict(r=(99, 3, 190, 20), t='운 전 중 지', k=0, f='G14B', s='oring', minlum=25),
        dict(r=(9, 38, 95, 57), t='승 무 완 료', k=0, f='G14B', s='oring', minlum=25), dict(r=(107, 38, 191, 57), t='승 무 완 료', k=0, f='G14B', s='oring', minlum=25),
    ],
}


def logos(*xy):
    def f(A, e):
        import misc_ex
        for X, Y in xy: misc_ex.put_logo_any(A, e, X, Y)
        return [('로고', X, Y) for X, Y in xy]
    return f


# 설정 화면(CFG_000·CFG_001, 1워드 16×16) — 16px 줄 × 글자 덩어리(원본 잉크 범위 안). 영문(EXIT·UP·NORMAL…)·BGM/SE·GO! 는 그대로
CFG_LINES = [   # (x0, x1(포함), y, 한국어)
    (1, 94, 0, '사운드 출력'), (129, 190, 0, '스테레오'), (273, 350, 0, '마스콘증'),
    (0, 46, 16, '난이도'), (129, 191, 16, '모노럴'), (273, 351, 16, '마스콘감'),
    (1, 78, 32, '크레딧'), (129, 158, 32, '예'), (177, 221, 32, '아니요'), (273, 350, 32, '브레이크증'),
    (0, 95, 48, '게임 모드'), (273, 351, 48, '브레이크감'),
    (0, 47, 64, '남은거리'), (273, 366, 64, '비상브레이크'),
    (48, 93, 80, '테스트'), (272, 302, 80, '경적'),
    (32, 78, 96, '테스트'), (273, 317, 96, '테스트'),
    (1, 110, 112, '무비 테스트'), (273, 349, 112, '기본값'),
    (2, 61, 128, '리플레이'),
    (1, 111, 144, '세이브/로드'),
    (1, 127, 160, '키 컨피그'),   # 하스피: 한 줄로(원본 キー　コンフィグ 사이 넓은 틈 없이)
    (1, 30, 192, '본체'), (2, 95, 208, '카트리지'),
    (1, 125, 256, '로드할까요?'), (1, 125, 272, '세이브할까요?'), (145, 190, 272, '오마케'),
    (1, 46, 288, '취소'), (144, 191, 288, '전차로'),
    (0, 47, 304, '전차로'), (145, 250, 304, '오프닝1'),
    (145, 250, 320, '엔딩1'),
    (1, 110, 336, '로드했습니다'), (145, 254, 336, '오프닝2'),
    (1, 110, 352, '세이브했습니다'), (145, 254, 352, '엔딩2'),
    (1, 174, 368, '로드하지 못했습니다'), (1, 174, 384, '세이브하지 못했습니다'),
    (1, 94, 400, '로드 중입니다'), (1, 94, 416, '세이브 중입니다'),
    (1, 190, 432, '카트리지가 없습니다'), (1, 239, 448, '카트리지가 꽂혀 있지 않습니다'), (1, 254, 464, '카트리지가 연결되어 있지 않습니다'),
    (0, 95, 496, '전차로전차로'),
]


def cfg_jobs(name):
    d = open(os.path.join(DISC, name + '.BIN'), 'rb').read(); C = atlas.Atlas(d).orig; out = []
    fill, ring = {'CFG_000': (3, 192), 'CFG_001': (36, 196)}[name]                 # 000 흰 속·보라 테두리 / 001 분홍 속·보라 테두리
    for x0, x1, y, t in CFG_LINES:
        if not (C[y:y + 16, x0:x1 + 1] != 0).any(): continue                      # 이 시트에 없는 줄
        if name == 'CFG_001' and 400 <= y < 496: continue                                  # 001 아래쪽은 버튼 판(따로)
        g0 = x0 // 16 * 16; n = (x1 + 1 - g0 + 15) // 16                           # 원본 가나 = 16px 격자 → 같은 격자에 G14P(같은 글자 타일 재사용)
        need = sum(1 for c in t)
        while need > n and not (C[y:y + 16, g0 + 16 * n:g0 + 16 * (n + 1)] != 0).any() and g0 + 16 * (n + 1) <= 512:
            n += 1                                                                    # 오른쪽 빈 타일로 늘림(⚠ 게임이 복사하는 폭 확인 필요 — 보고서에 적음)
        if need <= n: out.append(dict(r=(g0, y, g0 + 16 * n, y + 16), t=t, k='T', a='l', f='G14P', fill=fill, rc=ring))
        else: out.append(dict(r=(x0, y, x1 + 1, y + 16), t=t, k='T', a='l', fill=fill, rc=ring))         # 칸 모자람 → 작은 꼴(격자 밖)
    return out


CFG_BIG = [   # 무지개 큰 글자(CFG_000) — 줄별 색 = 원본 밝은 색, 테두리 없음(원본도 없음)
    dict(r=(128, 180, 276, 204), t='무비 테스트', k='T', f='A9', s='plain', minlum=45, stretch=True, smooth=True, dense=True),
    dict(r=(336, 175, 480, 206), t='컨피그', k='T', f='B2', s='plain', minlum=30, stretch=True, smooth=True, dense=True),
    dict(r=(336, 206, 510, 240), t='키 컨피그', k='T', f='B2', s='plain', minlum=30, stretch=True, smooth=True, dense=True),
    dict(r=(338, 245, 424, 271), t='세이브', k='T', f='B2', s='plain', fill=[128] * 10 + [138] * 9 + [141] * 7),
    dict(r=(338, 277, 422, 303), t='로드', k='T', f='B2', s='plain', fill=[128] * 10 + [138] * 9 + [141] * 7),
    dict(r=(320, 463, 415, 496), t='오마케', k='T', f='B2', s='plain', minlum=30, stretch=True, smooth=True, dense=True),
]
JOBS[('CFG_000', 0)] = cfg_jobs('CFG_000') + CFG_BIG
# 노선 선택(GO_SEL @1195C, 1워드) — 128×112 칸 4×4: 사진 + 분홍 노선명(y+75~97) + 초록 등급(오른쪽 아래 55×20)
SEL_NAMES = [['산인본선', '산인본선', '케이힌토호쿠선', '케이힌토호쿠선'], ['토카이도본선', '토카이도본선', '야마노테선', '야마노테선'],
             ['산인본선', '산인본선', '토카이도본선', '토카이도본선'], ['케이힌토호쿠선', '케이힌토호쿠선', '야마노테선', '야마노테선']]


def _sel_green():
    e = dict(v2img.embedded(open(os.path.join(DISC, 'GO_SEL.BIN'), 'rb').read()))[0x1195C]; pal = np.frombuffer(e[0x40:0x240], '>u2').astype(int)
    return {c for c in range(1, 256) if (pal[c] >> 5 & 31) >= 16 and (pal[c] & 31) < 14 and (pal[c] >> 10 & 31) < 14}


def sel_boxes():
    """노선 선택(1195C) 칸 — (g, c, 이름 칸, 등급 칸, 이름, 등급, 맞춤). 모드 변경(273C)은 같은 칸을 옮겨 씀(게임에서 겹쳐 그려짐 → 똑같아야 함)"""
    out = []
    for g in range(4):
        for c in range(4):
            y = 112 * g; x = 128 * c
            nx1 = x + 112 if g == 2 and c < 2 else x + 128                               # 산인본선EX — EX 작은 글자는 그대로
            nx0 = x + 16 if g == 2 and c < 2 else x                                      # EX 판도 이름 자리는 보통 판과 같게(가운데 = x+32…): 겹쳐 그려짐(하스피 «산산인본선»)
            gy = y + 277 - 224 if g == 2 else y + 53                                     # LONG/EXTRA 아래 등급
            out.append((g, c, (nx0, y + 75, nx1, y + 98), (x + 72, gy, x + 128, gy + 20), SEL_NAMES[g][c],
                        '초급' if g == 0 and c < 2 else '상급', 'c'))
    return out


SEL_FONT = dict(f='G14B', s='ring')                                                     # 이름 — 두 그림 같은 꼴(하스피: 겹쳐 보이니 같아야, B15 는 1195C 새 셀 36)
SEL_GFONT = dict(f='B15', s='ring')                                                     # 등급


def sel_jobs():
    out = []
    for g, c, nb, gb, name, grade, a in sel_boxes():
        out.append(dict(SEL_FONT, r=nb, t=name, k=0, fill=12, rc=235, a=a))
        out.append(dict(SEL_GFONT, r=gb, t=grade, k=('F', SEL_GREEN), fill=237, rc=235))
    return out


SEL_GREEN = _sel_green()
JOBS[('GO_SEL', 0x1195C)] = sel_jobs()


def _colors(name, off, pred):
    e = dict(v2img.embedded(open(os.path.join(DISC, name + '.BIN'), 'rb').read()))[off] if off else open(os.path.join(DISC, name + '.BIN'), 'rb').read()
    pal = np.frombuffer(e[0x40:0x240], '>u2').astype(int)
    return {c for c in range(1, 256) if pred(pal[c] & 31, pal[c] >> 5 & 31, pal[c] >> 10 & 31)}


BLUE = lambda r, g, b: b >= 18 and r < 10 and g < 14
ORANGE = lambda r, g, b: r >= 24 and 8 <= g <= 26 and b < 8
GREENC = lambda r, g, b: g >= 16 and r < 14 and b < 14
JOBS[('GO_SEL', 0x1195C)] += [   # 아래 레버·패드 아이콘의 選択/決定
    dict(r=(68, 514, 123, 536), t='결정', k=('F', _colors('GO_SEL', 0x1195C, BLUE)), f='A9', s='oring', stretch=True, inpaint=True),
    dict(r=(8, 558, 64, 581), t='선택', k=('F', _colors('GO_SEL', 0x1195C, ORANGE)), f='A9', s='oring', stretch=True, inpaint=True),
    dict(r=(146, 550, 184, 566), t='선택', k=('F', _colors('GO_SEL', 0x1195C, ORANGE)), f='B', s='ring', stretch=True),
    dict(r=(198, 535, 234, 551), t='결정', k=('F', _colors('GO_SEL', 0x1195C, GREENC)), f='G11', s='ring', stretch=True),
]
# 모드 변경 화면(GO_SEL @273C, 1워드 2쪽 — inpaint 쓰면 새 셀 12 → 셀 안 메움으로 새 셀 0) — 같은 판 3벌(y 0·240·512): 노선명 4·등급 4 + 아래 모드 문구(앞 두 벌)
G273 = _colors('GO_SEL', 0x273C, lambda r, g, b: g >= 14 and r < 10 and b < 10)
P273 = _colors('GO_SEL', 0x273C, lambda r, g, b: r >= 12 and g < 6 and b >= 5 and r > b)
Y273 = _colors('GO_SEL', 0x273C, lambda r, g, b: r >= 16 and g >= 12 and b < 8)
def _mv(r, dx, dy):
    return (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy)


SEL_TO_273 = {0: 32, 2: -64}                                                            # 1195C 열 c → 273C x 차이(왼 +32, 오른 −64)
JOBS[('GO_SEL', 0x273C)] = [j for d3 in (0, 240, 512) for g, c, nb, gb, name, grade, a in sel_boxes() if g < 2 and c in SEL_TO_273
                            for j in (dict(SEL_FONT, r=_mv(nb, SEL_TO_273[c], (12 if g == 0 else 8) + d3), t=name, k=('F', P273), fill=251, rc=255, a=a, **({} if name == '토카이도본선' else {'inpaint': 1})),   # 지운 자리 주변 메움(토카이도본선은 새 셀 8 → 셀 안 메움)
                                      dict(SEL_GFONT, r=_mv(gb, SEL_TO_273[c], (12 if g == 0 else 8) + d3), t=grade, k=('F', G273), fill=164, rc=255))] + [
    dict(r=(44, 216, 306, 233), t='브레이크 좌우로 모드 변경', k=('F', Y273), f='G14B', s='ring', stretch=True),
    dict(r=(76, 455, 276, 473), t='L • R로 모드 변경', k=('F', Y273), f='G14B', s='ring', stretch=True)]
# 운전 설명(GO_SEL @22904, 1워드) — 위 상자 문구·끔·가속(역행) · 호를 따른 낱글자는 EXTRA_22904(comp_labels)
JOBS[('GO_SEL', 0x22904)] = [
    dict(r=(10, 9, 119, 38), t='브레이크', k='M', f='B2', s='plain', minlum=40, stretch=True, dense=True, smooth=True),
    dict(r=(138, 9, 246, 31), t='마스콘', k='M', f='B2', s='plain', minlum=40, stretch=True, dense=True, smooth=True),
    dict(r=(142, 30, 241, 43), t='(액셀)', k='M', f='B', s='oring', minlum=25),
    dict(r=(3, 54, 237, 74), t='브레이크는 8단계입니다', k=255, f='G14B', s='oring', minlum=25, a='l'),
    dict(r=(3, 86, 237, 105), t='레버를 당기면 가속합니다', k=255, f='G14B', s='oring', minlum=25, a='l'),
    dict(r=(3, 105, 237, 122), t='(가속 중에는 브레이크 해제)', k=255, f='G14B', s='plain', minlum=25),
    dict(r=(330, 129, 362, 149), t='끔', k=255, f='A9', s='plain', fill=227),
    dict(r=(320, 236, 372, 256), t='가속', k='T', f='A9', s='oring', fill=244),
    dict(r=(316, 255, 376, 272), t='(역행)', k='T', f='G14B', s='oring', fill=244),
]
# 금속판 제목(操作説明 @20C2C) — 판 회색(9) 위 밝은 금속 글자 + 어두운 그림자
PLATE = dict(k=9, f='B2', s='shadow', rc=4, minlum=45, stretch=True)
JOBS[('GO_SEL', 0x20C2C)] = [dict(PLATE, r=(44, 25, 179, 55), t='조작설명')]
JOBS[('GO_SEL', 0x28B30)] = [dict(PLATE, r=(44, 25, 179, 55), t='운전설명')]
JOBS[('GO_SEL', 0x2F244)] = [dict(PLATE, r=(109, 19, 244, 50), t='운전설명')]
JOBS[('GO_SEL', 0x31C30)] = [dict(PLATE, r=(109, 26, 244, 57), t='출발점검', k='M')]
# 운전 설명 패드판(GO_SEL @28B30) — 위 상자 문구 = @22904 첫 6개를 아래로 240, 둘째 줄만 «버튼» · 버튼 판 = CFG_001 을 위로 32
def _shift(j, dy):
    x0, y0, x1, y1 = j['r']; return dict(j, r=(x0, y0 + dy, x1, y1 + dy))


JOBS[('GO_SEL', 0x28B30)] += [dict(_shift(j, 240), k='T') if j['k'] == 255 else _shift(j, 240) for j in JOBS[('GO_SEL', 0x22904)][:6]]
JOBS[('GO_SEL', 0x28B30)][-2] = dict(JOBS[('GO_SEL', 0x28B30)][-2], t='버튼을 누르면 가속합니다')
# 운전 그래프(@2F244)·설명 글(@30C60)·출발점검 문장(@31C30)
JOBS[('GO_SEL', 0x2F244)] += [
    dict(r=(58, 82, 122, 98), t='가 속', k='M', f='B', s='plain'), dict(r=(146, 82, 210, 98), t='타 행', k='M', f='B', s='plain'),
    dict(r=(234, 82, 298, 98), t='제 동', k='M', f='B', s='plain'),
    dict(r=(31, 124, 55, 145), t='속', k='M', f='A9', s='plain', minlum=15), dict(r=(31, 145, 55, 167), t='도', k='M', f='A9', s='plain', minlum=15),
    dict(r=(202, 172, 247, 191), t='거리', k='M', f='A9', s='plain', minlum=15)]
JOBS[('GO_SEL', 0x30C60)] = [dict(dict(k='M', f='G14B', s='plain', minlum=15, a='l'), r=r, t=t) for r, t in (
    ((0, 0, 254, 16), '마스콘을 풀노치 투입'), ((0, 16, 170, 32), '단숨에 가속합니다'), ((14, 32, 234, 48), '브레이크로 감속·정지'),
    ((0, 48, 234, 64), '비상브레이크는 감점 대상'), ((0, 64, 234, 80), '마스콘「끔」타력주행'))] + [
    dict(r=(6, 96, 58, 112), t='가 속', k='M', f='G14B', s='plain'), dict(r=(6, 112, 58, 128), t='타 행', k='M', f='G14B', s='plain'),
    dict(r=(6, 128, 58, 144), t='제 동', k='M', f='G14B', s='plain')]
JOBS[('GO_SEL', 0x31C30)] += [dict(r=(62, 172, 306, 191), t='각 레버를 스타트 위치에', k='M', f='G14B', s='plain', minlum=15, a='l'),
                              dict(r=(62, 191, 306, 209), t='맞춰 주세요.', k='M', f='G14B', s='plain', minlum=15, a='l')]
# 이름 등록 글자판(GO_NAME @5464·@F078 = GO_RANK @5200) — 셋째 줄 칸(속 13×12, 16px 간격): キハ…サロ = 차종 기호 → 갈무리7 두 글자, 系→계, 終→끝
def name_tiles(blk, white):
    out = [dict(r=(66 + 16 * i, 34, 79 + 16 * i, 46), t=t, k=blk, f='G7', s='plain', fill=white) for i, t in enumerate(('키하', '사하', '쿠하', '모하', '쿠로', '키로', '사로'))]
    return out + [dict(r=(178, 34, 191, 46), t='계', k=blk, f='G11', s='plain', fill=white), dict(r=(226, 34, 239, 46), t='끝', k=blk, f='G11', s='plain', fill=white)]


PLATE_RAMP = [184, 104, 184, 150, 129, 140, 140, 184, 129, 140, 140, 140, 184, 230, 167]   # 토카이도본선 줄 색(15행) — 네 노선·계 같은 색(산인본선만 흐리던 것)
LINE_PLATES = [   # @F078 아래 노선 판(돋을새김 회색) — 노선명 + 系
    dict(r=(4, 49, 92, 64), t='토카이도본선', k='M', f='G11', s='shadow', minlum=40), dict(r=(150, 49, 171, 64), t='계', k='M', f='B', s='shadow', minlum=40),
    dict(r=(4, 65, 92, 80), t='케이힌토호쿠선', k='M', f='G11', s='shadow', minlum=40), dict(r=(150, 65, 171, 80), t='계', k='M', f='B', s='shadow', minlum=40),
    dict(r=(18, 81, 88, 96), t='산인본선', k='M', f='G11', s='shadow', minlum=40), dict(r=(137, 81, 160, 96), t='계', k='M', f='B', s='shadow', minlum=40),
    dict(r=(18, 97, 88, 112), t='야마노테선', k='M', f='G11', s='shadow', minlum=40), dict(r=(137, 97, 160, 112), t='계', k='M', f='B', s='shadow', minlum=40),
]
JOBS[('GO_NAME', 0x5464)] = name_tiles(151, 1)
JOBS[('GO_NAME', 0xF078)] = name_tiles(254, 253) + LINE_PLATES
JOBS[('GO_RANK', 0x5200)] = name_tiles(254, 253) + LINE_PLATES
# 이름 등록 판(GO_NAME @2408 레버판 · @78AC 패드판)
def _nm_colors(off, pred):
    return _colors('GO_NAME', off, pred)


NAME_COMMON = [dict(r=(141, 24, 229, 39), t='남은시간', k='M', f='B', s='plain', minlum=15),
               dict(r=(215, 40, 238, 60), t='초', k='M', f='A9', s='plain', minlum=40),
               dict(r=(45, 74, 152, 98), t='이름등록', k='M', f='B2', s='plain', minlum=15, stretch=True)]
BLUE_OR_CYAN = lambda r, g, b: b >= 18 and r < 10
ORANGE2 = lambda r, g, b: r >= 12 and r // 5 <= g <= r and b <= 8     # 주황 + 어두운 주황 가장자리
JOBS[('GO_NAME', 0x2408)] = NAME_COMMON + [
    dict(r=(173, 64, 232, 87), t='결정', k=('F', _nm_colors(0x2408, BLUE_OR_CYAN)), f='B2', s='ring', stretch=True, inpaint=2),
    dict(r=(231, 99, 292, 123), t='선택', k=('F', _nm_colors(0x2408, ORANGE2)), f='B2', s='ring', stretch=True, inpaint=2)]
JOBS[('GO_NAME', 0x78AC)] = NAME_COMMON + [
    dict(r=(251, 81, 310, 105), t='결정', k=('F', _nm_colors(0x78AC, BLUE_OR_CYAN)), f='B2', s='ring', stretch=True, inpaint=2),
    dict(r=(180, 134, 244, 160), t='선택', k=('F', _nm_colors(0x78AC, ORANGE2)), f='B2', s='ring', stretch=True, inpaint=2)]
# 전용 컨트롤러 검사 모드(MSC_TES1, 통째 그림 1워드 2쪽) — 판 2열(x 0·256) × 8단(y 128k), 줄 = 원본 줄 자리, 흰 글자 한 색
def _tes(btn):
    return ['하늘색으로 깜박이는', btn + ('을' if btn[-1] in '튼' else '를'), '눌러 주세요.']


def _pos(lever, n):
    return ['하늘색으로 깜박이는', '%s:%s' % (lever, n), '위치에 맞춰 주세요.']


TES_PANELS = {(0, 0): None, (0, 1): _tes('SELECT'), (1, 0): _tes('B 버튼'), (1, 1): _tes('C 버튼'),
              (2, 0): _pos('마스콘', '3'), (2, 1): _pos('마스콘', '4'), (3, 0): _pos('브레이크', '2'), (3, 1): _pos('브레이크', '3'),
              (4, 0): _tes('START'), (4, 1): _tes('A 버튼'), (5, 0): _pos('마스콘', '1'), (5, 1): _pos('마스콘', '2'),
              (6, 0): _pos('마스콘', '5'), (6, 1): _pos('마스콘', '끔'), (7, 0): _pos('브레이크', '4'), (7, 1): _pos('브레이크', '5')}
TES_FIRST = ['검사에 합격했습니다.', '검사 시작은 A 버튼과', 'START를 동시에 눌러', '주세요.마스콘은 끔으로', '되돌리고,브레이크는 1로', '해 주세요.']


def tes_jobs():
    out = []
    for (k, side), lines in TES_PANELS.items():
        x0 = 256 * side; y0 = 128 * k
        if lines is None: rows, lines = [19, 37, 56, 74, 91, 110], TES_FIRST
        else: rows = [30, 48, 66]
        for yy, t in zip([1] + rows, ['검사 모드'] + lines):
            out.append(dict(r=(x0 + 3, y0 + yy - 1, x0 + 254, y0 + yy + 17), t=t, k=0, f='G14', s='plain', fill=2, a='l'))
    return out


JOBS[('MSC_TES1', 0)] = tes_jobs()
# 승객 그림(DR_B?X00.SZ3 항목 004, 다섯 노선 같은 바이트) — 빨간 띠 急制動 4벌(y 260+64k) → 급제동
JOBS[('DR_B1X00.SZ3/004.bin', 0)] = [dict(r=(424, 260 + 64 * k, 495, 276 + 64 * k), t='급 제 동', k=16, f='G14B', s='plain', fill=15) for k in range(4)]
# 컨트롤러 선택(CTRL, 1워드) — 흰 글자 + 어두운 테두리, 스타트 = 분홍 · A - C 는 그대로
JOBS[('CTRL', 0)] = [dict(dict(r=r, t=t, k=0, fill=84, rc=131, f='G14', s='oring', a='l'), **kw) for r, t, kw in (
    ((2, 1, 141, 17), '세가새턴', {'a': 'c'}), ((2, 17, 141, 32), '컨트롤 패드', {'a': 'c'}), ((2, 40, 92, 58), '마스콘', {'f': 'G14B', 'a': 'c'}),
    ((2, 64, 86, 80), '스타트', {'fill': 116, 'a': 'r'}), ((86, 64, 221, 80), '버튼으로 결정', {'a': 'l'}), ((86, 80, 221, 96), '버튼으로 선택', {'a': 'l'}),
    ((2, 97, 314, 112), '컨트롤러를 선택해 주세요.', {'a': 'l'}))]


def movie_tail(A, e):
    """ムービーテスト 아래 끝(행 204~208)이 Option 윗줄과 겹침 — 초록·파랑 쪽 화소만 지움(Option 윗줄은 빨강)"""
    pal = np.frombuffer(e[0x40:0x240], '>u2').astype(int); reg = A.can[204:209, 128:276]
    r, g, b = pal[reg] & 31, pal[reg] >> 5 & 31, pal[reg] >> 10 & 31
    reg[(reg != 0) & ((g > r) | (b > r))] = 0
    return []


JOBS[('CFG_001', 0)] = cfg_jobs('CFG_001')
def transplant(A, e, src_build, region=None, tol=24):
    """다른 그림에서 하스피 통과한 바꿈(원본→새)을 이 그림의 «비슷한 RGB 원본 조각»에 옮겨 심기(팔레트가 조금 달라도).
    색 대응 = 같은 자리 원본 색끼리(다수결), 원본에 없던 새 색 = 가장 가까운 팔레트 색"""
    d2, A2 = src_build()[:2]
    o2 = GJ.rgb(A2.orig, d2).astype(int); n2 = GJ.rgb(A2.can, d2).astype(int); o1 = GJ.rgb(A.orig, e).astype(int)
    pal = np.frombuffer(e[0x40:0x240], '>u2').astype(int)
    rgbpal = np.stack([(pal & 31) << 3, (pal >> 5 & 31) << 3, (pal >> 10 & 31) << 3], -1)
    ry0, ry1, rx0, rx1 = region or (0, o1.shape[0], 0, o1.shape[1])
    ch = A2.orig != A2.can; m = ch.copy()
    p = np.pad(m, 1); m = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | m
    boxes = []; seen_px = np.zeros_like(m)
    for sy, sx in zip(*np.nonzero(m)):
        if seen_px[sy, sx]: continue
        st = [(sy, sx)]; seen_px[sy, sx] = True; ys = [sy]; xs = [sx]
        while st:
            y, x = st.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not seen_px[yy, xx]:
                    seen_px[yy, xx] = True; st.append((yy, xx)); ys.append(yy); xs.append(xx)
        boxes.append((min(ys), max(ys) + 1, min(xs), max(xs) + 1))
    done = []; seen = set(); used = np.zeros(A.orig.shape, bool)
    for y0, y1, x0, x1 in boxes:
        T = o2[y0:y1, x0:x1]; N = n2[y0:y1, x0:x1]; H, W = T.shape[:2]
        if H * W < 12 or T.tobytes() in seen: continue
        seen.add(T.tobytes()); To = A2.orig[y0:y1, x0:x1]; Tn = A2.can[y0:y1, x0:x1]
        for y in range(ry0, ry1 - H + 1):
            for x in range(rx0, rx1 - W + 1):
                if used[y, x]: continue
                err = np.abs(o1[y:y + H, x:x + W] - T).mean()
                if err > tol: continue
                O = A.orig[y:y + H, x:x + W]; mp = {}
                for a_, b_ in zip(To.ravel().tolist(), O.ravel().tolist()): mp.setdefault(a_, collections.Counter())[b_] += 1
                mp = {k: v.most_common(1)[0][0] for k, v in mp.items()}
                cur = A.can[y:y + H, x:x + W]
                for yy, xx in zip(*np.nonzero(To != Tn)):
                    c = int(Tn[yy, xx])
                    cur[yy, xx] = mp[c] if c in mp else int(np.argmin(((rgbpal - N[yy, xx]) ** 2).sum(-1)))
                used[y:y + H, x:x + W] = True; done.append(('옮김', x, y))
    return done


def bubble(lines, box, bg, cols):
    """말풍선 줄 다시 쓰기 — box(x0,x1) 안 줄 범위의 바탕 아닌 화소 지우고 {g:…}{r:…} 색 구간 그림.
    lines = [(y0, y1, x0, 꼴, 문장)] · cols = {'k': 검정, 'g': 초록, 'r': 빨강}"""
    def f(A, e):
        import re
        bx0, bx1 = box
        for y0, y1, x0, fn, t in lines:
            r = A.can[y0:y1, bx0:bx1]; r[(r != bg) & (r != 0)] = bg
        for y0, y1, x0, fn, t in lines:
            segs = [(k, txt) for k, txt in ((m.group(1) or 'k', m.group(2) if m.group(1) else m.group(4)) for m in re.finditer(r'\{(\w):([^}]*)\}|()([^{]+)', t))]
            plain = ''.join(x for _, x in segs); flags = [k for k, x in segs for c in x if c != ' ']
            lay, total = GJ.layout(plain, fn); assert x0 + total <= bx1, ('넘침', t, total)
            gh = max(g.shape[0] for _, _, g in lay); yy = y0 + (y1 - y0 - gh) // 2
            for n, (ch, gx, g) in enumerate(lay):
                sub = A.can[yy + gh - g.shape[0]:yy + gh, x0 + gx:x0 + gx + g.shape[1]]; sub[g > 0] = cols[flags[n]]
        return [('말풍선', box[0], lines[0][0])]
    return f


def comp_labels(items, maxsize=900, kill_boxes=()):
    """흩어진 낱글자(호를 따라 놓인 常用ブレーキ 등) 바꾸기 — 상자 안 «작은 연결 덩어리»(큰 그림과 안 붙은 글자)만 지우고(바탕 0)
    그 덩어리의 주된 색 + 검정 테두리로 상자 가운데에 다시 그림. items = [(x0, y0, x1, y1, 글자, 꼴)] — 먼저 전부 지우고 나서 그림"""
    def f(A, e):
        C = A.orig; H, W = C.shape; nz = C != 0; seen = np.zeros_like(nz); fills = []
        for x0, y0, x1, y1, t, fn in items:
            cols = collections.Counter()
            for sy, sx in zip(*np.nonzero(nz[y0:y1, x0:x1])):
                sy += y0; sx += x0
                if seen[sy, sx]: continue
                st = [(sy, sx)]; seen[sy, sx] = True; comp = [(sy, sx)]
                while st and len(comp) <= maxsize:
                    y, x = st.pop()
                    for yy in (y - 1, y, y + 1):
                        for xx in (x - 1, x, x + 1):
                            if 0 <= yy < H and 0 <= xx < W and nz[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True; st.append((yy, xx)); comp.append((yy, xx))
                if len(comp) <= maxsize:
                    for y, x in comp: A.can[y, x] = 0; cols[int(C[y, x])] += 1
            cols.pop(255, None)
            if not cols:                                                              # 덩어리를 앞 상자가 이미 가져감 → 상자 안 원본 색
                r = C[y0:y1, x0:x1]; cols = collections.Counter(r[(r != 0) & (r != 255)].tolist())
            pal = np.frombuffer(e[0x40:0x240], '>u2').astype(int); lum = lambda c: (pal[c] & 31) + (pal[c] >> 5 & 31) + (pal[c] >> 10 & 31)
            br = collections.Counter({c: n for c, n in cols.items() if lum(c) >= 30}) or cols                # 밝은 색 우선(갈색 가장자리 말고)
            fills.append(br.most_common(1)[0][0] if br else None)
        for x0, y0, x1, y1 in kill_boxes:                                                # 큰 그림에 붙은 잔획(ブ 의 탁점)
            r = A.can[y0:y1, x0:x1]; r[...] = 0
        last = None; done = []
        for (x0, y0, x1, y1, t, fn), fill in zip(items, fills):
            fill = fill if fill is not None else last; last = fill
            lv = GJ.word(t, x1 - x0 + 2, y1 - y0 + 2, fn, 'oring')
            A.put(x0 - 1, y0 - 1, lv, fill, 255); done.append((t, x0, y0))
        return done
    return f


def sel_specks(A, e):
    """노선 선택 등급 칸: 새 글자에 안 붙은 초록 잔점(원래 級 끄트머리) → 옆 비초록 화소로(하스피 «상급 오른쪽 찌꺼기점»)"""
    n = 0
    for g, c, nb, gb, *_ in sel_boxes():
        x0, y0, x1, y1 = gb; r = A.can[y0 + 1:y1, x0:x1]                             # LONG·EXTRA(칸 위·왼쪽 작은 글자)는 건드리지 않음
        gm = np.isin(r, list(SEL_GREEN)); seen = np.zeros_like(gm)
        for sy, sx in zip(*np.nonzero(gm)):
            if seen[sy, sx]: continue
            st = [(sy, sx)]; seen[sy, sx] = True; comp = [(sy, sx)]
            while st:
                y, x = st.pop()
                for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= yy < gm.shape[0] and 0 <= xx < gm.shape[1] and gm[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; st.append((yy, xx)); comp.append((yy, xx))
            if len(comp) <= 8:
                for y, x in comp:
                    alt = [r[y, xx] for xx in (x - 3, x + 3, x - 4, x + 4) if 0 <= xx < r.shape[1] and r[y, xx] not in SEL_GREEN and r[y, xx] != 235]
                    r[y, x] = alt[0] if alt else 235; n += 1
    return [('잔점', n, 0)]


def hud_src():
    import hud_ex
    return hud_ex.build()


EXTRA_22904 = comp_labels([(257, 39, 291, 64, '해제', 'B'), (280, 58, 302, 80, '상', 'B'), (300, 72, 321, 90, '용', 'B'), (316, 82, 341, 98, '브', 'B'),
                           (343, 88, 358, 104, '레', 'B'), (360, 90, 377, 104, '이', 'B'), (379, 88, 395, 106, '크', 'B'),
                           (411, 78, 435, 98, '비', 'B'), (440, 54, 465, 75, '상', 'B'), (437, 6, 482, 23, '스타트', 'B')], kill_boxes=[(332, 81, 339, 88), (334, 83, 342, 96), (320, 95, 334, 98)])
EXTRA = {('GO_SEL', 0x22904): [EXTRA_22904], ('GO_SEL', 0x1195C): [sel_specks], ('GO_OVER', 0x52C): [logos((7, 97), (104, 97))], ('CFG_000', 0): [movie_tail],
         ('CFG_001', 0): [bubble([(331, 347, 298, 'G14B', '{g:테스트 중}!'), (354, 365, 298, 'G11', '스타트 버튼으로'),
                                  (366, 377, 298, 'G11', '{r:테스트 중지}입니다.')], (294, 408), 208, {'k': 255, 'g': 152, 'r': 48}), logos((424, 371))]}
# CFG_001 아래 시험용 버튼 판 = 운전 HUD 와 같은 낱말(비상·해제·끔·마스콘, hud_ex 와 같은 꼴: 비상·끔 B / 해제·마스콘 G7, 그림자)
JOBS[('CFG_001', 0)] += [dict(r=(34 + 32 * i, 402, 60 + 32 * i, 415), t='비상', k='M', f='B', s='shadow') for i in range(9)] +     [dict(r=(2 + 32 * i, 473, 28 + 32 * i, 487), t='해제', k='M', f='B', s='shadow') for i in range(10)] +     [dict(r=(322 + 32 * i, 402, 348 + 32 * i, 416), t='끔', k='M', f='B', s='shadow') for i in range(6)] +     [dict(r=(322 + 32 * i, 450, 348 + 32 * i, 458), t='마스콘', k='M', f='G7', s='shadow') for i in range(6)]
JOBS[('GO_SEL', 0x28B30)] += [_shift(j, -32) for j in JOBS[('CFG_001', 0)] if j['t'] in ('비상', '해제', '끔', '마스콘')]


def load(name, off):
    if '/' in name: return open(os.path.join(ROOT, 'work', 'x', name), 'rb').read()   # 묶음 안 항목(work/x/…) — 예 DR_B1X00.SZ3/004.bin
    d = open(os.path.join(DISC, name + '.BIN'), 'rb').read()
    return d if off == 0 else dict(v2img.embedded(d))[off]          # 오프셋 0 = 파일 통째가 그림


def build(name, off):
    e = load(name, off); A = atlas.Atlas(e)
    done = RJ.apply(A, e, JOBS.get((name, off), []))
    for fn in EXTRA.get((name, off), []): done += fn(A, e) or []
    new = A.save_one() if A.one else A.save()
    return e, A, done, new


def preview(name, off, e, A):
    ys, xs = np.nonzero(A.orig); H, W = ys.max() + 1, xs.max() + 1
    a = GJ.rgb(A.orig[:H, :W], e); b = GJ.rgb(A.can[:H, :W], e)
    sh = np.concatenate([a, np.full((H, 4, 3), 255, np.uint8), b], 1)
    p = os.path.join(ROOT, 'work', 'gfx', 'prev_%s_%05X.png' % (name.replace('/', '_'), off))
    Image.fromarray(sh).resize((sh.shape[1] * 2, sh.shape[0] * 2), Image.NEAREST).save(p); return p


if __name__ == '__main__':
    keys = [k for k in list(JOBS) + list(EXTRA) if not sys.argv[1:] or k[0] in sys.argv[1:]]
    for name, off in dict.fromkeys(keys):
        e, A, done, new = build(name, off)
        print(name, hex(off), '바꾼 곳', len(done), '새 셀', getattr(A, 'added', None), '크기', len(e), '→', len(new), preview(name, off, e, A))
