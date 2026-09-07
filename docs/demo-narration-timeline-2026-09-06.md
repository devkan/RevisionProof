# RevisionProof 영어 내레이션 — 2분 56초 타임라인

작성일: 2026-09-06

**기준 영상:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_visual_only_v1.mp4`
**속도 참조:** `D:\Hackathon\005.All Things Agentic Hackathon\screentshot\audio_1_sample.mp3`

샘플을 로컬에서 새로 전사해 분석했다. 길이 약 107.3초, 인식된 단어 272개로, 문장 사이 쉼을 포함한 평균 속도는 약 152.5 WPM이다. 샘플이 영어이므로 영문 내레이션으로 구성했다. 샘플 내용은 제품 설명의 근거가 아니라 읽는 속도의 참조로만 사용했다.

대본은 331단어이며, 약어와 제품명 발음을 풀어 센 예산은 341단어다. 152.5 WPM 기준 예상 낭독은 약 134.2초, 화면 확인과 호흡에 남긴 시간은 약 41.8초다. 각 행은 150 WPM에서도 배정 시간 안에 들어오는지 확인했다. 실제 음성을 생성하거나 강제 정렬한 결과가 아니므로 최종 발음·강세·쉼에 따라 길이는 달라질 수 있다.

## 타임라인과 대본

각 구간 시작에 해당 문장을 읽고, 먼저 끝나면 다음 구간까지 쉰다. 문장을 이어 붙여 영상 전체에 균등하게 늘이지 않는다. 화면 열은 녹음하지 않는다.

| 영상 시간 | 화면 | 영어 내레이션 |
|---|---|---|
| 00:00–00:04 | 제품 소개 | RevisionProof verifies video edits before final approval. |
| 00:04–00:10 | 스마트 장면 검색 | I locate the opening scene with Google AI and ClickHouse. |
| 00:10–00:20 | 자연어 요청과 Gemini 초안 | I ask for a zoom and a tagline on this scene. Gemini drafts the edits for me to review. |
| 00:20–00:27 | 텍스트·로고 설정 | I adjust the text, then position the logo precisely in the closing scene. |
| 00:27–00:32 | 편집 계획 검토 | I review all four edits before generating the previews. |
| 00:32–00:40 | A/B 비교와 확대 | The app creates two previews. I compare their treatments and inspect the opening in version A. |
| 00:40–00:47 | A 선택·전체 결과 생성 | I select A and build the full result. The rendering wait is shortened here. |
| 00:47–00:55 | 검증 통과·원본과 결과 | The checks pass. The original and revised ending show the website and logo added where intended. |
| 00:55–01:00 | 영어 자막 생성 | Next, Gemini creates editable English captions from the source audio. |
| 01:00–01:06 | 브랜드 표기 교정 | I correct the brand spelling myself. Generated captions remain a draft. |
| 01:06–01:09 | 무음 탐색 | Quiet pauses are suggested for review. |
| 01:09–01:13 | 속도 1.25배 | Playback speed is one point two five. |
| 01:13–01:17 | 볼륨 +6 dB | The quieter section gets six extra decibels. |
| 01:17–01:27 | 자막 검토·무음 구간 선택 | After reviewing the captions, I select only the main quiet pause. The other suggested cuts stay unchecked. |
| 01:27–01:32 | 실제 자막 결과 | The revised preview shows the captions on the actual footage. |
| 01:32–01:38 | 원본·결과 시간 대응 | Synchronized comparison follows the revised timing through removed pauses and speed changes. |
| 01:38–01:42 | 11개 편집·승인 대기 | Eleven edits, a shorter video, and approval still pending. |
| 01:42–01:47 | 잘못된 계획 차단 | Now, an invalid edit: this text falls entirely inside a cut. |
| 01:47–01:54 | 충돌 설명과 시간 수정 | The app explains why. Moving the text to the ending clears the conflict. |
| 01:54–01:58 | 정상 계획·27초 | The plan now targets twenty seven seconds. |
| 01:58–02:02 | B 선택 | I choose version B for this edit. |
| 02:02–02:06 | 잘못된 외부 영상 검사 | I submit an intentionally incorrect external export. |
| 02:06–02:11 | 다운로드 차단 | Matching duration is not enough. The incorrect export is blocked. |
| 02:11–02:17 | 세 가지 검사 실패 | Three deterministic checks fail: preview match, kept footage, and approved audio. |
| 02:17–02:23 | ClickHouse MCP·Change Map | The official ClickHouse MCP supplies measurements for these eleven flagged seconds. |
| 02:23–02:28 | B 재생성·재검사 | I rebuild version B and check the new result. |
| 02:28–02:35 | 세 가지 검사 통과 | All three checks pass for this new export: preview match, preserved timeline, and approved audio. |
| 02:35–02:39 | 수정된 엔딩 확인 | The comparison shows the requested ending text. |
| 02:39–02:44 | ClickHouse 실행 이력 | ClickHouse records completed queries from the MCP reader. |
| 02:44–02:50 | 저장된 FAIL·PASS 결과 | The stored checks show the external export failing, followed by version B passing. |
| 02:50–02:56 | 최종 승인권 | RevisionProof verifies the result. Final approval stays with you. |

## 녹음 메모

- `RevisionProof`: “Revision Proof”. `MCP`: “M C P”. `AI`: “A I”. `ClickHouse`: “Click House”.
- 1.25는 “one point two five”, +6 dB는 “six extra decibels”, 27초는 “twenty seven seconds”로 작성해 숫자 읽기 길이를 반영했다.
- 01:42의 “Now, an invalid edit”부터 문제 시연임을 분명하게 전환한다. 02:06의 “blocked”, 02:28의 “pass”, 마지막 “you”를 가볍게 강조한다.
- 02:23의 재검사는 선택한 B를 새로 만든 뒤 그 결과를 검사하는 과정이다. 실패한 외부 파일 자체가 고쳐졌다고 설명하지 않는다.
- Change Map의 표시 구간은 샘플 기반 진단이다. 모든 프레임이나 의미를 완벽하게 검증한다고 표현하지 않는다.
- ClickHouse 장면은 녹화된 실행 이력과 저장 결과이며, 이 대본 작성 중 새 쿼리를 실행한 것은 아니다.
- 마지막은 승인 대기다. 최종 승인·다운로드가 끝났다고 말하지 않는다.
- 영상과 참조 오디오는 수정하지 않았고, 내레이션 음성도 생성하지 않았다.

## 함께 저장한 파일

폴더: `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\narration\`

- `revisionproof-narration.en.txt`: 타임코드 없는 영문 대본
- `revisionproof-narration-pronunciation.en.txt`: 약어·제품명 발음을 풀어 쓴 참고 대본
- `revisionproof-narration-cues.csv`, `narration-cues.json`: 타임코드·예상 길이·여유 시간
- `reference-analysis.json`, `reference-transcript.txt`: 참조 음성의 새 로컬 분석
- `narration-validation.json`: 구간별 시간 예산 검증 결과

화면 편집 기록: [무음 데모 편집본](demo-visual-edit-2026-09-06.md).
