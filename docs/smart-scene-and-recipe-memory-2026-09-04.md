# 스마트 장면 찾기와 편집 레시피 메모리 — 2026-09-04

Status: 구현, ClickHouse Cloud 스키마 적용, Cloud Run 배포와 LIVE gstack 검증 완료.

## 사용 흐름

영상 수정 입력의 **Smart scene finder** 체크박스는 기본적으로 꺼져 있다.

- 꺼짐: 시작·종료 시간을 직접 입력하거나 요청문에 `4–10초`처럼 시간 범위를 써야 편집 초안을 만들 수 있다.
- 켜짐: 찾을 장면을 자연어로 입력하고 **Find scenes**를 누른다. LIVE 화면은 이 동작이 Google AI와 ClickHouse 크레딧을 사용한다고 미리 알린다. 체크만 하는 것은 호출이나 과금 작업을 만들지 않는다.
- 검색 결과: 최대 3개의 시간 범위, 유사도, 장면 설명을 보여준다. 하나를 선택하면 그 범위가 편집 초안과 이후 실행 계획에 전달된다.
- 실패 시: 자동 실행을 추측하지 않고 스마트 찾기를 끈 뒤 시간을 직접 입력하라고 안내한다.

업로드 영상은 장면 검색 때 다시 크기·길이 제한을 검사한다. 서버는 선택 결과를 원본 SHA-256과 연결해 보관하며, 다른 영상의 결과나 변조한 세그먼트 ID로 실행을 만들 수 없다.

## ClickHouse 사용 범위

스마트 찾기는 최대 15장의 표본 프레임을 Google AI로 설명하고, 설명과 보이는 글자의 임베딩을 `smart_scene_segments`에 기록한다. 원본 영상이나 프레임 이미지는 ClickHouse에 저장하지 않는다. 검색은 공식 `mcp-clickhouse.run_query`가 보안 뷰 `smart_scene_search`만 읽어 cosine 유사도로 순위를 만든다.

장면 검색 파생 데이터는 `expires_at` 기준 7일 뒤 자동 삭제된다. 쓰기 역할은 원본 테이블에 INSERT만 가능하고, MCP 역할은 보안 뷰만 SELECT할 수 있다.

Approved Edit Memory는 이제 단일 확대 선택뿐 아니라 검증된 복합 편집 계획도 `approved_edit_recipes`에 저장하고 찾을 수 있다. 저장 조건은 기존과 동일하다: 완성본 READY, 필수 검사 3개 PASS, 깨끗한 Change Map, 사용자의 최종 전달 승인, LIVE에서는 비공개 워크스페이스 키가 모두 필요하다. 검색 결과의 **Use as editable draft**는 설정을 복사할 뿐 자동 적용·후보 선택·승인을 하지 않는다.

백업 형식은 레시피 테이블을 포함하는 v2다. 복원기는 기존 v1 백업도 받아들이며, 스마트 장면 데이터는 7일짜리 임시 검색 자료라 백업 대상에서 제외한다.

## UI 정리

- 편집 기능 버튼을 작은 카드로 줄이고 자막 생성은 별도 한 줄 작업으로 분리했다.
- 자동 자막과 수동 자막은 Start, End, Words, Position, 재생, 삭제가 한 행에 보이는 압축 테이블로 편집한다.
- 모바일에서는 자막 행이 화면 폭 안에서 3단으로 재배치되고 가로 스크롤이 생기지 않는다.
- 실제 가능한 복합 요청과 외부 편집기가 필요한 고난도 작업 예시는 접을 수 있는 안내에 유지했다.

## 검토와 검증

- 백엔드 전체: **347 passed**. Ruff 검사 통과.
- 프런트엔드: **24 passed**, ESLint 통과, TypeScript/Vite 프로덕션 빌드 통과.
- ClickHouse **26.2.19.43** 임시 전용 인스턴스: 전체 스키마 생성, 7일 TTL, 스마트 장면 검색, 승인 레시피 검색, HNSW/QBit, 공식 MCP 뷰 조회가 통과했다. MCP 사용자의 `approved_edits`, `approved_edit_recipes`, `smart_scene_segments` 직접 조회는 모두 거부됐다.
- gstack 데스크톱: OFF 상태 시간 필수, ON 상태 비용 안내, 세 결과 선택, 선택한 4–8초가 편집 계획에 반영되는 흐름을 확인했다.
- gstack 데스크톱/390px 모바일: 압축 자막 편집 UI와 반응형 배치, 가로 오버플로 없음, 최종 브라우저 콘솔 오류 없음.

로컬 FIXTURE 검색 결과는 UI 연습용이며 Google 또는 ClickHouse 크레딧을 쓰지 않는다. LIVE 성공은 배포 뒤 실제 `google.vertex.gemini`와 `mcp-clickhouse.run_query` 출처를 확인해야 한다.

## ClickHouse Cloud 적용

기존 데이터와 권한을 보존한 채 다음 5개 객체를 추가했다.

- `smart_scene_segments`, `smart_scene_search`
- `approved_edit_recipes`, `approved_edit_recipe_memory`, `approved_edit_recipe_neighbors`

적용 후 `revisionproof` 데이터베이스는 전체 24개 대상 객체를 반환했다. 새 구성 검사는 보안 뷰 3개, TTL 테이블 1개, writer INSERT 권한 2개, MCP SELECT 권한 3개, definer 권한 2개를 확인했다. MCP 역할의 세 원본 테이블 직접 SELECT 권한은 0개였고, 적용 과정에서 실제 승인 레시피나 장면 데이터를 넣지 않았다.

## LIVE 배포와 검증

- Source: `b0b00a9937cf158560f4a3fba2f3d473104b3b6c`
- Cloud Build: `aa63da88-9407-45e6-9659-235427e5d4a2`, SUCCESS at `2026-09-04T05:51:14.595604Z`
- Image: `sha256:03da71d487c0911359164cae0956de4e29ce7410207ab5ec65d4df3b268f2970`
- Cloud Run: `revisionproof-staging-00024-c9p`, traffic 100%, readiness conditions `True / True / True`
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app/?release=b0b00a9`

배포 후 gstack으로 다음을 다시 확인했다.

- `/health`, `/ready`, `/api/runtime`가 모두 200을 반환했다. 런타임은 `LIVE`, `live_ready=true`, intelligence enabled, memory read-only다.
- 체크 해제 상태에서 **Start / End** 입력이 보이고, 요청문만 입력한 상태에서는 시간 범위가 없어 초안 버튼이 비활성화됐다.
- 체크 상태에서 **Uses Google AI and ClickHouse credits**와 **Find scenes를 누를 때만 표본 추출과 색인이 실행된다**는 안내가 보였다.
- 번들 샘플에 `dashboard chart`를 검색하자 `/api/scene-search`가 200으로 완료됐고, UI에 `8 segments indexed · ClickHouse search`와 세 결과를 표시했다.
- 첫 결과 `20.0–24.0s`를 선택하고 `선택한 장면을 확대해 주세요`를 해석하자 `Zoom in · 20s–24s` 초안이 만들어졌다.
- 스마트 검색은 28.9초, 편집 해석은 2.5초가 걸렸다. 네트워크 요청 실패와 브라우저 콘솔 오류는 없었다.
- 390px 뷰에서 `scrollWidth=390`, 가로 오버플로가 없었고 검색 결과와 편집 기능을 계속 조작할 수 있었다.

LIVE QA에는 번들 샘플만 사용했다. 실제 KANAPP 업로드 파일은 재전송하지 않았고, 전달 승인이나 가짜 Approved Edit Memory도 만들지 않았다.
