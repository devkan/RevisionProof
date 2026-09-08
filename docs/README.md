# RevisionProof Documentation Index

Quick Links:
- **GitHub Repository**: [https://github.com/devkan/RevisionProof](https://github.com/devkan/RevisionProof)
- **Live Studio Demo**: [https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/studio)
- **Demo Video (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)

---

## 1. Project Handoff & Hackathon Submission

- [현재 핸드오프 (HANDOFF.md)](../HANDOFF.md) — 배포·검수·최종 CI 완료 상태, 운영 주의점, 세션 완료 내역.
- [Submission Pack & Release Gates (2026-09-08 갱신)](submission-pack-2026-08-27.md) — 해커톤 제출용 영문 프로젝트 소개, 기능, 아키텍처, 파트너 연동, 링크 및 릴리스 게이트 상태.

---

## 2. Latest Deployment & Verification (Antigravity Fixes)

- [Antigravity 수정 배포 기록 (revision 00031 / source b13d8b0)](deployment-2026-09-07-antigravity-fixes.md) — PR #2 병합, Cloud Run 배포, 라이브 검증 및 회귀 증거.
- [Antigravity 보완 독립 재검수 보고서](review-2026-09-07-antigravity-supplement.md) — Ruff 검사 및 실 DOM 회귀 테스트 통과 검수.
- [Antigravity 보완 보고서 (Ruff 포맷팅 & 실 DOM 회귀 테스트 실증)](fix-supplement-2026-09-07.md) — 미사용 import 정리, 문자열 줄바꿈, happy-dom 실 DOM 테스트.
- [Antigravity 최초 수정 보고서](fix-report-2026-09-07.md) — Issue A/B/C 원인 분석, 코드 diff 및 단위 검증.
- [Antigravity 최초 독립 검수 보고서](review-2026-09-07-antigravity-fixes.md) — 독립 검수팀의 초기 점검 및 피드백.
- [스테이징 브라우저 QA 및 결함 재현 보고서](qa-review-2026-09-07.md) — Issue B/C 라이브 결함 재현 스크린샷 및 녹화 자료.
- [Main 브랜치 통합 계획](main-integration-2026-09-07.md) — 브랜치 통합 및 증거 보존 범위.
- [코드 리뷰 및 QA 분석 보고서](qa-report-2026-09-07-code-qa.md) — 자막 줄바꿈, 외부 검증 비교, Change Map 상태 동기화 분석.

---

## 3. Demo Video & Audio Production

- **최종 시연 영상 (YouTube)**: [https://youtu.be/KS1vJDMnnW4](https://youtu.be/KS1vJDMnnW4)
- [영어 자막 영상 v5 (최종 완성본, 3분 14초)](demo-subtitles-2026-09-07.md) — 흰색 Arial Bold, 검정 테두리·배경 자막 타임라인.
- [한국어 요약 자막 영상 v3](demo-korean-summary-subtitles-2026-09-07.md) — 37개 짧은 요약 자막, 고유명사·숫자 정리.
- [한국어 구술형 음성 영상 v2](demo-korean-conversational-audio-2026-09-07.md) — 자연스러운 한국어 구술형 음성 배치 및 검증.
- [한국어 구술형 대본 v2](demo-narration-ko-conversational-v2-2026-09-07.md) — 14개 문단 대본, 강조·쉼 편집 기준.
- [한국어판 오디오 싱크 v4](demo-korean-audio-sync-2026-09-07.md) — 45개 실제 음성 배치와 검증.
- [한국어 내레이션 대본 v4](demo-narration-ko-2026-09-07.md) — 3분 14초 타임라인 및 녹음 대본.
- [최종 데모 v4 타임라인](demo-final-video-2026-09-06.md) — 소개·시연 연결 멘트 반영 3분 14초 화면 구성.
- [18초 제품 소개 추가본](demo-intro-edit-2026-09-06.md) — 전체 3분 14초 확장 편집.
- [영어 음성 합성 완료본 (2분 56초)](demo-audio-sync-2026-09-06.md) — 음성 배치 및 검증 자료.
- [영어 내레이션 타임라인](demo-narration-timeline-2026-09-06.md) — 153 WPM 기준 화면별 대본.
- [무음 데모 영상 편집본](demo-visual-edit-2026-09-06.md) — 4개 원본 영상 화면 구성 및 검증.
- [KANAPP 30초 영어 프로모 영상 및 시나리오](kanapp-english-demo-video-2026-09-04.md) — 라이브 녹화 시나리오 및 차단/복구 증거.

---

## 4. Studio Interface & Editing Features

- [Studio 인라인 설정 배포 (revision 00028)](deployment-2026-09-05-inline-studio.md) — 항목 바로 아래 펼침 설정 카드 및 Check plan 복구.
- [Studio 항목별 인라인 설정 설계](studio-inline-settings-2026-09-05.md) — 카드 스타일, 포커스 복원, gstack 검증.
- [Studio 6단계 워크플로 UI 설계](studio-ui-2026-09-04.md) — 01~06 단계별 워크플로 및 기능 매핑.
- [Studio 최초 배포 및 QA (revision 00026)](deployment-2026-09-05-studio.md) — 실사용 검증 및 재배포 기록.
- [Studio LIVE QA](qa-live-2026-09-05-studio.md) / [Studio 재리뷰 QA](qa-review-2026-09-05-studio.md) — 모바일 뷰포트 및 차단·복구 검증.
- [Advanced Editing 가이드](advanced-editing-guide-2026-09-04.md) — 한국어/영어/혼합 음성 자막 생성, 0.5~2× 배속, 볼륨 조절, 로고 오버레이.
- [Advanced Editing 최초 배포 (revision 00023)](deployment-2026-09-04-advanced-editing.md) — 혼합 음성 자막 및 고급 편집 파이프라인.
- [Basic Editing 가이드](basic-editing-guide-2026-09-03.md) — 줌, 텍스트 오버레이, 구간 컷, 침묵 구간 자동 제안.
- [Basic Editing 배포 (revision 00021~00022)](deployment-2026-09-03-basic-editor.md) 및 [QA 리뷰](qa-review-2026-09-03-basic-editor.md).
- [32 MB 원본 업로드 확장 배포](deployment-2026-09-04-upload-32mb.md) — 4~60초, 최대 32 MB 미디어 수용.
- [스마트 장면 찾기 및 편집 레시피 메모리 UI](smart-scene-and-recipe-memory-2026-09-04.md).

---

## 5. ClickHouse MCP Intelligence & Cloud Infrastructure

- [ClickHouse 인텔리전스 런북](clickhouse-intelligence-runbook.md) — Change Map, 벡터 검색, 백업, 마이그레이션, 롤백 절차.
- [ClickHouse MCP 최초 연동 배포 (revision 00020)](deployment-2026-09-03-clickhouse-intelligence.md).
- [ClickHouse MCP 복구 및 gstack QA](qa-report-2026-09-02-mcp-recovery.md).
- [ClickHouse MCP QA 및 리소스 목록](qa-report-2026-09-03-clickhouse-intelligence.md).
- [시스템 아키텍처 및 신뢰 경계](architecture.md) — AI 해석 vs 결정론적 검증의 명확한 분리.
- [보안 및 실패 정책](security.md) — 비밀 관리, 무단 배포 차단.
- [GCP 인프라 프로비저닝 런북](gcp-foundation-runbook.md).
- [통합 상태 점검표](integration-status.md).

---

## 6. Historical QA & Early Foundations

- [영어 프롬프트 플레이스홀더 배포 (revision 00030)](deployment-2026-09-06-english-placeholders.md).
- [원본 업로드 및 승인 메모리 UX 배포 (revision 00019)](deployment-2026-09-03-source-upload.md).
- [초기 풀비디오 자동화 워크플로 QA](qa-report-2026-09-02-automatic-full-video-ui.md).
- [최초 LIVE 배포 및 최종 검증 (2026-08-26)](qa-report-2026-08-26-live-final.md).
- [초기 인프라 리소스 목록](infrastructure-inventory-2026-08-26.md) 및 [초기 제출 스모크](qa-report-2026-08-27-submission-smoke.md).
