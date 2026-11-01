# 전차로 GO! EX (세가 새턴 일본판) 한글 패치

> **내려받기:** [릴리즈 페이지](https://github.com/hospi0/densha-ex-kr-patch/releases/latest) — 최신 v0.9. 적용 방법·원본 MD5 는 패치 묶음의 readme 에 있습니다.
>
> 이 저장소에는 도구·번역 텍스트·작업 문서만 있습니다(ROM·빌드 결과물 없음).

## 내용

- 이 게임의 화면 글자는 글꼴이 아니라 전부 그림입니다. VDP2 그림 형식(`tools/v2img.py`)·SZ3/DARC/CHR 압축(`tools/arc.py`, `tools/lzenc.py`)을 풀고, 그림 위 글자를 갈무리 글꼴로 다시 그려 넣었습니다.
- 운전 HUD·말풍선·안내 판넬·구간 팝업·판정·통지표·사고·발차 안내·보너스 게임·설정·컨트롤러 선택·노선 선택·조작/운전 설명·이름 등록·순위·검사 모드
- 열차 소개 동영상 4편 설명 상자(cinepak 재인코딩)

## 빌드 순서

```
python tools/popup_ex.py all
python tools/repack_ex.py
python tools/moviebox_ex.py
python tools/discbuild.py --write
python tools/make_dist.py
```
