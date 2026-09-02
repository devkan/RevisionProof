# Infrastructure inventory - 2026-08-26 deployment delta

This file records the resources and artifacts added after the 2026-08-25 foundation inventory. Read both files before modifying or removing infrastructure.

## Current visual demo deployment - 2026-09-02

- Exact account: `secureis@gmail.com`
- Exact project: `revisionproof-agentic-2026-kan` (`348672234012`)
- Source commit: `81521d3`
- Cloud Build source: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788345660.840908-b8f0dacfb1b8473f82aa5052219b25f5.tgz`
- Cloud Build: `a38932bf-80ff-4b89-bdde-1353305a72ca`, `SUCCESS`
- RevisionProof image tag: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:a38932bf-80ff-4b89-bdde-1353305a72ca`
- RevisionProof image digest: `sha256:e3779de18b356002910c9983c29459cd31fe8c99c2f89e5b6668030d3c5332a8`
- Cloud Run revision: `revisionproof-staging-00012-dnv`, 100% traffic
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- Visual source: `gs://revisionproof-agentic-2026-kan-media/assets/01M00000000000000000000000/revisionproof_v1.mp4`, generation `1788344192014639`, 800,620 bytes
- ClickHouse visual source rows: asset `01M00000000000000000000000` count 1; segment rows count 3; legacy asset retained
- Complete QA run: `01M1GVQRHVVZ1TAQRWJZ1H0ACC`, state `READY`, delivery approval not granted
- QA candidate object: `runs/01M1GVQRHVVZ1TAQRWJZ1H0ACC/versions/revisionproof_v3_ready.mp4`, generation `1788346299626803`, 966,907 bytes
- QA ClickHouse rows: one spec, 12 version features, three version checks

The intermediate visual-asset deploy used commit `dc751a9`, Cloud Build `6a90c79e-1a4c-4272-af5d-55a09b99ffd7`, source object `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788344581.688018-63fbe01263074dedac65172494ba708f.tgz`, image digest `sha256:1e2574159637a13dae38051afb0a948efdcca980d67f7b2e06f81199587ce8f0`, and revision `revisionproof-staging-00011-sd9`. It has been superseded by revision `00012`.

These changes created no new GCP or ClickHouse resource type. They added two build-source objects, two build records, two Artifact Registry image versions, Cloud Run revisions `00011` and `00012`, one versioned visual source object, four source-index rows, and one QA run's private artifacts/audit rows. Existing guarded cleanup still targets the owning bucket, repository, service, and project-sentinel ClickHouse database. No other GCP project was selected or modified.

## Previous recovery deployment - 2026-09-02

- Exact account: `secureis@gmail.com`
- Exact project: `revisionproof-agentic-2026-kan` (`348672234012`)
- Source commit: `4852259`
- Cloud Build source: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1788338726.755047-7758a1b6f2ef4705862725a167e09763.tgz`
- Cloud Build: `3ebc367e-31a4-4087-abba-6c245cb8c9bc`, `SUCCESS`
- RevisionProof image tag: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:3ebc367e-31a4-4087-abba-6c245cb8c9bc`
- RevisionProof image digest: `sha256:c7cd7fc4f9ebc19cbfbc37294fd42d8a79b3e1f9007715f9020a5911b8975cc5`
- Cloud Run revision: `revisionproof-staging-00010-k4g`, 100% traffic
- Cloud Run capacity: concurrency 4, min 1, max 1; runtime service account `revisionproof-runtime@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- Runtime truth: `LIVE`, mutable, `live_ready=true`; successful integrations are proven per run
- Numeric Secret Manager version in use: version `1` for both exact RevisionProof ClickHouse secrets
- Recovery proof: run `01M1GN7EY252SSM5F2AM170TKY`; first MCP attempt timed out, second fresh process anchored three matches, `error=null`

This deploy added one Cloud Build source object, one build record, one Artifact Registry image version, and Cloud Run revision `00010`; the existing guarded cleanup targets already cover their parent bucket, repository, and service. The source object remains governed by the bucket's one-day delete lifecycle. No other project was selected or modified.

Local Docker recovery QA image:

- Tag: `revisionproof:mcp-retry-fix`
- Image ID: `sha256:75a7b5d452d6051703283a621c68d6f112bee501abab1fa8b8afaacbc8be7915`
- Image size: 2,270,263,589 bytes
- Temporary port: `127.0.0.1:18081`
- Result: `/health` and `/ready` PASS in `FIXTURE` mode; the temporary container was removed and the image retained

## Previous final LIVE deployment delta - 2026-08-26

These were the current resources before the 2026-09-02 recovery deployment above:

- Exact account: `secureis@gmail.com`
- Exact project: `revisionproof-agentic-2026-kan` (`348672234012`)
- Source commit: `d1b9a10`
- Cloud Build source: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1787748935.43622-57c54f8dcbb6447d822425a6f7a3b906.tgz`
- Cloud Build: `d5845e1e-9123-4e81-81cb-0fb3f6b607ec`, `SUCCESS`
- RevisionProof image tag: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:d5845e1e-9123-4e81-81cb-0fb3f6b607ec`
- RevisionProof image digest: `sha256:54e2427d56e8408dfd712c4864df8dec555d127f4b1380a070bbfe2b662e73e3`
- Cloud Run revision: `revisionproof-staging-00009-mbh`, 100% traffic
- Cloud Run capacity: concurrency 4, min 1, max 1; runtime service account `revisionproof-runtime@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`
- URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- Runtime truth: `LIVE`, mutable, `live_ready=true`; successful integrations are proven per run
- Numeric Secret Manager version in use: version `1` for both exact RevisionProof ClickHouse secrets

ClickHouse Cloud current inventory:

- Organization/service: `Kanapp` / `RevisionProof`
- Service ID: `268999c1-badb-423e-993c-ebab14b551c4`
- Host: `r2uz2gfc2f.asia-northeast1.gcp.clickhouse.cloud`
- Region/version observed: `asia-northeast1` / `26.2.1.558`
- Bootstrap admin: deleted (`revisionproof_bootstrap_admin` count 0)
- Durable view definer: `revisionproof_view_definer_user` count 1; two views across two replicas = 4 durable view replicas
- Preserved backup: `revisionproof.segments_pre_seed_dedupe_20260826` count 1. Do not drop it.

Final run persistence:

- Run: `01M0Z3338TYVHWHK4FZRGADTKZ`
- ClickHouse: one `revision_specs` row, 24 `version_features` rows, six `version_checks` rows
- GCS: private `runs/01M0Z3338TYVHWHK4FZRGADTKZ/versions/revisionproof_v2_blocked.mp4` (394,028 bytes) and `revisionproof_v3_ready.mp4` (394,983 bytes)
- Final state: `READY`, `delivery_approved=true`; human delivery approval event 14 at `2026-08-26T13:48:30.750541Z`

## Local Docker

- Final QA image: `revisionproof:qa-final`
- Image ID: `sha256:7fc2c1bf5ef5fa60d29b3919d3fadd2bb747e54336d1bf9cbc2ba7350441645c`
- Image size: 2,270,104,910 bytes
- Required labels: `com.kanapp.managed-by=revisionproof-repo`, `com.kanapp.project=revisionproof`
- Final QA container: `revisionproof-qa-final`, ID `57e41abd3343e532fb391435aec76c2b3d50672965814530e8c6fa9dde950d4b`
- Published port during verification: `127.0.0.1:18081`
- Result: `/health`, `/ready`, and `/api/runtime` passed in `FIXTURE` mode. The temporary container was stopped and automatically removed after QA. The image was retained.
- No unrelated image or container was removed, renamed, or stopped.

Dry-run local cleanup:

```powershell
powershell -File infra/docker/cleanup-local.ps1
```

Exact label-guarded cleanup, only after review:

```powershell
powershell -File infra/docker/cleanup-local.ps1 -Execute
```

## Historical foundation deployment

Every command was run with account `secureis@gmail.com`, project `revisionproof-agentic-2026-kan`, and an explicit `--project=revisionproof-agentic-2026-kan` where the command supports it. No global gcloud project was changed.

- Project: `revisionproof-agentic-2026-kan`
- Project number: `348672234012`
- Region: `us-central1`
- Source commit: `6977747`
- Local deployment archive SHA-256: `AFFA4A5B3B5C8213C4674BD31E064DE5E9E742DFFEE3ED7FF10558B85804D090`
- Cloud Shell archive: `/home/secureis/revisionproof-deploy-6977747.zip`
- Cloud Shell build directory: `/home/secureis/revisionproof-build-6977747`
- Cloud Build source object: `gs://revisionproof-agentic-2026-kan-media/cloud-build-source/1787672298.368003-b9106cb4bde344c09b0d7c92f97e17a9.tgz`
- Cloud Build ID: `354696e9-0fdc-451c-9e69-cf55184ea63f`
- Build status: `SUCCESS`
- Build create/start/finish: `2026-08-25T15:38:20Z` / `2026-08-25T15:38:21Z` / `2026-08-25T15:45:00Z`
- Image tag: `us-central1-docker.pkg.dev/revisionproof-agentic-2026-kan/revisionproof/revisionproof-staging:354696e9-0fdc-451c-9e69-cf55184ea63f`
- Image digest: `sha256:d8b4daad7107428776de4339726ba45fc32f60cee204ddf36a1d443f1cba8dfc`
- Cloud Run service: `revisionproof-staging`
- Revision: `revisionproof-staging-00003-q56`
- Traffic: 100% to `revisionproof-staging-00003-q56`
- Service URL: `https://revisionproof-staging-sdixpvvwoq-uc.a.run.app`
- Runtime service account: `revisionproof-runtime@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`
- Capacity: 2 CPU, 4 GiB, concurrency 8, min 1, max 1, request timeout 300 seconds
- Runtime controls: `REVISIONPROOF_MAX_NEW_RUNS_PER_MINUTE=12`, `REVISIONPROOF_MAX_VERIFICATION_ATTEMPTS_PER_RUN=6`
- Runtime truth: `FIXTURE`, mutable, `live_ready=false`, `integration_execution_verified=false`
- ClickHouse resources and LIVE secrets: not created in this phase

The service remains covered by the project-scoped KRW 30,000 alert budget recorded in the 2026-08-25 inventory. That budget is not a hard spending cap.

## Inventory and cleanup evidence

The guarded inventory completed with exit code 0 and wrote 458 lines to:

```text
/home/secureis/revisionproof-inventory-6977747.txt
```

The guarded cleanup script completed in dry-run mode with exit code 0 and wrote:

```text
/home/secureis/revisionproof-cleanup-dry-run-6977747.txt
```

Its exact target set is limited to:

- project `revisionproof-agentic-2026-kan`
- Cloud Run service `revisionproof-staging` in `us-central1`
- Artifact Registry repository `revisionproof` in `us-central1`
- bucket `gs://revisionproof-agentic-2026-kan-media` and its lifecycle-managed objects
- exact legacy build bucket `gs://revisionproof-agentic-2026-kan_cloudbuild`, only if it exists and ownership checks pass
- the two future labeled RevisionProof ClickHouse secrets, if present
- service accounts `revisionproof-runtime` and `revisionproof-build`
- project-scoped budget `RevisionProof revisionproof-agentic-2026-kan`

Always select and verify the exact Cloud Shell identity before inventory or cleanup:

```bash
gcloud config set account secureis@gmail.com
gcloud config set project revisionproof-agentic-2026-kan
gcloud config get-value account
gcloud config get-value project
bash infra/gcp/inventory.sh infra/gcp/foundation.env
bash infra/gcp/cleanup.sh infra/gcp/foundation.env revisionproof-agentic-2026-kan
```

Do not export `CLOUDSDK_CORE_ACCOUNT`; the guarded scripts reject delegated account overrides. A Cloud Shell session can occasionally lose its active account or fail token refresh with `metadata server ... missing 'email' field`. In that case, stop, reauthorize the existing `secureis@gmail.com` Cloud Shell session, and rerun the four preflight commands. Never substitute another authenticated account or project.

Destructive cleanup is intentionally not run. After reviewing the inventory, the exact command is:

```bash
gcloud config set account secureis@gmail.com
gcloud config set project revisionproof-agentic-2026-kan
gcloud config get-value account
gcloud config get-value project
bash infra/gcp/cleanup.sh infra/gcp/foundation.env revisionproof-agentic-2026-kan --execute
```

The script leaves billing linked, enabled APIs enabled, and the project active. Full project deletion remains a separate manual decision.

## Non-billable Cloud Shell working files

The archive, build directory, inventory, and dry-run output above remain in the `secureis` Cloud Shell home directory for audit. The failed private Git clone may also have left `/home/secureis/revisionproof-6977747`; inspect it before any removal. These paths are not GCP project resources and are not removed by `infra/gcp/cleanup.sh`.

## LIVE hardening IAM delta, 2026-08-26

These changes were applied after selecting `secureis@gmail.com` and `revisionproof-agentic-2026-kan`, with exact RevisionProof resource names:

- Runtime bucket binding removed: `roles/storage.objectAdmin`.
- Runtime bucket bindings present: `roles/storage.objectCreator` and `roles/storage.objectViewer` on `gs://revisionproof-agentic-2026-kan-media` only.
- Build project binding removed: `roles/run.admin`.
- Custom role created: `projects/revisionproof-agentic-2026-kan/roles/revisionproofCloudRunDeployer`, stage `GA`.
- The custom role contains 16 permissions: project lookup; Cloud Run location, operation, configuration, revision, route, and service reads; service create/update; and service IAM policy get/set.
- Build project binding present: the custom role above for `revisionproof-build@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`.
- Historical note: this IAM checkpoint preceded creation of the two current RevisionProof ClickHouse secrets and the dedicated ClickHouse service.
- ScopeShift and every other project were left unchanged.

The current deployment is the 2026-09-02 LIVE recovery revision recorded at the top of this file. The older LIVE and FIXTURE facts remain as a dated audit trail.
