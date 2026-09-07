# 소개 음성 포함 최종 데모

작성일: 2026-09-06

## 최신본 v4 — 소개에서 시연으로 연결

사용자의 `audio_3.mp3`로 본편 첫 제품 소개 문장을 교체했다. 소개의 최종 승인 설명 뒤에 제품 소개가 다시 나오는 반복을 없애고, `Now, let's see RevisionProof in action.`으로 실제 시연을 안내한다.

- **최신 최종 영상:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v4.mp4`
- **최신 전체 정렬 음성:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_narration_full_v4.wav`
- 길이·규격: **03:14.000**, 1920×1080, 30 fps, 5,820프레임, H.264 + AAC 48 kHz 스테레오.
- MP4: 21,836,068 bytes. SHA-256: `e62297bd70b8b0ea4e4215a77b9879e6538d01faeba283e24a31cb29fc900ce6`.
- 이전 v3와 모든 원본 입력을 보존했다.

| 완성 영상 시간 | 연결부 음성 |
|---|---|
| 00:15.80–00:17.40 | You keep final approval. |
| 00:18.45–00:20.55 | Now, let's see RevisionProof in action. |
| 00:21.55–00:24.52 | I locate the opening scene with Google AI and Click House. |

새 MP3는 디코딩 기준 약 2.101초다. 새 전사를 기존 요청 문장과 정규화해 대조했고 내용이 일치한다. 원본 전체 음성을 속도 1.0배·게인 변경 0 dB로 배치했다. 입력 음량은 약 −16.35 LUFS다. 파일 구간 기준 앞뒤 약 1초씩 여유를 두며, 원본 음성 자체의 쉼도 유지했다.

v3의 `body-1` 문장 `RevisionProof verifies video edits before final approval.`이 차지하던 00:18.12–00:21.47 음성을 제거하고 그 안에 새 문장을 배치했다. 그 외 44개 소개·본편 음성 구간의 PCM과 배치 시각은 동일하다. 영상 비트스트림도 v3와 동일하다.

전체 디코딩 검사와 45개 음성 구간 대조를 통과했다. 최소 AAC 파형 상관계수는 약 0.99894, 최종 오디오 피크는 약 −1.22 dBFS다. 교체 문장의 원본 샘플 누락·중복과 다른 음성의 겹침이 없으며, 제거한 문장 뒤쪽은 실제 무음으로 확인했다.

후속 자막·수정은 `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\intro\transition_voice\final-audio-placement-v4.csv`와 최신 WAV를 사용한다. 같은 폴더의 `qa.json`, `audio_3-transcript.json`에 검사와 전사 기록이 있다. 재현 도구는 상위 폴더의 `replace_transition_voice.py`, `analyze_transition_voice.py`다.

## 이전 v3 완료 기록

사용자가 제공한 소개 음성 `video/audio_2.mp3`를 앞 18초 소개 장면에 맞춰 배치해 최종 영상을 완성했다. 기존 본편의 영상과 음성 타이밍을 유지했다.

## 결과물

- **최종 영상:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_demo_final_v3.mp4`
- **전체 정렬 음성:** `D:\Hackathon\006.Agentic Cinema Hackathon\video\revisionproof_narration_full_v3.wav`
- 길이: **03:14.000**. 1920×1080, 30 fps, 5,820프레임, H.264 + AAC 48 kHz 스테레오.
- MP4: 21,861,496 bytes. SHA-256: `683bbc636e996bcb3745ec9a83f4e396c34dd840848ca95fe92e575477f9f2df`.
- WAV: 194초, PCM 24비트 48 kHz 스테레오. 55,872,102 bytes.
- 자막은 추가하지 않았다. 원본 녹화·MP3·이전 편집본은 보존했다.

## 소개 음성 배치

약 14.269초인 원본 음성을 로컬 faster-whisper로 새로 전사했다. 제품명 띄어쓰기와 문장부호를 정규화한 뒤 기존 대본과 비교해 내용 일치를 확인했다. 실제 검출된 0.276–0.350초 문장 사이 무음의 가운데에서 분리했다.

| 완성 영상 시간 | 소개 음성 |
|---|---|
| 00:00.12–00:04.33 | Meet RevisionProof, a video editing workspace built for human control. |
| 00:04.45–00:09.70 | Find scenes, add captions and branding, trim pauses, and adjust speed and sound. |
| 00:10.60–00:12.23 | AI drafts the edits. |
| 00:13.60–00:15.19 | Checks verify the result. |
| 00:15.80–00:17.40 | You keep final approval. |

소개의 자막 초안 화면에 AI 문장을, 계획 검토 화면에 검사와 최종 승인 문장을 배치했다. 본편 첫 음성은 00:18.12이며 소개 구간 끝과 약 0.72초 여유가 있다. 표의 구간은 원본의 문장 앞뒤 쉼을 포함한다.

소개 입력 음량은 약 −15.59 LUFS, 본편 원본은 약 −15.40 LUFS로 차이가 작아 속도와 음량을 바꾸지 않았다. 전체 영상에 맞춰 문장 사이 무음만 추가했다. 새 음성을 생성하지 않았다.

## 검증

- 소개 MP3를 디코딩한 684,911 스테레오 샘플 프레임을 빠짐없이 한 번씩 순서대로 사용했다. 문장 사이 분할점 주변 20ms 피크는 −40 dBFS 미만이다.
- 본편 정렬 WAV는 정확히 18초 위치부터 같은 PCM으로 배치했다. 소개와 본편의 속도는 1.0배, 게인 변경은 0 dB다.
- 최종 WAV의 24비트 변환 오차를 확인했다.
- 기존 3:14 편집본과 최종 영상의 H.264 비트스트림 SHA-256이 동일하다. 영상은 재인코딩하지 않았다.
- 소개 5개 + 본편 40개 음성 구간을 최종 AAC와 대조했다. 최소 파형 상관계수 약 0.99894로, 누락·겹침 없이 타이밍이 일치한다.
- 최종 오디오 피크 약 −1.24 dBFS. 클리핑 없음. AAC 마지막 패킷의 디코더 패딩 256샘플은 무음이며 MP4 종료 시각은 194초다.
- 영상·음성 전체 `-xerror` 디코딩 검사 통과. 입력 파일 SHA-256 보존 확인.

## 후속 편집 자료

폴더: `D:\Hackathon\006.Agentic Cinema Hackathon\video\edit_work\intro\voice_sync\`

- `final-audio-placement.csv`: 소개와 본편을 합친 45개 실제 음성 구간. 후속 자막은 이 시각과 전체 WAV를 기준으로 맞춘다.
- `audio_2-transcript.json`: 소개 음성의 새 전사·단어 시각.
- `qa.json`: 원본/최종 해시, 실제 소개 배치, 음성 대조 결과, 파일 규격.
- 재현 도구: 상위 폴더의 `finalize_demo.py`, `transcribe_intro_voice.py`.

이전 단계: [소개 편집·대본](demo-intro-edit-2026-09-06.md), [본편 음성 배치](demo-audio-sync-2026-09-06.md). 최종 로컬 영상 파일을 완성했으며 게시·제출·클라우드 변경은 수행하지 않았다.
