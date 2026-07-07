<p class="badges">
  <img src="https://img.shields.io/badge/버전-v20260707-9e1b1b" alt="버전">
  <img src="https://img.shields.io/badge/플랫폼-Nintendo%20DS-c8a15a" alt="플랫폼">
  <img src="https://img.shields.io/badge/형식-xdelta-informational" alt="형식">
  <img src="https://img.shields.io/badge/번역-한국어-success" alt="한국어">
</p>

# 삼국지대전 DS 한국어 패치

닌텐도 DS용 **삼국지대전 DS**(三国志大戦DS, SEGA, 2007 — 아케이드 이식작)를 한국어로 번역한 팬 패치입니다.
스토리·카드 데이터·시스템 텍스트를 전량 번역하고, 무장 명판과 메뉴 그래픽까지 한글로 다시 그렸습니다.

> ※ 이 패치는 시리즈 **1편인 「삼국지대전 DS」**(게임코드 A3DJ)용입니다.
> 후속작 **「삼국지대전 텐(三国志大戦 天)」에는 적용되지 않습니다.**

## 한눈에 보기

| 항목 | 내용 |
|---|---|
| 대상 게임 | San Goku Shi Taisen (J) · 128MB · 게임코드 A3DJ |
| 원본 MD5 | `4322aaa2144d997fe3fea0038b4bf9e3` |
| 패치 형식 | xdelta3 (`.xdelta`) |
| 최신 버전 | **v20260707** |
| 동작 확인 | DeSmuME 0.9.13 · 실기 · 세이브 데이터 원본 호환 |

## 설치 및 적용

1. 원본 일본판 롬을 준비합니다. **(이 저장소는 롬을 포함하지 않습니다.)**
   - 파일: `San Goku Shi Taisen (J).nds` (128MB)
   - MD5: `4322aaa2144d997fe3fea0038b4bf9e3`
2. [패치 파일](https://github.com/kimjh-eclipse/sangokushi-taisen-ds-kr/raw/main/SGS_kr_patch_v20260707.xdelta)을 내려받아 xdelta(또는 xdeltaUI, Delta Patcher 등)로 적용합니다.

   ```bash
   xdelta -d -s "San Goku Shi Taisen (J).nds" SGS_kr_patch_v20260707.xdelta "San Goku Shi Taisen (K).nds"
   ```
3. 적용 결과를 확인합니다 (선택).
   - 한국어판 MD5: `0a59f57dd371bc73a3d97b91cacb9a9a`
   - 패치 파일 MD5: `12cc7973c80e91304f74d9e6d8076256`

> 💡 GUI 툴만 쓰신다면 **xdeltaUI**에서 원본 롬을 Source, 패치를 Patch로 지정하고 Apply Patch를 누르면 됩니다.

## 번역 범위

### 텍스트
- **스토리 모드(삼국영걸전)**: 시나리오 전량 (110 엔트리, 5,200여 문자열)
- **카드 데이터베이스**: 무장명 · 소속 · 계략명 · 계략 설명 · 특기
- **시스템 텍스트**: 메뉴 · 안내 · 전투 메시지 등 약 1,100건 인플레이스 번역
- **한글 폰트**: KS X 1001 완성형 2,350자 전체를 게임 폰트에 주입

### 그래픽 (이미지 글자)
- **무장 명판 950종** (대형 NP + 전투용 소형 NPS)
- **버튼류**: 결정 / 예 / 아니오 / 뒤로 / 전환 / 덱편성 / 이름변경 / 파기 / 교환 / 계략설명 / 삭제
- **모드 선택 화면**: 하단 터치 배너 5종 + 상단 「모드 선택」 헤더 · 미리보기 캡션
- **군의(軍議) 서브메뉴 배너**: 카드도감 / 전기도감 / 덱편성 / 군주설정
- **덱편집 UI · 필터 탭 34종** 등

전체 변경 내역과 미번역 잔여 항목은 **[📝 패치노트](patch-notes.md)** 에 정리되어 있습니다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `SGS_kr_patch_v20260707.xdelta` | 한국어 패치 본체 |
| `docs/patch-notes.md` | 패치노트 (적용법 · 번역 범위 · 알려진 한계) |
| `docs/dev-log.md` | 리버스 엔지니어링 · 한글화 작업 기록 |
| `tools/` | 언팩/리팩, 압축 코덱, 폰트 주입, 그래픽 식자, 에뮬레이터 자동화 도구 109종 |

## 저작권 고지

- 이 저장소는 **게임 롬이나 원본 게임 자산을 포함하지 않습니다.** 패치는 정품 소지자의 개인적 이용을 전제로 합니다.
- 三国志大戦 및 관련 자산의 모든 권리는 **SEGA**에 있습니다. 본 패치는 비영리 팬 번역이며, 권리자의 요청이 있을 경우 배포를 중단합니다.
- `tools/`의 소스 코드는 저장소 라이선스(Apache-2.0)를 따릅니다.
