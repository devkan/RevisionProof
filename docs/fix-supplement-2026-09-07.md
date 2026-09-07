# RevisionProof QA Follow-Up & Regression Test Supplement Report

- **Date**: 2026-09-07
- **Repository**: `D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof`
- **Branch**: `fix/qa-followup-bugs-20260907`
- **Base Commit**: `9fd3411` (`main`)
- **Status**: **보완 완료 / 내 재검수 대기 / 미병합·미배포 (Fix Completed / Awaiting User Re-Audit / Unmerged & Undeployed)**

---

## 1. 개요 및 추가 작업 배경

사용자 독립 검수 보고서([`docs/review-2026-09-07-antigravity-fixes.md`](review-2026-09-07-antigravity-fixes.md))에서 확인된 두 가지 보완 사항을 완벽하게 해결했습니다:
1. **백엔드 CI 린트 및 포맷 오류 해결**: E501(100자 초과), I001(import 정렬), F401(미사용 import) 수정 및 Ruff 포맷 검사 통과.
2. **Issue C 실 DOM 마운트 기반 회귀 테스트 보완 및 회귀 방지 실증**:
   - `renderToStaticMarkup` 대신 실제 DOM 환경에 마운트하여 사용자가 직접 실패 구간(review)을 클릭한 후, 컴포넌트를 unmount하거나 key를 변경하지 않고 동일 마운트에 새 PASS props를 전달하여 상태 전환을 검증.
   - 수정 전(9fd3411) 구현 실행 시 **FAIL**과 현재 수정본 실행 시 **PASS**를 명확한 증거 로그로 입증.

---

## 2. 추가 변경 파일 및 변경 이유

| 파일 경로 | 변경 유형 | 변경 이유 |
|---|---|---|
| [`backend/src/revisionproof/editing/render.py`](../backend/src/revisionproof/editing/render.py) | 수정 | 48행 E501(104자) 초과 if 조건문을 Ruff 포맷팅 규칙에 맞게 개행 분리하여 Ruff check 및 format 통과 |
| [`backend/tests/test_text_wrap_regression.py`](../backend/tests/test_text_wrap_regression.py) | 수정 | 미사용 `pytest` import 제거(F401), I001 import 정렬, 11/47행 장문 문자열 리터럴 분할(E501 해결, 문자열 내용 불변) |
| [`frontend/package.json`](../frontend/package.json) | 수정 | DOM 마운트 및 클릭 이벤트 기반 React 19 컴포넌트 테스트를 위해 `devDependencies`에 `"happy-dom": "^20.14.0"` 추가 |
| [`frontend/package-lock.json`](../frontend/package-lock.json) | 수정 | `happy-dom` 개발 의존성 추가에 따른 lockfile 갱신 (런타임 의존성 변경 없음) |
| [`frontend/src/changeMapTransitions.regression.test.tsx`](../frontend/src/changeMapTransitions.regression.test.tsx) | 수정 | `createRoot`와 `act`를 사용한 실 DOM 마운트 테스트 3종 추가 (동일 마운트에서 클릭 후 PASS 전환, 동일 analysis_id 갱신, 선택 구간 삭제 시 폴백) |

---

## 3. 백엔드 린트 및 포맷 검사 결과

프로젝트 루트(`D:\Hackathon\006.Agentic Cinema Hackathon\RevisionProof`)에서 실제 CI 명령을 실행하여 100% 통과를 확인했습니다.

### 1) Ruff Lint 검사
```bash
backend/.venv/Scripts/ruff.exe check backend scripts
```
**실행 결과**:
```text
All checks passed!
Exit Code: 0
```

### 2) Ruff Format 검사
```bash
backend/.venv/Scripts/ruff.exe format --check backend scripts
```
**실행 결과**:
```text
81 files already formatted
Exit Code: 0
```

---

## 4. Issue C 회귀 방지 효과 실증 (수정 전 FAIL vs 수정 후 PASS)

`runtime/antigravity-review-20260907/vitest-baseline.config.mjs`의 소스 보존 인메모리 컴포넌트 치환(Vite plugin) 방식을 활용하여 원본 소스코드 훼손 없이 기준 커밋(`9fd3411`)의 `ChangeMap`과 현재 수정본을 대상으로 동일한 테스트를 대조 실행했습니다.

### A. 수정 전 9fd3411 기준 커밋 실행: **FAIL (4개 실패)**

- **실행 명령어**:
  ```bash
  npx vitest run src/changeMapTransitions.regression.test.tsx --config ../runtime/antigravity-review-20260907/vitest-baseline.config.mjs
  ```
- **실패 테스트 항목 및 원인**:
  1. `Issue B: enables Compare this moment button when revisedVideoUrl is passed`:
     - **실패 원인**: 외부 영상 검사 시 `generated_version_url`이 없으므로 버튼이 `disabled=""`로 비활성화됨.
  2. `Issue C: clears stale failure explanation and metrics when transitioning from BLOCKED to PASS on the same mount`:
     - **실패 원인**: BLOCKED 상태에서 0:01 구간 클릭 후 PASS로 전환되었으나, `selected` 객체 상태가 이전 실패 윈도우 객체를 그대로 유지하여 `<div class="map-detail map-detail-review">` 및 `"Review needed"`, `"The observed result differs from the approved edit"`, `"28.00%"`가 잔존함.
     - **실패 로그**:
       ```text
       FAIL src/changeMapTransitions.regression.test.tsx > ChangeMap regression: Issue B & Issue C > Issue C: Change Map state transition from BLOCKED to PASS (Mounted DOM) > clears stale failure explanation and metrics when transitioning from BLOCKED to PASS on the same mount
       AssertionError: expected <div class="map-detail map-detail-review"> to be null
       ```
  3. `Issue C: updates detail metrics even when analysis_id is unchanged but window data is re-evaluated on the same mount`:
     - **실패 원인**: 동일 analysis_id 상태에서 구간이 재평가되어 PASS(0.00%)가 되었으나, 이전 실패 객체 참조 때문에 stale `28.00%`가 남음.
  4. `Issue C: falls back safely when previously selected window disappears in the new map on the same mount`:
     - **실패 원인**: 새 맵에서 0:01 구간이 삭제되었음에도 이전 `selected` 객체 참조로 인해 사라진 구간의 실패 설명이 계속 표시됨.

### B. 현재 수정본 실행: **PASS (6개 전체 통과)**

- **실행 명령어**:
  ```bash
  npm test -- src/changeMapTransitions.regression.test.tsx
  ```
- **실행 결과**:
  ```text
  RUN  v4.1.11 D:/Hackathon/006.Agentic Cinema Hackathon/RevisionProof/frontend

  Test Files  1 passed (1)
       Tests  6 passed (6)
    Start at  20:06:17
    Duration  998ms (transform 89ms, setup 0ms, import 290ms, tests 85ms, environment 460ms)
  ```
  - 동일 마운트에서 실패 구간 클릭 후 새 PASS props가 주입되었을 때, `selection`이 현재 `analysis_id`와 동기화되어 즉시 초기화되며 상세 카드 및 잔차 델타가 최신 PASS 값(`0:00–0:01 · Unchanged`, `0.00%`)으로 정확히 갱신됨.
  - 동일 analysis_id 내 윈도우 갱신 시에도 현재 맵의 윈도우를 조회하여 신규 수치(0.00%) 반영 확인.
  - 선택된 윈도우가 사라지는 경우 신규 맵의 유효한 첫 번째 윈도우로 안전하게 폴백 확인.

---

## 5. 전체 테스트, 린트 및 빌드 검증

| 항목 | 명령어 | 실행 위치 | 결과 | 비고 |
|---|---|---|---|---|
| **백엔드 Ruff 린트** | `backend/.venv/Scripts/ruff.exe check backend scripts` | 루트 | **PASS** | All checks passed! |
| **백엔드 Ruff 포맷** | `backend/.venv/Scripts/ruff.exe format --check backend scripts` | 루트 | **PASS** | 81 files already formatted |
| **백엔드 회귀 테스트** | `uv run pytest tests/test_text_wrap_regression.py` | `backend/` | **PASS** | 4 passed in 0.10s |
| **백엔드 전체 테스트** | `uv run pytest -q` | `backend/` | **PASS** | **353 passed** in 131.75s (100%) |
| **프론트엔드 전체 테스트** | `npm test` | `frontend/` | **PASS** | **16 files, 78 passed** in 1.29s |
| **프론트엔드 린트** | `npm run lint` | `frontend/` | **PASS** | 0 errors, 0 warnings (`eslint . --max-warnings 0`) |
| **프론트엔드 프로덕션 빌드** | `npm run build` | `frontend/` | **PASS** | `tsc -b && vite build` 정상 번들링 완료 |

---

## 6. 의존성 변경 사항 및 미검증 항목 보고

1. **의존성 변경 내역**:
   - `dependencies`(런타임 의존성): **0건 변경 (일절 수정 없음)**.
   - `devDependencies`(개발/테스트 의존성): `"happy-dom": "^20.14.0"` 추가.
     - **추가 이유**: Vitest 환경에서 컴포넌트를 실제 DOM에 마운트(`createRoot`)하고 사용자 클릭 이벤트를 직접 발생시킨 뒤 동일 마운트 인스턴스에 새 props를 전달하는 실 DOM 상호작용 회귀 테스트를 실행하기 위해 필요한 최소한의 경량 DOM 환경 라이브러리입니다.
2. **미검증 항목 및 환경적 한계**:
   - 본 검증은 로컬 가상 환경 및 합성 스냅샷/실제 영상 파일 기반의 컴포넌트/엔진 단위 검증입니다.
   - 최종 main 브랜치 통합 및 운영/스테이징 배포 후의 라이브 클라우드 환경 통합 점검은 배포 절차에 따라 후속 진행될 예정입니다.
