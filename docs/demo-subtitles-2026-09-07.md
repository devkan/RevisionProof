# 영어 자막 포함 최종 영상 v5

작성일: 2026-09-07

사용자가 요청한 흰색 영어 자막, 검은 테두리, 투명도 약 35%의 검정 배경을 기존 v4 영상에 추가했다. 원본을 보존하고 별도 영상과 수정 가능한 자막 파일을 출력했다.

## 결과물

- **자막 포함 영상:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v5_subtitled.mp4`
- **스타일 포함 자막:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v5.en.ass`
- **일반 자막:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v5.en.srt`
- 영상: 03:14.000, 1920×1080, 30 fps, 5,820프레임, H.264 + 기존 AAC 음성.
- MP4: 23,944,976 bytes. SHA-256: `763f9b636cb837eb35d1a2d2025d91a691d64847b5fc09fcb082baebdac1a108`.
- 이전 v4 MP4와 전체 정렬 WAV는 그대로 보존했다. 영상에 자막을 직접 표시했으며 음성은 재인코딩 없이 복사했다.

## 자막 구성

- Arial Bold, ASS 기준 52 크기, 흰 글자, 검은색 2.3px 테두리.
- 검정 배경은 ASS alpha `0x59`: 투명도 약 34.9%, 불투명도 약 65.1%. 모서리를 약간 둥글게 하고 글자 주변 여백을 확보했다.
- 문장마다 고정된 최대 두 줄이다. 단어별 강조나 빠르게 바뀌는 단문 연속 표시는 사용하지 않았다.
- 실제 음성 45개 구간을 38개 자막 묶음으로 구성했다. 의미가 이어지는 짧은 문장은 한 자막으로 묶었다.
- 자막 표시 시간은 약 2.40–7.31초. 가장 빠른 구간도 초당 약 16.5글자다.
- 대부분 화면 아래 중앙에 표시한다. A/B 비교와 A 선택 설명 두 자막은 선택 버튼과 미리보기 하단 내용을 가리지 않도록 화면 위쪽으로 이동했다.
- 제품명 RevisionProof, ClickHouse, `tagline`, 전사 오류 `rendering weight`를 실제 대본의 `rendering wait`로 교정했다. 숫자 표기를 정리했으며 의미·발화 내용은 유지했다.
- v4에서 반영한 연결 멘트 `Now, let's see RevisionProof in action.`도 포함했다. 제거된 본편 첫 제품 소개 문장은 자막에 다시 넣지 않았다.

SRT에는 텍스트·줄바꿈·시각이 들어 있다. ASS에는 같은 내용에 배경·테두리·글꼴·위치·짧은 등장/퇴장 효과가 포함되어 있다.

## 검증

- 실제 음성 배치표와 자막의 전체 내용을 비교했다. 문장부호·숫자·전사 오류를 정규화하면 일치하며, 45개 음성 구간이 각각 한 번씩 포함된다.
- 자막 시작·종료, 구간 겹침, 최대 두 줄, 표시 시간, 읽기 속도를 확인했다.
- Windows의 실제 libass 렌더 결과로 글자 영역을 측정해 배경 크기를 맞췄다. 최종 선택 글꼴은 `Arial-BoldMT`다.
- 최종 MP4에서 38개 자막의 중간 시각을 각각 추출해 실제 글자 표시를 확인했다. 기준 흰색 글자 픽셀 검출 비율은 모든 구간에서 99.8% 이상이다.
- 별도 회색 화면에서 배경 투명도를 렌더링해 약 34.4%로 측정했다. 색 공간·양자화 오차를 포함해 요청한 약 35%와 일치한다.
- 기존 v4와 자막 영상의 AAC 비트스트림 SHA-256이 같다. 음성·싱크는 그대로다.
- 최종 파일의 전체 영상·음성 `-xerror` 디코딩 검사 통과. 194초, 5,820프레임 확인.
- 원본 v4 SHA-256 `e62297bd70b8b0ea4e4215a77b9879e6538d01faeba283e24a31cb29fc900ce6` 보존 확인.

## 재현·후속 편집

- 생성 도구: `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\build_subtitled_demo.py`
- 검증 도구: 같은 폴더의 `verify_subtitled_demo.py`
- 작업 폴더: `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\subtitles\`
- `caption-manifest.json`: 문장별 시각, 줄바꿈, 글자·배경 좌표, 읽기 속도.
- `qa.json`: 출력 규격·해시·음성 보존·자막별 표시 검증.
- `final-cue-01.png`부터 `final-cue-38.png`: 실제 최종 영상의 자막별 화면.

이전 기록: [연결 멘트 포함 v4와 음성 배치](demo-final-video-2026-09-06.md). 게시·제출·제품 코드·클라우드 변경은 수행하지 않았다.
