# 32 MB upload limit release — 2026-09-04

## Result

RevisionProof now accepts source videos up to **32,000,000 bytes (32 MB)**. The limit is deliberately decimal MB rather than 32 MiB: Cloud Run's 32 MiB HTTP/1 request limit also includes the multipart form envelope, so a 33,554,432-byte file would leave no room for form fields and headers.

Files larger than 32 MB are rejected in the browser before an upload request is sent. The message reports the actual size rounded upward to one decimal place, so a 32,000,001-byte file is shown as 32.1 MB rather than appearing equal to the limit.

## Source and deployment

- Branch: `review/qa-hardening`
- Source commit: `08113823abbba221a9926799e9f5ae1dc0f33657`
- Cloud Build: `98fdd1af-59ca-4300-ae39-c4cca0d334a5` — `SUCCESS`
- Image digest: `sha256:c04b1b1caae3bbd97b3d21741ee12709a468e2fbe49947411b677554d40e4ef4`
- Cloud Run revision: `revisionproof-staging-00025-88t`
- Traffic: 100%
- Service: `revisionproof-staging`, project `revisionproof-agentic-2026-kan`, region `us-central1`

## Verification

- Backend: 348 passed.
- Frontend: 24 passed across 8 files.
- Ruff, ESLint, production build and `git diff --check`: passed.
- LIVE `/api/runtime`: `upload_limits.max_bytes=32000000`, mode `LIVE`, intelligence enabled.
- LIVE browser: the upload area states `up to 32 MB`.
- LIVE browser boundary: selecting a synthetic 32,000,001-byte file displayed `This video is 32.1 MB. The maximum is 32 MB. Choose a smaller file.` and sent no upload request.
- LIVE server boundary: a multipart request containing a synthetic 32,000,000-byte `.mp4` reached application validation and returned HTTP 422 `This file could not be read as a video. Try exporting it as MP4.`. It did not receive a Cloud Run HTTP 413 response.
- LIVE `/health` and `/ready`: HTTP 200; browser console had no errors.

## Operating constraint

Keep `REVISIONPROOF_MAX_UPLOAD_MB` at or below 32 and continue interpreting it as decimal MB. Raising the file limit to 32 MiB would exceed Cloud Run's body limit once multipart overhead is added.
