from __future__ import annotations

import asyncio
import json
import re
import shutil
from datetime import UTC, datetime
from typing import BinaryIO

from revisionproof.assets import require_demo_asset
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    LockedElement,
    PatchCandidate,
    RevisionSpec,
    RunSnapshot,
    RunState,
    TimeRange,
)
from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter
from revisionproof.ids import new_ulid
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.preview import generate_preview
from revisionproof.media.probe import probe_media, validate_hackathon_media
from revisionproof.repository import InMemoryRunRepository
from revisionproof.settings import Settings
from revisionproof.state_machine import assert_transition
from revisionproof.verification.service import DeterministicVerifier


class RevisionProofService:
    def __init__(self, settings: Settings, repository: InMemoryRunRepository) -> None:
        self.settings = settings
        self.repository = repository
        self.executor = MediaExecutor(settings.ffmpeg_timeout_seconds)
        self.verifier = DeterministicVerifier(self.executor)
        self.fixture_interpreter = FixtureInterpreter()
        self.fixture_locator = FixtureEvidenceLocator()

    def _transition(self, snapshot: RunSnapshot, target: RunState, message: str) -> None:
        assert_transition(snapshot.state, target)
        snapshot.state = target
        self.repository.append_event(snapshot.run_id, target, message)

    async def create_run(self, request: CreateRunRequest) -> RunSnapshot:
        asset, source_path = await asyncio.to_thread(
            require_demo_asset,
            request.asset_id,
            self.settings.runtime_dir,
            self.executor,
        )
        run_id = new_ulid()
        snapshot = RunSnapshot(
            run_id=run_id,
            asset=asset,
            mode=self.settings.mode,
            state=RunState.INDEXED,
        )
        self.repository.create(snapshot, source_path)

        if self.settings.mode in {ExecutionMode.FIXTURE, ExecutionMode.OFFLINE_REHEARSAL}:
            snapshot.feedback = self.fixture_interpreter.interpret(request.feedback)
            self._transition(
                snapshot, RunState.NOTES_PARSED, "Feedback interpreted by fixture adapter"
            )
            snapshot.evidence = self.fixture_locator.locate(snapshot.feedback)[:3]
            self._transition(
                snapshot,
                RunState.EVIDENCE_ANCHORED,
                "Evidence anchored by fixture segment index",
            )
            return snapshot
        if self.settings.mode is ExecutionMode.LIVE:
            if self.settings.live_missing_settings:
                snapshot.error = "Missing live settings: " + ", ".join(
                    self.settings.live_missing_settings
                )
                self._transition(snapshot, RunState.FAILED, snapshot.error)
                return snapshot
            try:
                await self._run_live_interpretation(snapshot, request.feedback)
            except Exception:
                snapshot.error = "Live interpretation or evidence lookup failed"
                self._transition(snapshot, RunState.FAILED, snapshot.error)
            return snapshot
        snapshot.error = "Execution mode is unavailable"
        self._transition(snapshot, RunState.FAILED, snapshot.error)
        return snapshot

    async def _run_live_interpretation(self, snapshot: RunSnapshot, raw_feedback: str) -> None:
        from revisionproof.evidence.live import (
            LiveEvidenceLocator,
            McpClickHouseReader,
            VertexGeminiInterpreter,
        )

        interpreter = VertexGeminiInterpreter(self.settings)
        snapshot.feedback = await interpreter.interpret(raw_feedback)
        self._transition(snapshot, RunState.NOTES_PARSED, "Feedback interpreted by Vertex Gemini")
        locator = LiveEvidenceLocator(
            self.settings, McpClickHouseReader(self.settings), interpreter
        )
        snapshot.evidence = await locator.locate(snapshot.asset.asset_id, snapshot.feedback)
        self._transition(
            snapshot,
            RunState.EVIDENCE_ANCHORED,
            "Evidence selected through mcp-clickhouse.run_query",
        )

    def generate_previews(self, run_id: str) -> RunSnapshot:
        with self.repository.locked(run_id):
            return self._generate_previews_locked(run_id)

    def _generate_previews_locked(self, run_id: str) -> RunSnapshot:
        snapshot = self.repository.get(run_id)
        if snapshot.state is not RunState.EVIDENCE_ANCHORED:
            raise ValueError("previews require EVIDENCE_ANCHORED state")
        anchor = snapshot.evidence[0]
        preview_dir = self.settings.runtime_dir / "runs" / run_id / "previews"
        candidates = [
            PatchCandidate(
                candidate_id="A",
                scale=1.05,
                time_range=anchor.time_range,
                preview_url=f"/media/runs/{run_id}/previews/A.mp4",
            ),
            PatchCandidate(
                candidate_id="B",
                scale=1.12,
                time_range=anchor.time_range,
                preview_url=f"/media/runs/{run_id}/previews/B.mp4",
            ),
        ]
        source = self.repository.source_path(run_id)
        for candidate in candidates:
            generate_preview(
                source=source,
                destination=preview_dir / f"{candidate.candidate_id}.mp4",
                candidate=candidate,
                executor=self.executor,
            )
        snapshot.candidates = candidates
        self._transition(snapshot, RunState.PREVIEWS_READY, "Two constrained previews rendered")
        return snapshot

    def approve(self, run_id: str, request: ApprovalRequest) -> RunSnapshot:
        with self.repository.locked(run_id):
            return self._approve_locked(run_id, request)

    def _approve_locked(self, run_id: str, request: ApprovalRequest) -> RunSnapshot:
        snapshot = self.repository.get(run_id)
        if snapshot.state is not RunState.PREVIEWS_READY:
            raise ValueError("approval requires PREVIEWS_READY state")
        candidate = next(
            (item for item in snapshot.candidates if item.candidate_id == request.candidate_id),
            None,
        )
        if candidate is None:
            raise ValueError("candidate does not exist")
        frozen_spec = RevisionSpec.freeze(
            run_id=run_id,
            asset_id=snapshot.asset.asset_id,
            candidate=candidate,
            evidence=snapshot.evidence,
            locked_elements=[
                LockedElement(
                    element_id="cta_end_card",
                    kind="CTA_OVERLAY",
                    time_range=TimeRange(start_seconds=24, end_seconds=29),
                    description="Bottom-right publish CTA remains visible for the end card.",
                ),
                LockedElement(
                    element_id="master_audio",
                    kind="AUDIO",
                    time_range=TimeRange(start_seconds=0, end_seconds=30),
                    description=(
                        "Master audio RMS may vary by at most 3 dB and peak stays below -1 dBFS."
                    ),
                ),
            ],
            approved_at=datetime.now(UTC),
        )
        if self.settings.mode is ExecutionMode.LIVE:
            from revisionproof.evidence.live import ClickHouseWriter

            ClickHouseWriter(self.settings).insert_spec(
                [
                    run_id,
                    frozen_spec.spec_hash,
                    frozen_spec.model_dump_json(),
                    frozen_spec.approved_at,
                ]
            )
        snapshot.spec = frozen_spec
        self._transition(
            snapshot,
            RunState.HUMAN_APPROVED,
            f"Candidate {candidate.candidate_id} approved; immutable spec frozen",
        )
        return snapshot

    def _persist_live_verification(
        self, snapshot: RunSnapshot, destination, version_label: str
    ) -> None:
        if snapshot.proof is None:
            raise RuntimeError("verification proof is missing")
        from revisionproof.evidence.live import (
            ClickHouseWriter,
            GcsObjectStore,
            McpClickHouseReader,
            build_version_diff_query,
        )

        proof = snapshot.proof
        checked_at = proof.generated_at
        feature_values = {
            "patch_similarity": float(
                next(item for item in proof.checks if item.check_id == "approved_patch").measured[
                    "normalized_similarity"
                ]
            ),
            "cta_passing_ratio": float(
                next(item for item in proof.checks if item.check_id == "locked_cta").measured[
                    "ratio"
                ]
            ),
            "audio_rms_dbfs": float(
                next(item for item in proof.checks if item.check_id == "locked_audio").measured[
                    "candidate_rms_dbfs"
                ]
            ),
        }
        baseline_values = {
            "patch_similarity": 1.0,
            "cta_passing_ratio": 1.0,
            "audio_rms_dbfs": float(
                next(item for item in proof.checks if item.check_id == "locked_audio").measured[
                    "source_rms_dbfs"
                ]
            ),
        }
        rows = [
            [snapshot.run_id, "v1", name, value, 0.0, 30.0, checked_at]
            for name, value in baseline_values.items()
        ] + [
            [snapshot.run_id, version_label, name, value, 0.0, 30.0, checked_at]
            for name, value in feature_values.items()
        ]
        writer = ClickHouseWriter(self.settings)
        writer.insert_features(rows)
        writer.insert_checks(
            [
                [
                    snapshot.run_id,
                    version_label,
                    check.check_id,
                    check.verdict,
                    check.failure_code,
                    json.dumps(check.measured, sort_keys=True),
                    json.dumps(check.threshold, sort_keys=True),
                    checked_at,
                ]
                for check in proof.checks
            ]
        )
        GcsObjectStore(self.settings).upload(
            destination, f"runs/{snapshot.run_id}/versions/{version_label}.mp4"
        )
        reader = McpClickHouseReader(self.settings)
        query = build_version_diff_query(snapshot.run_id, version_label, "v1")
        rows = asyncio.run(reader.run_query(query))
        if not rows:
            raise RuntimeError("mcp-clickhouse version feature diff returned no rows")
        self.repository.append_event(
            snapshot.run_id,
            RunState.VERIFYING,
            "Version feature diff read through mcp-clickhouse.run_query",
        )

    def upload_and_verify(
        self,
        *,
        run_id: str,
        version_label: str,
        stream: BinaryIO,
        size: int,
    ) -> RunSnapshot:
        with self.repository.locked(run_id):
            return self._upload_and_verify_locked(
                run_id=run_id,
                version_label=version_label,
                stream=stream,
                size=size,
            )

    def _upload_and_verify_locked(
        self,
        *,
        run_id: str,
        version_label: str,
        stream: BinaryIO,
        size: int,
    ) -> RunSnapshot:
        snapshot = self.repository.get(run_id)
        if snapshot.state not in {RunState.HUMAN_APPROVED, RunState.BLOCKED, RunState.FAILED}:
            raise ValueError(
                "version upload requires HUMAN_APPROVED, BLOCKED, or retryable FAILED state"
            )
        if snapshot.spec is None:
            raise ValueError("immutable spec is missing")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", version_label):
            raise ValueError(
                "version_label must use 1-64 letters, numbers, dots, dashes, or underscores"
            )
        if size <= 0 or size > self.settings.max_upload_bytes:
            raise ValueError(
                f"upload must be between 1 byte and {self.settings.max_upload_mib} MiB"
            )

        destination = (
            self.settings.runtime_dir / "runs" / run_id / "versions" / f"{version_label}.mp4"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            shutil.copyfileobj(stream, output)
        try:
            info = probe_media(destination, self.executor)
            validate_hackathon_media(info, max_duration_seconds=self.settings.max_duration_seconds)
            self.repository.set_version_path(run_id, destination)
            self._transition(snapshot, RunState.VERSION_UPLOADED, f"{version_label} uploaded")
            self._transition(snapshot, RunState.VERIFYING, "Deterministic verification started")
            snapshot.proof = None
            snapshot.proof = self.verifier.verify(
                source=self.repository.source_path(run_id),
                candidate=destination,
                spec=snapshot.spec,
                version_label=version_label,
            )
            if self.settings.mode is ExecutionMode.LIVE:
                self._persist_live_verification(snapshot, destination, version_label)
            target = RunState.READY if snapshot.proof.publish_allowed else RunState.BLOCKED
            self._transition(
                snapshot,
                target,
                "All checks passed; publish ready"
                if target is RunState.READY
                else "At least one invariant failed; publish blocked",
            )
        except Exception as exc:
            snapshot.error = str(exc)
            if snapshot.state in {RunState.VERSION_UPLOADED, RunState.VERIFYING}:
                self._transition(snapshot, RunState.FAILED, "Verification failed closed")
            if destination.exists():
                destination.unlink()
            raise
        return snapshot
