# 18초 소개 추가 — 소개 음성 대기

후속 완료: 사용자 소개 음성을 반영한 [최종 3분 14초 영상과 음성 배치 기록](demo-final-video-2026-09-06.md). 아래는 소개 음성을 받기 전 편집 단계의 기록이다.

작성일: 2026-09-06

사용자가 새로 촬영한 `video/demo_trial_0.mp4`에서 18초 소개를 편집해 기존 음성 포함 데모 앞에 붙였다. 제품의 주요 기능과 사람의 검토·승인을 중심에 둔 설계 방향을 짧게 소개한다. 사용자가 아래 대본으로 음성을 생성해 보내면 소개 구간에 배치하는 단계가 남아 있다.

## 결과물

- 전체 영상: `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_intro_pending_voice_v2.mp4`
- 소개만 보기: `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_intro_visual_only_v1.mp4`
- 녹음용 영문 대본: `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_intro_script.en.txt`
- 전체 길이: **03:14.000**, 1920×1080, 30 fps, H.264 + AAC 48 kHz 스테레오
- **00:00–00:18은 무음 소개**, 00:18부터 기존 02:56 본편과 음성이 시작된다.
- 전체 MP4: 21,571,816 bytes. SHA-256: `ab21e2c2db7e211c5be46e44c3e511eb9cdd34d3c8a270ab2a711a2c144722fb`.
- 기존 본편·원본 녹화·정렬 WAV는 보존했다. 소개 음성이나 자막을 새로 생성하지 않았다.

## 소개 화면 편집

| 완성 영상 시간 | 원본 demo_trial_0.mp4 시간 | 화면 |
|---|---|---|
| 00:00–00:04 | 00:08.90–00:11.90 | 제품명과 6단계 흐름에서 전체 편집 화면으로 천천히 넓혀 보여줌 |
| 00:04–00:07 | 00:49.10–00:51.65 | 텍스트·자막·컷·무음·속도·음량·로고 도구 목록 확대 |
| 00:07–00:10.5 | 01:10.00–01:13.50 | 속도·무음 도구와 실제 음량 설정 화면 |
| 00:10.5–00:14 | 01:47.00–01:50.50 | Gemini 음성 자막 초안과 편집 가능한 설정 |
| 00:14–00:18 | 02:02.35–02:05.55 | 계획 검토와 `Final approval — Never automatic` 진행 안내 |

대기, 빈 입력에 따른 경고, 녹화 도구 팝업 구간은 사용하지 않았다. 원본 UI 값이나 판정을 바꾸지 않았다. 소개의 음량 설정은 녹화 그대로 −6 dB이며, 본편의 별도 +6 dB 시나리오와 구분한다. 소개에서 보이는 자막은 아직 검토 전 초안이며, 실제 검증 통과 결과를 보여주는 구간이 아니다.

## 녹음할 영어 대본

| 소개 시간 | 내용 | 녹음 대본 |
|---|---|---|
| 00:00–00:04.5 | 제품과 설계 방향 | Meet RevisionProof, a video editing workspace built for human control. |
| 00:04.5–00:10.5 | 주요 기능 | Find scenes, add captions and branding, trim pauses, and adjust speed and sound. |
| 00:10.5–00:18 | AI·검증·사람의 역할 | AI drafts the edits. Checks verify the result. You keep final approval. |

- 총 35단어. RevisionProof와 AI 발음을 풀면 약 37단어 예산이다.
- 앞선 샘플에서 확인한 약 152.5 WPM을 참조하면 약 14.6초 낭독이다. 이번 소개 음성은 아직 받지 않았으므로 실제 소요 시간은 미확정이다.
- 기존 본편과 같은 영어 음색·속도로 세 문단만 녹음한다. 문장 사이 잠깐 쉬어도 되며, 정확한 화면 시각에 맞추는 작업은 음성 수신 후 수행한다.
- `RevisionProof`는 “Revision Proof”, `AI`는 “A I”로 읽는다.
- 소개의 장면 검색 설명은 이어지는 본편 첫 기능 시연으로 연결된다.

## 검증과 다음 음성 배치

- 총 5,820프레임 = 소개 540프레임 + 기존 본편 5,280프레임.
- 완성본의 00:18 이후 모든 디코딩 영상 프레임을 기존 본편과 비교해 동일함을 확인했다. 본편 영상 스트림은 재인코딩하지 않았다.
- 기존 정렬 WAV 앞에 정확히 18초 무음을 추가하고 AAC로 인코딩했다. 음성 속도 1.0배, 게인 변경 0 dB.
- 처음 18초는 디지털 무음이다. 기존 40개 음성 구간은 모두 18초 이동했으며, 원본 정렬 WAV와 최소 파형 상관계수 약 0.99890으로 일치한다.
- 오디오 최대 피크 약 −1.34 dBFS. 영상·음성 전체 디코딩 검사 통과. MP4 종료 시각은 정확히 194초이며 AAC 마지막 패킷의 디코더 패딩 256샘플은 무음이다.
- 소개 음성을 받으면 00:00–00:18에 맞춘다. 본편 첫 음성 배치는 00:18.12다. 실제 음성 길이를 확인한 뒤 문장 사이 쉼을 조정하고 본편 음성과 겹치지 않게 검증한다.

작업 자료: `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\intro\`

- `build_intro.py`: 소개 렌더링, 본편 결합, 대본·타임라인 생성
- `intro-edit-decisions.json`: 원본/완성 시간과 화면 구성
- `intro-narration-cues.csv`: 소개의 예상 음성 구간
- `body-audio-placement-offset-18s.csv`: 18초 이동한 본편 실제 음성 배치
- `verify_intro.py`, `qa.json`: 프레임·음성·입력 보존 검증

이전 기록: [본편 음성 배치](demo-audio-sync-2026-09-06.md). 제품 코드·배포·게시·제출 변경은 없다.
