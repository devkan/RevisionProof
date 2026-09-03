# ClickHouse intelligence QA and inventory — 2026-09-03

## Result and release boundary

Change Map, Approved Edit Memory, exact/HNSW/QBit search and portable backup/restore are implemented and verified locally. This report records the initial pre-deployment verification. The owner subsequently requested push/deployment; the seven-object Cloud migration and new-object-only role grants have now been applied. See [the release record](deployment-2026-09-03-clickhouse-intelligence.md) for current GitHub, deployment and LIVE evidence. Existing Cloud data and grants were preserved; billing configuration, other hackathon projects and the segment backup were not changed.

The Docker demo is available on this machine at `http://127.0.0.1:18125`, explicitly FIXTURE. It has the production-built frontend and the LIVE-capable backend package, but this rehearsal does not call Gemini or Cloud ClickHouse. No new LIVE delivery approval was granted. No commit/push occurred during the initial implementation turn; the subsequent authorized release is recorded separately. No PR, merge or repository visibility change occurred.

## Automated verification

| Gate | Result |
| --- | --- |
| Full backend suite | 278 PASS, 72.58 s |
| New intelligence tests | 136 service/query/media/schema + 34 backup tests |
| Final changed API/GCP guard tests | 72 PASS, 9.77 s |
| Frontend tests | 16 PASS |
| TypeScript/Vite production build | PASS; JS 233.17 kB / gzip 72.56 kB |
| Backend Ruff check/format, frontend ESLint | PASS |
| Git whitespace validation | PASS |
| Deployment Docker build | PASS |
| Linux-container full B render | READY, 3 PASS, map ready, 30 windows, zero review flags |

The first combined pytest run had 244 PASS and 34 setup errors because the Windows sandbox could not access a shared temporary pytest directory. No product assertion failed. Rerunning with the new workspace-scoped `--basetemp='../.gstack/pytest-main-20260903'` passed all 278 tests. Final API changes were then rerun with the 72-test targeted suite.

Linux Docker run: `01M1JMQCHKK01N4DJGTVKGJPWX`, candidate B, `READY`, all checks PASS, `delivery_approved=false`. Current local generated video is `/api/runs/01M1JMQCHKK01N4DJGTVKGJPWX/generated-video` on port 18125; this run is process-local and disappears after container restart. Do not present it as LIVE integration evidence.

## Real ClickHouse 26.2 evidence

An isolated local ClickHouse **26.2.19.43** was initialized with the actual SQL and the official `mcp-clickhouse` subprocess adapter.

- Successful synthetic namespace: `benchmark-20260903025709`, 12,000 normalized 768D vectors.
- One top-15 correctness comparison: exact 1.0, HNSW 1.0, QBit 1.0 agreement with exact. This is not a representative recall or speed benchmark.
- `EXPLAIN indexes=1` named `approved_edit_hnsw` and `vector_similarity` on the real MCP route.
- The original ordinary definer view did **not** select HNSW, even with more data/filter settings. A dedicated parameterized `approved_edit_neighbors` view with internal distance ordering and limit fixed this without allowing raw-table reads.
- The official MCP reader was denied raw `approved_edits` access.
- Two repeated raw samples aggregated to one unique sample, second 8, visual delta 0.15. Duplicate retry inserts did not inflate the map count.
- The script is wired into the existing isolated ClickHouse CI job; that hosted job has not been run in this task.

The tested export streamed 12,000 approved-edit benchmark rows and two frame-pair rows to a new manifest-backed directory. Restoration into a second empty 26.2 server reproduced both raw counts and the identical merged map `(8, 1, 0.15)`. QBit was rematerialized and the MV rebuilt from source data. No existing target data was overwritten.

Export checksums:

- `approved_edits.jsonl`: `b9fa714d9bbb00cb05e29ccacc3dfd04559249b605e423e7ba4ea61ead90655d`
- `revision_frame_pairs.jsonl`: `d5c2125935d3793f0331c7efe18b45c90379318ed5160660f5d63d04c36cf2ee`

## gstack design/browser QA and scoped review

Used gstack browser, design-review guidance and the review checklist. Testing-specialist work added negative-path regression tests. The code inspection was scoped to this extension and its integration boundaries, not a fresh full landing review of all historical differences from `main`. No numerical global health score or completed PR approval is claimed.

Observed and fixed during implementation:

1. HNSW could have been configured but unused behind the ordinary definer view; actual EXPLAIN verification and the parameterized query view now distinguish the real engine.
2. Empty Change Maps and malformed/fractional/bool count responses could have allowed a memory save; the save path now fails closed. Regression tests cover them.
3. Owner-key errors now use a dedicated authorization exception instead of returning arbitrary filesystem permission messages to the client.
4. Memory results follow newer server snapshots until an explicit manual search override.
5. Added inner spacing to timeline/save panels after visual inspection on mobile.

Browser checks (1280px desktop and 390px mobile):

- Default feedback classification, explicit checkbox, A/B generation, B full-source render and a 30-window map passed.
- The six expected seconds were labelled requested, the remainder unchanged, with no sampled review flags.
- Enlarged original/revised popup displayed both 1280px videos; shared play started both with observed time delta about 0.011 seconds.
- Escape closed the popup and returned focus to `Compare this moment`.
- Mobile stacked the players, retained controls and had no horizontal page overflow.
- Fixture save was disabled before final approval. An explicit fixture-only approval/save succeeded; a new proof retrieved Option B but did not automatically choose or approve it.
- QBit selector in FIXTURE still displayed actual engine FIXTURE, not a fabricated live query.
- Browser console: no errors during the tested flow. Source, preview and result videos loaded.

Screenshots were captured and visually inspected under ignored `.gstack/design-reports/`:

- `intelligence-initial.png`
- `change-map-mobile.png` (before inner-spacing adjustment)
- `comparison-desktop.png`, `comparison-mobile.png`
- `memory-mobile-final.png`, `memory-desktop-final.png`

The UI keeps technical search settings collapsed, readable body text, labelled time buttons, at least 44px control targets, non-color status icons, spinner/error states and a native modal focus boundary. Change Map remains sampled diagnostics, not an every-frame identity guarantee or a replacement for frozen checks. For externally uploaded edits without a generated-video URL, comparison is unavailable; the map and locked-check evidence remain visible.

## Resource inventory delta

### Local resources created

| Resource | Identity / status |
| --- | --- |
| ClickHouse image | `clickhouse/clickhouse-server:26.2`, digest `sha256:c2f2605585899d5103a0447daadbc0005f362200d5f0fcca7f40db3ca0dd36dd` |
| SQL QA container | `revisionproof-intelligence-check-20260903`, ID `b489b1bae2c6be31912e023e402a07a6988e74316a4f6ca7241cf1298ddaf856`, port 18123; stopped after verification |
| SQL QA volume | `revisionproof-intelligence-check-data`; preserved, including clearly labelled synthetic benchmark namespaces |
| Restore QA container | `revisionproof-intelligence-restore-20260903`, ID `0757b825820129033103f37db3e5161bd2e84c072edb4c06c4ab5e6abd8c05d8`, port 18124; stopped after verification |
| Restore QA volume | `revisionproof-intelligence-restore-data`; preserved |
| Application image | `revisionproof:intelligence-20260903`, ID `sha256:6c3fbbf2203e4fd7b7c328d01ef2db69f9e1b350ba14391c64b54d059dbcb9b9` |
| User-test application | `revisionproof-intelligence-demo-20260903`, ID `6e3f335990eea932bef2f5006e777ca6bc67dc3f0985c5e5d37e5b1751d87d2c`, loopback port 18125; left running, FIXTURE |
| Test export | `.gstack/intelligence-backup-roundtrip/`; synthetic data only, ignored by Git |
| Temporary native dev servers | Ports 8000 / 5173, started by this task; stopped after Docker demo was ready |

SQL QA labels are `project=revisionproof,purpose=intelligence-qa`; restore/demo use `com.kanapp.project=revisionproof` plus their purpose labels. Labels and exact names were inspected before stopping the two DB containers. No container, image, or volume belonging to another project was changed/deleted. Docker Desktop was started hidden because it was initially off.

Final Docker state: restore QA exited 0; source SQL QA exited 137 during stop, with `OOMKilled=false` and no Docker state error. Its named volume was retained; the already completed export and second-server restoration are the validated recovery evidence. Do not treat a forced stop as proof of a clean database shutdown.

To stop the user-test demo without deleting its container:

```powershell
docker stop revisionproof-intelligence-demo-20260903
```

Later removal of the listed containers, volumes and image must be separately reviewed. Stopped DB containers can be restarted with `docker start <exact-name>`. The backup does not require the QA containers to stay running.

### Initial Cloud read-only preflight (before the authorized release)

- Verified service: `268999c1-badb-423e-993c-ebab14b551c4` (RevisionProof), host `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`.
- Current observed server: `26.2.1.641`; deployment sentinel points to `revisionproof-agentic-2026-kan` and the exact host.
- Existing 12 tables/views listed; none of the seven extension objects existed. `segments_pre_seed_dedupe_20260826` remains present.
- Woke the existing RevisionProof service to perform those reads; no idling or billing settings were changed.
- Created a separate SQL-console draft `10b3df86-6a21-4796-bc3c-88a34f8050ea`; the user's historical query draft `61b0f114-44ce-46ac-b671-7699eb692739` was preserved. The new draft holds a read-only table inventory query.
- Billing page observed trial credits valid through 2026-09-24. This is an observation, not a promise of post-trial hosting or data retention.

### Cloud additions (subsequently applied in the authorized release)

Objects in database `revisionproof`:

| Object | Purpose |
| --- | --- |
| `revision_frame_pairs` | Append-only sampled measurements |
| `revision_change_windows` | Per-second aggregate states |
| `revision_change_windows_mv` | Incremental aggregation |
| `revision_change_map` | MCP diagnostic view |
| `approved_edits` | Approved reference facts, embedding, materialized QBit and HNSW |
| `approved_edit_memory` | Count/exact/QBit read view |
| `approved_edit_neighbors` | Parameterized HNSW read view |

Role additions are only for these new objects: writer INSERT on two raw tables, MCP reader SELECT on three views, and the existing HOST NONE definer's necessary source/aggregation privileges. Existing project-wide GCP IAM and existing ClickHouse grants are not removed.

Disable by feature flag first, then export. If deletion is later approved, detach/drop the three ordinary extension views and the extension MV before the three extension tables, after reviewing exact dependencies. Revoke only extension-specific grants. Never remove the common roles, definer, base database or preserved segment backup as part of extension cleanup. No deletion command is executed or auto-generated here.

## Release follow-up

The owner-authorized push/deployment completed the seven-object migration, restricted grants, Cloud Run release and fresh LIVE Gemini/MCP/full-video/Change Map QA. Current build, revision, image and run IDs are in [the release record](deployment-2026-09-03-clickhouse-intelligence.md) and HANDOFF. No new final delivery approval was granted.

The public library remains read-only. Enabling an owner-managed private save token requires separate credential setup; do not add a public write path or synthetic approved memories merely to populate the demo. Trial-expiry export/hosting decisions and submission publication remain owner tasks.
