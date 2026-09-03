# 기본 영상 편집 사용법과 검증 기록

현재 LIVE는 QA 수정본 `94c081c`, revision `00022-swm`이다. 영상 변경 시 초안 잔존, 정상 컷의 오판 BLOCKED, 로컬 자막 제거 오해석을 수정했고 실제 컷·복합 편집 검증을 통과했다. [최신 배포 기록](deployment-2026-09-03-qa-fixes.md)과 [현재 편집기](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=94c081c)를 참조한다. 아래 `00021` 배포 증거는 이전 릴리스 기록이다.

## 이번에 추가한 기능

2026-09-03 사용자가 요청한 기본 편집 확장이다. 기존 확대 전용 경로와 별도로 `EDIT_PLAN`을 구현했고, 기본 화면은 새 편집기로 열린다. 이전 문서의 “텍스트 삽입 미지원”은 이전 배포에 대한 기록이다. 이 문서의 배포 항목에서 실제 반영 여부를 확인한다.

| 기능 | 입력과 동작 | 범위 |
|---|---|---|
| Zoom in | 원본의 시작·끝 시간에 중심 확대 | 고정 1.05× / 1.12× A/B, 가장자리 기존 글자가 잘릴 수 있음 |
| Add text | 정확한 문구, 시작·끝, 위치 선택 | 한글·영문, 상단·중앙·하단·우측 하단, 글자 크기 A/B |
| Timed subtitle | 자막마다 시간·문구를 별도로 입력 | 직접 입력한 자막 cue, 다음 줄은 별도 편집으로 추가 |
| Cut a section | 지정 구간의 영상·소리를 함께 삭제 | 남은 구간 연결, 최소 1초 유지 |
| Find quiet pauses | 소리가 작은 구간 감지 후 체크박스로 선택 | 기본 −40 dB, 최소 0.7초, 소리 주변 0.12초 여유 |

MP4/MOV/WebM, 최대 24 MiB, 4–60초 원본. 최대 24개 작업을 조합할 수 있다. 결과는 1280×720 / 30 fps / H.264·AAC. 입력 영상 비율을 유지하며 여백을 넣어 준비한다. 무음 제안이 편집 한도를 넘으면 긴 구간부터 제안하고 생략된 개수를 알린다. 좌우 채널을 섞어 무음으로 오판하지 않도록 모든 채널의 음량을 확인한다.

자동 음성 인식·자막 생성, 원본에 이미 합성된 글자 제거·교체, 객체 추적·제거, 배경 교체, 생성 영상, 임의 효과·폰트 디자인은 지원하지 않는다. 텍스트와 자막은 새로 합성하는 레이어이다.

## 화면 순서

1. `Upload your video` 또는 샘플 선택. 크기·길이 초과는 업로드 전 경고하고 서버에서도 다시 검증한다.
2. 기능 버튼이나 예제를 선택한다. 자연어를 입력했다면 `Turn request into edit plan` → 결과 확인 → `Use draft in edit controls`. 경고가 있으면 `Use only these listed edits`로 적용 범위를 명시적으로 확인한다.
3. 카드에서 시간·문구·위치를 수정한 뒤 `Review edit plan`을 누른다. 카드만 사용하면 AI 해석을 기다리지 않는다.
4. 검토 목록에서 적용할 항목을 체크한다. 감지된 무음 컷은 기본 미선택이다. 원본과 수정 후 길이를 함께 보여준다.
5. `Create previews` → 전체 미리보기 확인 → A 또는 B 선택. 컷만 있다면 중복 영상 대신 한 개 미리보기를 만든다.
6. 최종 파일의 세 검사를 확인하고 전체 영상을 재생한다. 필요하면 `Adjust edits`로 돌아가 입력을 보존한 채 수정한다. 최종 납품 승인은 사용자가 별도로 누른다.

모든 입력 시간은 **원본 기준**이다. 앞부분을 삭제해도 뒤 자막의 시간을 다시 계산할 필요가 없다. 비교 화면도 삭제 구간을 건너뛰어 수정본과 같은 원본 장면을 표시한다.

## 바로 사용할 요청 예시

| 시도할 편집 | 화면에서 시작하는 방법 |
|---|---|
| 간단한 제목·주소 삽입 | `Add text` → 문구, 시간, 위치 선택 |
| 홍보 장면 강조 | `Promo highlight` → 확대와 하단 문구를 함께 수정 |
| 문장별 자막 | `Two timed subtitles` → 각 줄의 문구와 시간을 수정, 필요한 줄 추가 |
| 여러 편집 조합 | 자막·확대·문구 카드를 추가하고 `Cut a section`과 `Find quiet pauses`를 함께 검토 |

10초 KANAPP 인트로:

```text
4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시
```

시간별 자막과 특정 구간 삭제를 함께:

```text
0–4초에 “KANAPP, 실용적인 AI” 자막을 하단에 표시
4–10초에 “AI, made practical.” 자막을 하단에 표시
1–2초 구간 삭제
```

사이트 주소를 추가하려면 `Add text`에서 `http://www.kanapp.net`, 전체 시간, `Bottom right`를 선택한다. 기존 글자와 겹치지 않는지 미리보기로 확인한다.

침묵 정리:

```text
무음 제거
```

음악이 계속 있는 영상은 무음이 없을 수 있다. 이때 “No quiet pause…”를 표시하고 임의 구간을 삭제하지 않는다. 완전 무음 영상도 거의 전체를 삭제하지 않도록 보류 안내를 한다. 모든 무음 제안을 선택해야 하는 것은 아니다.

## 검증 방식과 호환성

- 새 spec 3.0은 선택한 작업, 원본→수정본 시간 연결, 전체 미리보기 SHA-256을 승인 시 고정한다. 최종 export는 승인한 전체 미리보기의 바이트 단위 복사이다.
- 승인 파일 일치 검사는 작은 글자 변경이나 0.2초 문구 누락도 실패시킨다. 외부 편집기로 다시 인코딩한 파일을 근사하게 허용하는 계약은 아니다.
- 보존 장면은 원본의 대응 시간으로 검사하고, 승인된 시각 편집 구간은 승인 미리보기와 비교한다. 소리는 잘린 승인 타임라인을 기준으로 비교한다. Change Map은 초당 2개 프레임의 진단이므로 전 프레임 의미 검수와 구분한다.
- LIVE는 기존 ClickHouse `version_feature_diff`에 `approved-reference` 기준선을 기록하고 공식 MCP 읽기 결과로 판정을 다시 계산한다. 3개 check ID는 유지한다. 별도 DB migration은 필요하지 않다.
- 기존 spec 2.0/2.1/2.2의 JSON·hash·오디오 기준은 그대로 유지한다. 새 코드 이전 커밋에서 생성한 고정 fixture로 검증한다.
- 승인 편집 라이브러리는 기존 확대 proof만 표현할 수 있다. 새 복합 편집에서는 저장·검색 UI를 숨기고 서버도 잘못된 저장을 거절한다. 복합 편집 저장을 지원한다고 표시하지 않는다.
- 원본과 진행 중 작업은 프로세스 메모리/임시 런타임에 있다. 서버 재시작 후 진행 중 작업 복구는 아직 없다.

## 로컬 검증

- gstack 엔지니어링 검토와 독립 반대 검토 수행. 원문 따옴표, 문구 속 명령 단어, 짧은 한국어 요청, 무음 제안 한도, 미리보기 후 수정 복귀 문제를 수정했다.
- 실제 `demo_movie_kanapp.mp4`: `01M1KD2G84K7G3CCT5RAG0WS89`, 원래 오류 요청 그대로 zoom + text, B 선택, READY / 3 PASS, Change Map ready / review flags 0. 6초 프레임에서 문구를 직접 확인했다.
- 합성 영상 자막 2개 + 수동 컷 + 무음 컷: `01M1KDAT3C4Z43KQJTYB8ZSW3J`, 10초→7.766667초, READY / 3 PASS, map flags 0. 수정본 3초와 원본 5.233333초 비교 확인.
- `Adjust edits`에서 원문·문구·원본 선택 보존 확인. 390px에서 가로 overflow 없음. 콘솔 오류 없음.
- 로컬 증거는 무시된 `.gstack/basic-*` PNG와 격리된 `.gstack/basic-editor-browser/`에 있다. 사용자 원본/출력 영상은 Git에 포함하지 않는다.
- 최종 소스 `1b2c0ae`의 로컬 gate: 백엔드 **322 passed / 113.75s**, 프런트엔드 **22 passed**, Ruff·ESLint·TypeScript·production build 통과. 25 MiB와 61초 파일의 브라우저 경고도 확인했다.

### LIVE 초안 연동 오류 회귀 검증

첫 배포 `1297750` / `revisionproof-staging-00018-4nc`에서 실제 Gemini 초안 요청이 HTTP 409로 실패했다. Cloud Run 로그와 설치된 Vertex SDK의 실제 스키마 변환으로 `properties.operations.items.properties.end.exclusiveMinimum` 미지원 오류를 재현했다. `c21d480`에서 SDK가 지원하는 inclusive minimum으로 표현하고, 기존 최소 구간 길이 검증을 유지했다. 종료 0초는 여전히 거절한다. 실제 `EditDraftOutput`에 SDK 변환을 적용하는 회귀 테스트가 수정 전 실패하고 수정 후 통과했다. 화면에 오류를 숨기거나 LIVE를 로컬 해석기로 바꾸는 방식은 사용하지 않았다.

이어 `c21d480` / `revisionproof-staging-00019-7d8`에서는 SDK 변환 뒤 Vertex가 복잡한 응답 스키마를 HTTP 400 `INVALID_ARGUMENT`로 거절했다. [공식 structured output 문서](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output?hl=en)의 제약에 맞춰 모델에 전달하는 형식만 단순화했다. 동일 프로젝트·모델의 실제 API에서 원래 한국어 요청이 확대와 정확한 문구의 두 작업으로 반환되는 것을 먼저 확인했다. `b6817e8`은 그 검증된 형식을 적용한다. 응답 수신 시에는 기존 엄격한 Pydantic 검증을 그대로 거치며, 시간 범위·문구 길이·알 수 없는 필드·24개 한도 위반을 거절하는 회귀 검증도 통과했다.

`b6817e8`의 앱 요청에서는 AI가 무음 부가 설정을 0으로 채워 엄격한 응답 검증이 거절하는 문제도 확인했다. `1b2c0ae`는 AI 출력에서 `threshold_db`, `min_silence`, `detected`를 제외한다. AI는 작업 종류·시작·끝·문구·위치만 제안하고, 실제 분석 설정은 검증된 기본값과 편집 카드가 소유한다. 앱 소스에서 추출한 동일 지침과 동일 SDK 스키마를 실제 Vertex에 보내 한국어 복합 요청 5개가 정확히 반환되는 것까지 사전 검증했다. 사용자가 요청문을 수정하면 이전 실패 안내도 지운다.

## 배포

푸시·배포·최종 LIVE QA를 완료했다. [현재 편집기 열기](https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=1b2c0ae). 기존 화면을 열어 둔 경우 이 링크로 다시 열거나 강력 새로고침한다. 새 HTML에는 `Cache-Control: no-cache`를 적용했다.

| 항목 | 확인 값 |
|---|---|
| 애플리케이션 소스 | `1b2c0aec4208359c5d764c527af5c41d59c91f67` |
| 브랜치 | `review/qa-hardening`, PRIVATE 저장소, PR·merge·공개 전환 없음 |
| Cloud Build | `2467c268-f0f9-4090-9c88-7dd71f454f53`, SUCCESS |
| 빌드 완료 | `2026-09-03T11:40:35.284495Z` |
| Cloud Run revision | `revisionproof-staging-00021-4fx`, 트래픽 100%, Ready / ConfigurationsReady / RoutesReady True |
| 이미지 digest | `sha256:9fc57bc421bbbd42476f6eb0d2082a3facf94a4770cca8d679fb8935f6e60f0a` |
| 소스 ZIP SHA-256 | `3fa6e58b5d790b6dd9c4522a19bc9b35922d6311b2665e0beb6b4216647880f2` |
| 전송 묶음 SHA-256 | `83b7779f3b8f9d7ba40ad32693b053f34ed21055f638d150b19860fc5e6a7e45` |
| 프런트엔드 자산 | `index-hZ4NyhYs.js`, `index-BNnhkqnB.css` |

### 최종 LIVE 실행 증거

- 원래 한 줄 요청 `4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시`가 실제 `/api/edit-plans/interpret`에서 성공했다. 응답 source는 `google.vertex.gemini`, 정확한 확대·문구 2개 작업, 경고 없음이다.
- gstack 브라우저에서 비민감 10초 합성 영상을 업로드하고 한국어 복합 요청을 입력했다. 한글 자막 0–3초 / 확대 4–10초 / 영문 문구 4–10초 / 수동 컷 0.5–1초 / 무음 찾기가 정확히 초안으로 표시됐다. 무음 컷 3.133333–4.866667초는 기본 미선택이며, 명시적으로 선택했다.
- 최종 run `01M1KHABHY8YWTZ7RQVPK3MF9Q`, B 선택, spec 3.0 hash `1d13f08da1107d4341e66354522975df23004f1c0106fef665909eb7a9325d3d`, 결과 **READY / 세 검사 PASS**. 원본 10초 → 수정본 **7.766667초**.
- 각 검사에 실제 `mcp_*` 측정값이 있고, Change Map은 `mcp-clickhouse.run_query` / ready / 8 windows / 16 samples / review flags 0이다. AI 초안 확인 후 사용자가 선택한 실행 계획의 provenance는 `user.structured`로 별도 표시한다.
- 다운로드한 MP4는 **2,687,810 bytes**. 선택한 B 미리보기와 최종 파일 SHA-256 모두 `3b095abd3db7f62f0ba375ac8013f85f610708c51780425e7a094e1189190735`로 일치한다. 파일의 1초 프레임에서 한글, 3초 프레임에서 하단 영문과 확대를 직접 확인했다.
- 비교 창의 수정본 3초 → 원본 5.233333초 연결과 양쪽 재생 준비 상태를 확인했다. 최종 흐름에서 새 브라우저 콘솔 오류가 없었다. 남아 있는 세 HTTP 409 로그는 위에서 수정한 이전 revision의 실패 기록이다.
- `/`, `/health`, `/ready`, `/api/runtime` HTTP 200. LIVE ready / intelligence enabled / 24 MiB / 4–60초 / memory read-only 확인. 최종 납품 승인은 `delivery_approved=false`로 남겼다.
- 증거는 무시된 `.gstack/basic-final-live-*`, `.gstack/basic-live-exact-draft.json`에 있다. 공개 저장소에 원본·결과 영상·실행 JSON·배포 묶음을 넣지 않는다. 서버 재시작 후 run API가 사라질 수 있으므로 이 기록과 보관된 증거를 함께 본다.

실제 KANAPP 원본의 LIVE 재전송은 앞선 자동 승인 검토가 거절했던 경계를 유지한다. 새 LIVE QA는 비민감 합성 영상으로 수행한다. 사용자의 실제 원본을 업로드했다고 주장하지 않는다. 기존 프로젝트·서비스·SA·자원·secret version을 유지한다.
