# Infrastructure inventory - 2026-08-26 deployment delta

This file records the resources and artifacts added after the 2026-08-25 foundation inventory. Read both files before modifying or removing infrastructure.

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

## Google Cloud deployment

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

Dry-run:

```bash
export CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com
export CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan
bash infra/gcp/inventory.sh infra/gcp/foundation.env
bash infra/gcp/cleanup.sh infra/gcp/foundation.env revisionproof-agentic-2026-kan
```

Destructive cleanup is intentionally not run. After reviewing the inventory, the exact command is:

```bash
export CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com
export CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan
bash infra/gcp/cleanup.sh infra/gcp/foundation.env revisionproof-agentic-2026-kan --execute
```

The script leaves billing linked, enabled APIs enabled, and the project active. Full project deletion remains a separate manual decision.

## Non-billable Cloud Shell working files

The archive, build directory, inventory, and dry-run output above remain in the `secureis` Cloud Shell home directory for audit. The failed private Git clone may also have left `/home/secureis/revisionproof-6977747`; inspect it before any removal. These paths are not GCP project resources and are not removed by `infra/gcp/cleanup.sh`.

## LIVE hardening IAM delta, 2026-08-26

These changes were applied with `CLOUDSDK_CORE_ACCOUNT=secureis@gmail.com`, `CLOUDSDK_CORE_PROJECT=revisionproof-agentic-2026-kan`, and exact RevisionProof resource names:

- Runtime bucket binding removed: `roles/storage.objectAdmin`.
- Runtime bucket bindings present: `roles/storage.objectCreator` and `roles/storage.objectViewer` on `gs://revisionproof-agentic-2026-kan-media` only.
- Build project binding removed: `roles/run.admin`.
- Custom role created: `projects/revisionproof-agentic-2026-kan/roles/revisionproofCloudRunDeployer`, stage `GA`.
- The custom role contains 16 permissions: project lookup; Cloud Run location, operation, configuration, revision, route, and service reads; service create/update; and service IAM policy get/set.
- Build project binding present: the custom role above for `revisionproof-build@revisionproof-agentic-2026-kan.iam.gserviceaccount.com`.
- Secret Manager query found no RevisionProof-labeled secrets. No secret or ClickHouse Cloud resource was created.
- ScopeShift and every other project were left unchanged.

The currently deployed Cloud Run revision remains `revisionproof-staging-00003-q56` in FIXTURE mode. The IAM delta does not claim that the uncommitted LIVE source or ClickHouse path is deployed.
