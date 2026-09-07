# Main integration — 2026-09-07

## Authorization and starting point

The owner explicitly requested careful commit, push, and merge after a read-only Git/GitHub audit. This record captures the integration scope and local verification; the resulting GitHub PR and Actions runs are the authoritative merge/hosted-CI evidence.

- Repository: `devkan/RevisionProof`, private; default branch `main`.
- Starting main: `00603c5f9a69cfe22ee78f1ea6fad1aa97539a58` (initial commit).
- Starting implementation head: `b23208ac43232b340b9f711efc6d017a54d911a9` on `review/qa-hardening`.
- Fresh GitHub comparison: source branch 88 commits ahead, 0 behind; 179 changed files. There were no open or historical PRs at the audit.
- Initial working changes: three tracked documentation files and twelve untracked documentation files. No application-source changes remained from the Antigravity session.
- Four remote `backup/pre-*` branches are restoration references. Preserve them and the implementation branch; do not merge backup branches separately or rewrite the existing commits.

## Integrated implementation

The existing commits bring main up to the already-developed application: bounded video uploads, natural-language edit drafts, zoom/text/captions/cuts/speed/volume/logo controls, Studio and classic UI, A/B previews, deterministic export checks and human delivery approval. ClickHouse integration includes MCP reads, sampled Change Map diagnostics, scene search, scoped approved-memory retrieval, migrations and recovery tooling. Historical deployment evidence remains in its dated records.

The new documentation commit adds the actual demo recordings and English/Korean narration/subtitle records, plus the owner's Google Antigravity code-review report. Large generated media remains outside Git in the parent `video/` directory.

## Changes made during integration preparation

- Added root `ruff.toml`, extending the existing `backend/pyproject.toml` with `src = ["backend/src"]`. Root-level `ruff check backend scripts` previously applied fallback settings to `scripts/`: two import-order errors and nine formatting failures. Explicit discovery applies the existing Python style without reformatting application or operational code.
- The first PR CI run passed isolated ClickHouse/MCP integration but failed three of 349 backend tests because the Ubuntu runner lacked `NotoSansCJK-Regular.ttc`. Added `fonts-noto-cjk` alongside FFmpeg and a file-existence check in CI, matching the renderer's required Linux font and the existing production image. No renderer fallback, skipped test or application behavior change was introduced. First-run evidence: [Actions 34096772251](https://github.com/devkan/RevisionProof/actions/runs/34096772251).
- Corrected the stale engineering-guide statement that speech transcription was outside scope. The existing implementation already supports editable Korean/English/mixed-speech subtitle drafts; unsupported object/background edits remain excluded.
- Added explicit Antigravity attribution to its review report and separated its findings from implemented changes. Existing source/commit attribution is preserved.

## Fresh local verification

Executed on Windows using the repository's existing Python and Node environments:

| Check | Result |
|---|---|
| Backend suite | 349 passed in 142.25 seconds; 83% statement coverage |
| Frontend suite | 72 passed across 15 files |
| Ruff lint | PASS for backend and scripts |
| Ruff format | All 80 Python files already formatted |
| Frontend lint | PASS with zero allowed warnings |
| Frontend production build | PASS; JS `index-BYBHYv_J.js`, CSS `index-BaYy-LUs.css` |
| FIXTURE release rehearsal | Three complete BLOCKED → READY → local delivery-approval runs passed |
| Repository text audit | 214 tracked/new files scanned; no matches for the selected credential patterns; checked local document links resolve |

Local raw logs and the document/credential-pattern audit are under ignored `runtime/premerge-2026-09-07/`. Frontend tooling initially could not spawn a helper inside the sandbox; the same commands passed with authorized local execution. Backend collection was restricted to `backend/tests` and a fresh temporary directory to avoid old inaccessible runtime folders; no test files were excluded.

The existing CI workflow runs on PRs and main pushes. It must pass before merge, including the container build and isolated ClickHouse/MCP integration job. Existing results on initial main do not validate this branch. See the PR/Actions for hosted results; do not infer fresh cloud-provider execution from local tests.

## Open findings and scope boundaries

The [Antigravity report](qa-report-2026-09-07-code-qa.md) documents word-breaking captions, unavailable external-result comparison, and stale selected Change Map details after rechecking. Its scope was code analysis and local tests, with browser automation and retained source fixes explicitly excluded. Those findings remain open; this integration does not claim to fix them or that the current test suite covers each defect.

The integration review checked the export-reference hash, final-delivery gate, fixed-array media executor and the reported UI paths. This is not a claim of an exhaustive new line-by-line review of every historical commit or a fresh production-browser audit.

Use a normal merge commit after CI passes so all existing commits remain reachable from main. Verify the merged tree against the reviewed PR head, fetch main, and fast-forward the local main without disturbing dirty work. Do not force-push, squash away provenance, delete restoration branches, change repository visibility, or run cloud migrations/deployments as part of this Git task. The GitHub workflow inspected here contains tests/builds and isolated integration checks; the existing Cloud Run deployment is a separate operational concern.
