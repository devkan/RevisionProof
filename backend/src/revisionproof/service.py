from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import threading
from collections import deque
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import UTC, datetime
from time import monotonic
from typing import BinaryIO

from revisionproof.assets import require_demo_asset
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    LockedElement,
    ParsedFeedback,
    PatchCandidate,
    RevisionNote,
    RevisionSpec,
    RunSnapshot,
    RunState,
    SafetyClassification,
    TimeRange,
    VerificationManifest,
    VerificationProof,
)
from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter
from revisionproof.ids import new_ulid
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.preview import generate_preview
from revisionproof.media.probe import probe_media, validate_hackathon_media
from revisionproof.repository import InMemoryRunRepository
from revisionproof.settings import Settings
from revisionproof.state_machine import assert_transition
from revisionproof.verification.metrics import write_frame_png
from revisionproof.verification.service import (
    AUDIO_PEAK_LIMIT_DBFS,
    AUDIO_RMS_TOLERANCE_DB,
    CTA_REQUIRED_RATIO,
    CTA_ROI,
    CTA_SIMILARITY_THRESHOLD,
    PATCH_REQUIRED_RATIO,
    PATCH_SIMILARITY_THRESHOLD,
    PATCH_WINNER_MARGIN,
    DeterministicVerifier,
    apply_mcp_feature_diff,
    mark_proof_not_checked,
)


class RevisionProofService:
    def __init__(self, settings: Settings, repository: InMemoryRunRepository) -> None:
        self.settings = settings
        self.repository = repository
        self.executor = MediaExecutor(settings.ffmpeg_timeout_seconds)
        self.verifier = DeterministicVerifier(self.executor)
        self.fixture_interpreter = FixtureInterpreter()
        self.fixture_locator = FixtureEvidenceLocator()
        self._media_slot = threading.Lock()
        self._create_idempotency_locks: dict[str, asyncio.Lock] = {}
        self._create_idempotency_waiters: dict[str, int] = {}
        self._create_idempotency_locks_guard = threading.Lock()
        self._create_timestamps: deque[float] = deque()
        self._create_rate_lock = threading.Lock()

    def _transition(self, snapshot: RunSnapshot, target: RunState, message: str) -> None:
        assert_transition(snapshot.state, target)
        snapshot.state = target
        snapshot.retryable = target is RunState.FAILED
        self.repository.append_event(snapshot.run_id, target, message)

    @contextmanager
    def _exclusive_media_pipeline(self) -> Iterator[None]:
        if not self._media_slot.acquire(blocking=False):
            raise ValueError("media pipeline is busy; retry this request")
        try:
            yield
        finally:
            self._media_slot.release()

    def _assert_mutable_mode(self) -> None:
        if self.settings.mode is ExecutionMode.OFFLINE_REHEARSAL:
            raise ValueError("OFFLINE_REHEARSAL is a read-only recorded replay")
        if self.settings.mode is ExecutionMode.UNAVAILABLE:
            raise ValueError("runtime integrations are unavailable")

    @staticmethod
    def _validate_idempotency_key(key: str | None) -> str | None:
        if key is not None and not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", key):
            raise ValueError("Idempotency-Key must contain 8-128 safe characters")
        return key

    @staticmethod
    def _fingerprint(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @asynccontextmanager
    async def _create_idempotency_lock(self, key: str) -> AsyncIterator[None]:
        with self._create_idempotency_locks_guard:
            lock = self._create_idempotency_locks.setdefault(key, asyncio.Lock())
            self._create_idempotency_waiters[key] = self._create_idempotency_waiters.get(key, 0) + 1
        try:
            async with lock:
                yield
        finally:
            with self._create_idempotency_locks_guard:
                remaining = self._create_idempotency_waiters[key] - 1
                if remaining:
                    self._create_idempotency_waiters[key] = remaining
                else:
                    self._create_idempotency_waiters.pop(key, None)
                    self._create_idempotency_locks.pop(key, None)

    def _record_new_run(self) -> None:
        now = monotonic()
        with self._create_rate_lock:
            while self._create_timestamps and self._create_timestamps[0] <= now - 60:
                self._create_timestamps.popleft()
            if len(self._create_timestamps) >= self.settings.max_new_runs_per_minute:
                raise ValueError("new run rate limit reached; retry in one minute")
            self._create_timestamps.append(now)

    @staticmethod
    def _feedback_from_notes(snapshot: RunSnapshot, source: str) -> ParsedFeedback | None:
        note = next(
            (
                item
                for item in snapshot.notes
                if item.classification is SafetyClassification.AUTO_PREVIEWABLE
            ),
            None,
        )
        if note is None or note.target_phrase is None:
            return None
        return ParsedFeedback(
            raw_text=note.raw_text,
            intent=note.intent,
            target_phrase=note.target_phrase,
            rationale=note.rationale,
            interpreter_source=source,
        )

    async def create_run(
        self, request: CreateRunRequest, idempotency_key: str | None = None
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = self._fingerprint(request.model_dump_json())
        if key is not None:
            async with self._create_idempotency_lock(key):
                replay = self.repository.recall_idempotent("create_run", key, fingerprint)
                if replay is not None:
                    return replay
                return await self._create_run_once(request, key, fingerprint)
        return await self._create_run_once(request, key, fingerprint)

    async def _create_run_once(
        self, request: CreateRunRequest, key: str | None, fingerprint: str
    ) -> RunSnapshot:
        replay = self.repository.recall_idempotent("create_run", key, fingerprint)
        if replay is not None:
            return replay
        self._record_new_run()
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
            source_feedback=request.feedback,
        )
        self.repository.create(snapshot, source_path)

        if self.settings.mode is ExecutionMode.FIXTURE:
            snapshot.notes = self.fixture_interpreter.interpret_many(request.feedback)
            snapshot.feedback = self._feedback_from_notes(snapshot, "fixture.interpreter")
            self._transition(
                snapshot,
                RunState.NOTES_PARSED,
                "Feedback classified by fixture adapter; unsupported notes held back",
            )
            if snapshot.feedback is None:
                self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
                return snapshot
            snapshot.evidence = self.fixture_locator.locate(snapshot.feedback)[:3]
            self._transition(
                snapshot,
                RunState.EVIDENCE_ANCHORED,
                "Evidence anchored by fixture segment index",
            )
            self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
            return snapshot
        if self.settings.mode is ExecutionMode.LIVE:
            if self.settings.live_missing_settings:
                snapshot.error = "Missing live settings: " + ", ".join(
                    self.settings.live_missing_settings
                )
                self._transition(snapshot, RunState.FAILED, snapshot.error)
                self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
                return snapshot
            try:
                await self._run_live_interpretation(snapshot, request.feedback)
            except Exception:
                snapshot.error = "Live interpretation or evidence lookup failed"
                self._transition(snapshot, RunState.FAILED, snapshot.error)
            self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
            return snapshot
        raise ValueError("execution mode cannot create runs")

    async def retry_live_interpretation(
        self, run_id: str, idempotency_key: str | None = None
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        if self.settings.mode is not ExecutionMode.LIVE:
            raise ValueError("interpretation retry is only available in LIVE mode")
        key = self._validate_idempotency_key(idempotency_key)
        lock_key = f"retry:{run_id}"
        async with self._create_idempotency_lock(lock_key):
            fingerprint = self._fingerprint(run_id)
            replay = self.repository.recall_idempotent(lock_key, key, fingerprint)
            if replay is not None:
                return replay
            snapshot = self.repository.get(run_id)
            if snapshot.state is not RunState.FAILED or not snapshot.retryable:
                raise ValueError("interpretation retry requires a retryable FAILED run")
            if not snapshot.source_feedback:
                raise ValueError("original feedback is unavailable for retry")
            if self.settings.live_missing_settings:
                raise ValueError(
                    "live settings are incomplete: "
                    + ", ".join(self.settings.live_missing_settings)
                )
            snapshot.notes = []
            snapshot.feedback = None
            snapshot.evidence = []
            snapshot.error = None
            self._transition(snapshot, RunState.INDEXED, "Retrying preserved source feedback")
            try:
                await self._run_live_interpretation(snapshot, snapshot.source_feedback)
            except Exception:
                snapshot.error = "Live interpretation or evidence lookup failed"
                self._transition(snapshot, RunState.FAILED, snapshot.error)
            self.repository.remember_idempotent(lock_key, key, fingerprint, run_id)
            return snapshot

    async def _run_live_interpretation(self, snapshot: RunSnapshot, raw_feedback: str) -> None:
        from revisionproof.evidence.live import (
            LiveEvidenceLocator,
            McpClickHouseReader,
            VertexGeminiInterpreter,
        )

        interpreter = VertexGeminiInterpreter(self.settings)
        snapshot.notes = await interpreter.interpret_many(raw_feedback)
        snapshot.feedback = self._feedback_from_notes(snapshot, "google.vertex.gemini")
        self._transition(
            snapshot,
            RunState.NOTES_PARSED,
            "Feedback classified by Vertex Gemini; unsupported notes held back",
        )
        if snapshot.feedback is None:
            return
        locator = LiveEvidenceLocator(
            self.settings, McpClickHouseReader(self.settings), interpreter
        )
        anchors = await locator.locate(snapshot.asset.asset_id, snapshot.feedback)
        if anchors[0].score < 0.82:
            auto_index = next(
                index
                for index, note in enumerate(snapshot.notes)
                if note.classification is SafetyClassification.AUTO_PREVIEWABLE
            )
            auto_note = snapshot.notes[auto_index]
            snapshot.notes[auto_index] = RevisionNote(
                note_id=auto_note.note_id,
                raw_text=auto_note.raw_text,
                intent=auto_note.intent,
                classification=SafetyClassification.NEEDS_CLARIFICATION,
                confidence=max(0.55, min(0.81, anchors[0].score)),
                rationale="Scene evidence confidence is too low for automatic preview generation.",
                clarification_question=("Which exact scene should receive the center punch-in?"),
            )
            snapshot.feedback = None
            self.repository.append_event(
                snapshot.run_id,
                RunState.NOTES_PARSED,
                "Evidence score below 0.82; automatic preview held for clarification",
            )
            return
        snapshot.evidence = anchors
        self._transition(
            snapshot,
            RunState.EVIDENCE_ANCHORED,
            "Evidence selected through mcp-clickhouse.run_query",
        )

    def generate_previews(self, run_id: str, idempotency_key: str | None = None) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = self._fingerprint(run_id)
        with self.repository.locked(run_id):
            replay = self.repository.recall_idempotent(f"{run_id}:previews", key, fingerprint)
            if replay is not None:
                return replay
            with self._exclusive_media_pipeline():
                snapshot = self._generate_previews_locked(run_id)
                self.repository.remember_idempotent(
                    f"{run_id}:previews", key, fingerprint, run_id
                )
                return snapshot

    def _generate_previews_locked(self, run_id: str) -> RunSnapshot:
        snapshot = self.repository.get(run_id)
        if snapshot.state is not RunState.EVIDENCE_ANCHORED:
            raise ValueError("previews require EVIDENCE_ANCHORED state")
        anchor = snapshot.evidence[0]
        anchor_duration = anchor.time_range.end_seconds - anchor.time_range.start_seconds
        preview_duration = min(8.0, max(4.0, anchor_duration))
        midpoint = (anchor.time_range.start_seconds + anchor.time_range.end_seconds) / 2
        preview_start = max(
            0.0,
            min(
                midpoint - preview_duration / 2, snapshot.asset.duration_seconds - preview_duration
            ),
        )
        preview_range = TimeRange(
            start_seconds=preview_start,
            end_seconds=preview_start + preview_duration,
        )
        preview_dir = self.settings.runtime_dir / "runs" / run_id / "previews"
        candidates = [
            PatchCandidate(
                candidate_id="A",
                scale=1.05,
                time_range=preview_range,
                preview_url=f"/media/runs/{run_id}/previews/A.mp4",
            ),
            PatchCandidate(
                candidate_id="B",
                scale=1.12,
                time_range=preview_range,
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

    def approve(
        self,
        run_id: str,
        request: ApprovalRequest,
        idempotency_key: str | None = None,
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = self._fingerprint(request.model_dump_json())
        with self.repository.locked(run_id):
            replay = self.repository.recall_idempotent(f"{run_id}:approval", key, fingerprint)
            if replay is not None:
                return replay
            snapshot = self._approve_locked(run_id, request)
            self.repository.remember_idempotent(f"{run_id}:approval", key, fingerprint, run_id)
            return snapshot

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
            verification_manifest=[
                VerificationManifest(
                    check_id="approved_patch",
                    time_range=candidate.time_range,
                    threshold={
                        "minimum_similarity": PATCH_SIMILARITY_THRESHOLD,
                        "minimum_winner_margin": PATCH_WINNER_MARGIN,
                        "minimum_passing_ratio": PATCH_REQUIRED_RATIO,
                    },
                ),
                VerificationManifest(
                    check_id="locked_cta",
                    time_range=TimeRange(start_seconds=24, end_seconds=29),
                    roi=CTA_ROI,
                    threshold={
                        "minimum_frame_similarity": CTA_SIMILARITY_THRESHOLD,
                        "minimum_passing_ratio": CTA_REQUIRED_RATIO,
                    },
                ),
                VerificationManifest(
                    check_id="locked_audio",
                    time_range=TimeRange(start_seconds=0, end_seconds=30),
                    threshold={
                        "maximum_rms_delta_db": AUDIO_RMS_TOLERANCE_DB,
                        "maximum_peak_dbfs": AUDIO_PEAK_LIMIT_DBFS,
                    },
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
        if snapshot.spec is None:
            raise RuntimeError("immutable spec is missing")
        checked_at = proof.generated_at
        baseline_proof = self.verifier.verify(
            source=self.repository.source_path(snapshot.run_id),
            candidate=self.repository.source_path(snapshot.run_id),
            spec=snapshot.spec,
            version_label="v1",
        )

        def feature_values(source_proof: VerificationProof) -> dict[str, float]:
            checks = {item.check_id: item for item in source_proof.checks}
            return {
                "patch_similarity": float(
                    checks["approved_patch"].measured["normalized_similarity"]
                ),
                "patch_passing_ratio": float(checks["approved_patch"].measured["ratio"]),
                "patch_winner_margin": float(
                    checks["approved_patch"].measured["minimum_winner_margin_observed"]
                ),
                "cta_passing_ratio": float(checks["locked_cta"].measured["ratio"]),
                "audio_rms_dbfs": float(checks["locked_audio"].measured["candidate_rms_dbfs"]),
                "audio_peak_dbfs": float(checks["locked_audio"].measured["candidate_peak_dbfs"]),
            }

        current_values = feature_values(proof)
        baseline_values = feature_values(baseline_proof)
        patch_range = snapshot.spec.manifest_for("approved_patch").time_range
        cta_range = snapshot.spec.manifest_for("locked_cta").time_range
        audio_range = snapshot.spec.manifest_for("locked_audio").time_range
        feature_ranges = {
            "patch_similarity": patch_range,
            "patch_passing_ratio": patch_range,
            "patch_winner_margin": patch_range,
            "cta_passing_ratio": cta_range,
            "audio_rms_dbfs": audio_range,
            "audio_peak_dbfs": audio_range,
        }
        rows = []
        for label, values in (("v1", baseline_values), (version_label, current_values)):
            rows.extend(
                [
                    snapshot.run_id,
                    label,
                    name,
                    value,
                    feature_ranges[name].start_seconds,
                    feature_ranges[name].end_seconds,
                    checked_at,
                ]
                for name, value in values.items()
            )
        writer = ClickHouseWriter(self.settings)
        writer.insert_features(rows)
        GcsObjectStore(self.settings).upload(
            destination, f"runs/{snapshot.run_id}/versions/{version_label}.mp4"
        )
        reader = McpClickHouseReader(self.settings)
        query = build_version_diff_query(snapshot.run_id, version_label, "v1")
        try:
            diff_rows = asyncio.run(reader.run_query(query))
            if not diff_rows:
                raise RuntimeError("mcp-clickhouse version feature diff returned no rows")
            apply_mcp_feature_diff(proof, snapshot.spec, diff_rows)
            self.repository.append_event(
                snapshot.run_id,
                RunState.VERIFYING,
                "Release verdict recomputed from mcp-clickhouse feature diff",
            )
        except Exception:
            mark_proof_not_checked(proof, "MCP_FEATURE_DIFF_UNAVAILABLE")
            self.repository.append_event(
                snapshot.run_id,
                RunState.VERIFYING,
                "MCP feature diff unavailable; release failed closed",
            )
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
                    proof.generated_at,
                ]
                for check in proof.checks
            ]
        )

    def _attach_cta_evidence(self, snapshot: RunSnapshot, destination, version_label: str) -> None:
        if snapshot.proof is None or snapshot.spec is None:
            raise RuntimeError("verification proof or immutable spec is missing")
        manifest = snapshot.spec.manifest_for("locked_cta")
        second = (manifest.time_range.start_seconds + manifest.time_range.end_seconds) / 2
        evidence_dir = self.settings.runtime_dir / "runs" / snapshot.run_id / "evidence"
        baseline_name = "baseline-cta.png"
        current_name = f"{version_label}-cta.png"
        baseline_path = evidence_dir / baseline_name
        if not baseline_path.exists():
            write_frame_png(self.repository.source_path(snapshot.run_id), second, baseline_path)
        write_frame_png(destination, second, evidence_dir / current_name)
        check = next(item for item in snapshot.proof.checks if item.check_id == "locked_cta")
        check.evidence_urls = [
            f"/media/runs/{snapshot.run_id}/evidence/{baseline_name}",
            f"/media/runs/{snapshot.run_id}/evidence/{current_name}",
        ]

    def upload_and_verify(
        self,
        *,
        run_id: str,
        version_label: str,
        stream: BinaryIO,
        size: int,
        idempotency_key: str | None = None,
        content_sha256: str | None = None,
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        if key is not None and not (
            content_sha256 and re.fullmatch(r"[a-fA-F0-9]{64}", content_sha256)
        ):
            raise ValueError("X-Content-SHA256 is required with an upload Idempotency-Key")
        if key is not None:
            assert content_sha256 is not None
            position = stream.tell()
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
            stream.seek(position)
            if digest.hexdigest() != content_sha256.lower():
                raise ValueError("X-Content-SHA256 does not match the uploaded file")
        fingerprint = self._fingerprint(f"{version_label}:{size}:{(content_sha256 or '').lower()}")
        with self.repository.locked(run_id):
            replay = self.repository.recall_idempotent(f"{run_id}:version", key, fingerprint)
            if replay is not None:
                return replay
            with self._exclusive_media_pipeline():
                snapshot = self._upload_and_verify_locked(
                    run_id=run_id,
                    version_label=version_label,
                    stream=stream,
                    size=size,
                )
                self.repository.remember_idempotent(
                    f"{run_id}:version", key, fingerprint, run_id
                )
                return snapshot

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
            self._attach_cta_evidence(snapshot, destination, version_label)
            if self.settings.mode is ExecutionMode.LIVE:
                self._persist_live_verification(snapshot, destination, version_label)
            snapshot.error = None
            snapshot.delivery_approved = False
            target = RunState.READY if snapshot.proof.publish_allowed else RunState.BLOCKED
            self._transition(
                snapshot,
                target,
                "All checks passed; publish ready"
                if target is RunState.READY
                else "At least one invariant failed; publish blocked",
            )
        except Exception:
            snapshot.error = "Media validation or verification failed"
            if snapshot.state in {RunState.VERSION_UPLOADED, RunState.VERIFYING}:
                self._transition(snapshot, RunState.FAILED, "Verification failed closed")
            if destination.exists():
                destination.unlink()
            raise
        return snapshot

    def approve_for_delivery(self, run_id: str, idempotency_key: str | None = None) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = self._fingerprint(run_id)
        with self.repository.locked(run_id):
            replay = self.repository.recall_idempotent(
                f"{run_id}:delivery-approval", key, fingerprint
            )
            if replay is not None:
                return replay
            snapshot = self.repository.get(run_id)
            if (
                snapshot.state is not RunState.READY
                or snapshot.proof is None
                or not snapshot.proof.publish_allowed
            ):
                raise ValueError("delivery approval requires a READY proof with all checks passed")
            if not snapshot.delivery_approved:
                snapshot.delivery_approved = True
                self.repository.append_event(
                    run_id, RunState.READY, "Human approved the verified version for delivery"
                )
            self.repository.remember_idempotent(
                f"{run_id}:delivery-approval", key, fingerprint, run_id
            )
            return snapshot
