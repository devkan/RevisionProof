from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import shutil
import tempfile
import threading
from collections import deque
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from queue import Empty, SimpleQueue
from time import monotonic
from typing import BinaryIO

from revisionproof.assets import DEMO_ASSET_ID, require_demo_asset
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    DemoAsset,
    EditCandidate,
    EvidenceAnchor,
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
from revisionproof.editing.logo import save_logo
from revisionproof.editing.models import (
    EditPlan,
    InterpretEditRequest,
    LogoAsset,
    TranscriptionLanguage,
    TranscriptionResult,
)
from revisionproof.editing.transcription import extract_speech_audio, transcribe_with_gemini
from revisionproof.editing.verify import approved_reference
from revisionproof.editing.workflow import plan_previews, review_plan
from revisionproof.evidence.fixture import FixtureEvidenceLocator, FixtureInterpreter
from revisionproof.ids import new_ulid
from revisionproof.intelligence.models import (
    EditMemorySearch,
    MemorySaveResult,
    SceneSearchResult,
    SearchEngine,
)
from revisionproof.intelligence.scene_search import search_fixture_scenes, search_live_scenes
from revisionproof.intelligence.service import RevisionIntelligence
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.preview import generate_full_revision, generate_preview
from revisionproof.media.probe import probe_media, validate_hackathon_media
from revisionproof.media.source import (
    SourceUploadError,
    copy_source,
    interpret_selected_range,
    prepare_source,
    validate_source,
)
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

logger = logging.getLogger(__name__)


def _file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


class RateLimitError(ValueError):
    def __init__(self, message: str, retry_after_seconds: int) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class RevisionProofService:
    def __init__(self, settings: Settings, repository: InMemoryRunRepository) -> None:
        self.settings = settings
        self.repository = repository
        self.executor = MediaExecutor(settings.ffmpeg_timeout_seconds)
        self.verifier = DeterministicVerifier(self.executor)
        self.fixture_interpreter = FixtureInterpreter()
        self.fixture_locator = FixtureEvidenceLocator()
        self.intelligence = RevisionIntelligence(settings)
        self._media_slot = threading.Lock()
        self._create_idempotency_locks: dict[str, asyncio.Lock] = {}
        self._create_idempotency_waiters: dict[str, int] = {}
        self._create_idempotency_locks_guard = threading.Lock()
        self._create_timestamps: deque[float] = deque()
        self._create_rate_lock = threading.Lock()
        self._evicted_run_ids: SimpleQueue[str] = SimpleQueue()
        self._baseline_proofs: dict[str, VerificationProof] = {}
        self._scene_searches: dict[str, tuple[str, str, SceneSearchResult]] = {}
        self._scene_search_lock = threading.Lock()
        self.repository.set_eviction_callback(self._evicted_run_ids.put)

    def _cleanup_evicted_run(self, run_id: str) -> None:
        if not re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", run_id):
            raise RuntimeError("refusing to clean an invalid run id")
        runs_root = (self.settings.runtime_dir / "runs").resolve()
        run_root = (runs_root / run_id).resolve()
        if run_root.parent != runs_root:
            raise RuntimeError("refusing to clean a run path outside the runtime root")
        if run_root.exists():
            shutil.rmtree(run_root)

    async def _cleanup_pending_evictions(self) -> None:
        while True:
            try:
                run_id = self._evicted_run_ids.get_nowait()
            except Empty:
                return
            try:
                self._baseline_proofs.pop(run_id, None)
                self.intelligence.forget_run(run_id)
                await asyncio.to_thread(self._cleanup_evicted_run, run_id)
            except OSError:
                self._evicted_run_ids.put(run_id)
                logger.exception("Evicted run workspace cleanup will be retried: %s", run_id)
                return

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

    async def interpret_edit_plan(self, request: InterpretEditRequest):
        from revisionproof.editing.interpret import interpret_live, interpret_local

        self._assert_mutable_mode()
        self._record_new_run()
        if self.settings.mode is ExecutionMode.LIVE:
            if self.settings.live_missing_settings:
                raise ValueError(
                    "Request interpretation is unavailable. Use the edit controls below."
                )
            try:
                return await interpret_live(request, self.settings)
            except Exception as exc:
                logger.exception("Edit plan interpretation failed")
                raise ValueError(
                    "We could not turn this request into an edit plan. "
                    "Your words are preserved; use the edit buttons below or try again."
                ) from exc
        return interpret_local(request)

    def upload_logo(self, stream: BinaryIO, *, size: int, content_sha256: str) -> LogoAsset:
        self._assert_mutable_mode()
        self._record_new_run()
        with self._exclusive_media_pipeline():
            return save_logo(
                stream,
                self.settings.runtime_dir / "edit-assets",
                size=size,
                limit=self.settings.max_logo_bytes,
                expected_hash=content_sha256,
            )

    async def transcribe_source(
        self,
        *,
        language: TranscriptionLanguage,
        stream: BinaryIO | None,
        size: int,
        content_sha256: str,
        asset_id: str | None,
    ) -> TranscriptionResult:
        self._assert_mutable_mode()
        if self.settings.mode is not ExecutionMode.LIVE:
            raise ValueError(
                "Automatic speech subtitles require the LIVE Google Gemini runtime. "
                "You can still add and edit timed subtitles manually."
            )
        if not self.settings.google_cloud_project:
            raise ValueError("Automatic speech subtitles are unavailable in this runtime.")
        self._record_new_run()
        self.settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="transcription-", dir=self.settings.runtime_dir
        ) as temporary:
            folder = Path(temporary)
            if stream is not None:
                if size <= 0 or size > self.settings.max_upload_bytes:
                    raise SourceUploadError(
                        f"Video is too large or empty. Maximum: {self.settings.max_upload_mb} MB.",
                        413,
                    )
                source = folder / "source.video"
                await asyncio.to_thread(
                    copy_source,
                    stream,
                    source,
                    self.settings.max_upload_bytes,
                    content_sha256,
                )
            elif asset_id:
                _, source = require_demo_asset(asset_id, self.settings.runtime_dir, self.executor)
            else:
                raise SourceUploadError("Choose a video before generating subtitles.")
            try:
                info = await asyncio.to_thread(probe_media, source, self.executor)
            except Exception as exc:
                raise SourceUploadError("This file could not be read as a video.") from exc
            if not 4 <= info.duration_seconds <= self.settings.max_duration_seconds:
                raise SourceUploadError(
                    "Choose a video between 4 and "
                    f"{self.settings.max_duration_seconds} seconds long."
                )
            if info.audio_codec is None:
                raise SourceUploadError(
                    "This video has no audio track. Add timed subtitles manually instead."
                )
            audio = folder / "speech.wav"
            try:
                with self._exclusive_media_pipeline():
                    await asyncio.to_thread(extract_speech_audio, source, audio, self.executor)
                return await transcribe_with_gemini(
                    audio,
                    duration=round(info.duration_seconds, 3),
                    language=language,
                    settings=self.settings,
                )
            except (SourceUploadError, ValueError):
                raise
            except Exception as exc:
                logger.exception("Automatic subtitle transcription failed")
                raise ValueError(
                    "Speech could not be transcribed. Try the language setting again, "
                    "or add timed subtitles manually."
                ) from exc

    async def search_scenes(
        self,
        *,
        query: str,
        stream: BinaryIO | None,
        size: int,
        content_sha256: str,
        asset_id: str | None,
    ) -> SceneSearchResult:
        self._assert_mutable_mode()
        query = query.strip()
        if not 2 <= len(query) <= 500:
            raise ValueError("Describe the scene to find in 2-500 characters.")
        self._record_new_run()
        self.settings.runtime_dir.mkdir(parents=True, exist_ok=True)

        async def execute(source: Path, source_key: str) -> SceneSearchResult:
            try:
                info = await asyncio.to_thread(probe_media, source, self.executor)
                selection = TimeRange(
                    start_seconds=0,
                    end_seconds=min(6, round(info.duration_seconds, 3)),
                )
                validate_source(info, selection, self.settings)
                search_asset_id = new_ulid()
                if self.settings.mode is ExecutionMode.LIVE:
                    if self.settings.live_missing_settings:
                        raise ValueError("Smart scene finder is unavailable in this runtime.")
                    result = await search_live_scenes(
                        source,
                        duration=round(info.duration_seconds, 3),
                        query=query,
                        asset_id=search_asset_id,
                        settings=self.settings,
                    )
                else:
                    result = search_fixture_scenes(
                        round(info.duration_seconds, 3), query, search_asset_id
                    )
            except (SourceUploadError, ValueError):
                raise
            except Exception as exc:
                logger.exception("Smart scene search failed")
                raise ValueError(
                    "Smart scene finder could not finish. Enter a start and end time instead."
                ) from exc
            return result

        if stream is not None:
            if size <= 0 or size > self.settings.max_upload_bytes:
                raise SourceUploadError(
                    f"Video is too large or empty. Maximum: {self.settings.max_upload_mb} MB.",
                    413,
                )
            with tempfile.TemporaryDirectory(
                prefix="scene-search-", dir=self.settings.runtime_dir
            ) as tmp:
                source = Path(tmp) / "source.video"
                source_key = await asyncio.to_thread(
                    copy_source,
                    stream,
                    source,
                    self.settings.max_upload_bytes,
                    content_sha256,
                )
                result = await execute(source, source_key)
        elif asset_id:
            _, source = await asyncio.to_thread(
                require_demo_asset, asset_id, self.settings.runtime_dir, self.executor
            )
            source_key = await asyncio.to_thread(_file_sha256, source)
            result = await execute(source, source_key)
        else:
            raise SourceUploadError("Choose a video before using Smart scene finder.")
        with self._scene_search_lock:
            if len(self._scene_searches) >= 64:
                self._scene_searches.pop(next(iter(self._scene_searches)))
            self._scene_searches[result.search_id] = (asset_id or "upload", source_key, result)
        return result

    def _smart_evidence(
        self,
        *,
        search_id: str | None,
        segment_id: str | None,
        source_key: str,
        sample_asset_id: str | None = None,
    ) -> EvidenceAnchor | None:
        if not search_id and not segment_id:
            return None
        if not search_id or not segment_id:
            raise ValueError("Choose a complete Smart scene finder result.")
        with self._scene_search_lock:
            receipt = self._scene_searches.get(search_id)
        if receipt is None:
            raise ValueError("That scene result expired. Run Smart scene finder again.")
        source_ref, expected_key, result = receipt
        if expected_key != source_key or (sample_asset_id and source_ref != sample_asset_id):
            raise ValueError("The selected scene belongs to a different video.")
        hit = next((item for item in result.matches if item.segment_id == segment_id), None)
        if hit is None:
            raise ValueError("Choose one of the returned scene results.")
        return EvidenceAnchor(
            segment_id=hit.segment_id,
            time_range=TimeRange(start_seconds=hit.start_seconds, end_seconds=hit.end_seconds),
            score=max(0, hit.score),
            transcript=hit.transcript,
            visual_summary=hit.visual_summary,
            source=(
                "mcp-clickhouse.run_query"
                if result.source == "mcp-clickhouse.run_query"
                else "fixture.segment_index"
            ),
        )

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
                raise RateLimitError(
                    "new run rate limit reached; retry in one minute",
                    retry_after_seconds=60,
                )
            self._create_timestamps.append(now)

    @staticmethod
    def _feedback_from_notes(
        snapshot: RunSnapshot,
        source: str,
        selected_note_id: str | None = None,
    ) -> ParsedFeedback | None:
        note = next(
            (
                item
                for item in snapshot.notes
                if item.classification is SafetyClassification.AUTO_PREVIEWABLE
                and (selected_note_id is None or item.note_id == selected_note_id)
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

    async def create_uploaded_run(
        self,
        *,
        stream: BinaryIO,
        size: int,
        filename: str,
        feedback: str,
        selected_range: TimeRange,
        content_sha256: str,
        idempotency_key: str | None,
        edit_plan: EditPlan | None = None,
        scene_search_id: str | None = None,
        scene_segment_id: str | None = None,
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        if not key:
            raise SourceUploadError("An upload request identifier is required.")
        if size <= 0 or size > self.settings.max_upload_bytes:
            raise SourceUploadError(
                f"Video is too large or empty. Maximum: {self.settings.max_upload_mb} MB.", 413
            )
        minimum = 2 if edit_plan is not None else 8
        if not minimum <= len(feedback) <= 2000:
            raise SourceUploadError(f"Describe the edit in {minimum}–2000 characters.")
        self.settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        async with self._create_idempotency_lock("source:" + key):
            with tempfile.TemporaryDirectory(
                prefix="source-upload-", dir=self.settings.runtime_dir
            ) as temporary:
                incoming = Path(temporary) / "incoming.video"
                with self._exclusive_media_pipeline():
                    digest = await asyncio.to_thread(
                        copy_source,
                        stream,
                        incoming,
                        self.settings.max_upload_bytes,
                        content_sha256,
                    )
                    smart_evidence = self._smart_evidence(
                        search_id=scene_search_id,
                        segment_id=scene_segment_id,
                        source_key=digest,
                    )
                    fingerprint = self._fingerprint(
                        json.dumps(
                            [
                                digest,
                                feedback,
                                selected_range.model_dump(),
                                edit_plan.model_dump() if edit_plan else None,
                                scene_search_id,
                                scene_segment_id,
                            ],
                            sort_keys=True,
                        )
                    )
                    replay = self.repository.recall_idempotent("upload_source", key, fingerprint)
                    if replay is not None:
                        return replay
                    self._record_new_run()
                    prepared = Path(temporary) / "source.mp4"
                    info = await asyncio.to_thread(
                        prepare_source,
                        incoming,
                        prepared,
                        selected_range,
                        self.settings,
                        self.executor,
                    )
                run_id = new_ulid()
                source_path = self.settings.runtime_dir / "runs" / run_id / "source" / "source.mp4"
                title = filename.replace("\\", "/").split("/")[-1]
                title = "".join(c for c in title if c.isprintable())[:160] or "Uploaded video"
                snapshot = RunSnapshot(
                    run_id=run_id,
                    mode=self.settings.mode,
                    state=RunState.INDEXED,
                    selected_range=selected_range,
                    source_feedback=feedback,
                    edit_plan=edit_plan,
                    asset=DemoAsset(
                        asset_id=run_id,
                        title=title,
                        source_kind="upload",
                        source_url=f"/api/runs/{run_id}/source-video",
                        duration_seconds=info.duration_seconds,
                        width=info.width,
                        height=info.height,
                        codec="h264/aac",
                    ),
                )
                if smart_evidence is not None:
                    snapshot.evidence = [smart_evidence]
                self.repository.create(snapshot, source_path, active=True)
                try:
                    source_path.parent.mkdir(parents=True, exist_ok=True)
                    prepared.replace(source_path)
                    await self._cleanup_pending_evictions()
                    await self._interpret_uploaded(snapshot, feedback)
                except Exception:
                    logger.exception("Uploaded video review failed for %s", run_id)
                    snapshot.error = (
                        "Video review failed. Your uploaded video and notes are "
                        "preserved; retry review."
                    )
                    self._transition(
                        snapshot, RunState.FAILED, "Uploaded video review failed closed"
                    )
                finally:
                    self.repository.release_active(run_id)
                self.repository.remember_idempotent("upload_source", key, fingerprint, run_id)
                return snapshot

    async def _interpret_uploaded(self, snapshot: RunSnapshot, feedback: str) -> None:
        if snapshot.edit_plan is not None:
            await asyncio.to_thread(review_plan, self, snapshot, snapshot.edit_plan)
            return
        selected = snapshot.selected_range
        if selected is None:
            raise ValueError("Uploaded videos require an explicit selected section")
        if self.settings.mode is ExecutionMode.LIVE:
            from revisionproof.evidence.live import VertexGeminiInterpreter

            if self.settings.live_missing_settings:
                raise RuntimeError("LIVE integrations are not configured")
            snapshot.notes = await VertexGeminiInterpreter(self.settings).interpret_many(
                feedback, selected_range=selected
            )
            source = "google.vertex.gemini"
        else:
            snapshot.notes = interpret_selected_range(feedback)
            source = "local.range_rules"
        snapshot.feedback = self._feedback_from_notes(snapshot, source)
        self._transition(
            snapshot,
            RunState.NOTES_PARSED,
            "Requests reviewed for your uploaded video; timing is selected by you",
        )
        if snapshot.feedback is None:
            return
        snapshot.evidence = [
            EvidenceAnchor(
                segment_id=f"selected_{snapshot.run_id}",
                time_range=selected,
                score=1,
                transcript="",
                visual_summary=(
                    "User-selected section of the uploaded video. "
                    "No speech transcription or scene recognition is claimed."
                ),
                source="user.selected_range",
            )
        ]
        self._transition(
            snapshot, RunState.EVIDENCE_ANCHORED, "Your selected section is ready for A/B previews"
        )

    async def _create_run_once(
        self, request: CreateRunRequest, key: str | None, fingerprint: str
    ) -> RunSnapshot:
        replay = self.repository.recall_idempotent("create_run", key, fingerprint)
        if replay is not None:
            return replay
        if request.asset_id != DEMO_ASSET_ID:
            raise ValueError("asset is not in the RevisionProof demo allowlist")
        asset, source_path = await asyncio.to_thread(
            require_demo_asset,
            request.asset_id,
            self.settings.runtime_dir,
            self.executor,
        )
        source_key = await asyncio.to_thread(_file_sha256, source_path)
        smart_evidence = self._smart_evidence(
            search_id=request.scene_search_id,
            segment_id=request.scene_segment_id,
            source_key=source_key,
            sample_asset_id=request.asset_id,
        )
        self._record_new_run()
        run_id = new_ulid()
        if request.edit_plan is not None:
            # Planned exports own an immutable reference beside their source, including samples.
            owned_source = self.settings.runtime_dir / "runs" / run_id / "source" / "source.mp4"
            owned_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, owned_source)
            source_path = owned_source
        snapshot = RunSnapshot(
            run_id=run_id,
            asset=asset,
            mode=self.settings.mode,
            state=RunState.INDEXED,
            source_feedback=request.feedback,
            edit_plan=request.edit_plan,
        )
        if smart_evidence is not None:
            snapshot.evidence = [smart_evidence]
        self.repository.create(snapshot, source_path, active=True)
        try:
            await self._cleanup_pending_evictions()
            if snapshot.edit_plan is not None:
                await asyncio.to_thread(review_plan, self, snapshot, snapshot.edit_plan)
                self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
                return snapshot
            if self.settings.mode is ExecutionMode.FIXTURE:
                snapshot.notes = self.fixture_interpreter.interpret_many(request.feedback)
                snapshot.feedback = self._feedback_from_notes(snapshot, "fixture.interpreter")
                self._transition(
                    snapshot,
                    RunState.NOTES_PARSED,
                    "Feedback classified by fixture adapter; unsupported notes held back",
                )
                if snapshot.feedback is None:
                    self.repository.remember_idempotent(
                        "create_run", key, fingerprint, snapshot.run_id
                    )
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
                    self.repository.remember_idempotent(
                        "create_run", key, fingerprint, snapshot.run_id
                    )
                    return snapshot
                try:
                    await self._run_live_interpretation(snapshot, request.feedback)
                except Exception:
                    logger.exception("LIVE interpretation failed for run %s", snapshot.run_id)
                    snapshot.error = "Live interpretation or evidence lookup failed"
                    self._transition(snapshot, RunState.FAILED, snapshot.error)
                self.repository.remember_idempotent("create_run", key, fingerprint, snapshot.run_id)
                return snapshot
            raise ValueError("execution mode cannot create runs")
        finally:
            self.repository.release_active(snapshot.run_id)

    async def retry_live_interpretation(
        self, run_id: str, idempotency_key: str | None = None
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        if (
            self.settings.mode is not ExecutionMode.LIVE
            and self.repository.get(run_id).asset.source_kind != "upload"
        ):
            raise ValueError("interpretation retry is only available in LIVE mode")
        key = self._validate_idempotency_key(idempotency_key)
        lock_key = f"retry:{run_id}"
        async with self._create_idempotency_lock(lock_key):
            fingerprint = self._fingerprint(run_id)
            replay = self.repository.recall_idempotent(lock_key, key, fingerprint)
            if replay is not None:
                return replay
            self.repository.acquire_active(run_id)
            try:
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
                    if snapshot.asset.source_kind == "upload":
                        await self._interpret_uploaded(snapshot, snapshot.source_feedback)
                    else:
                        await self._run_live_interpretation(snapshot, snapshot.source_feedback)
                except Exception:
                    logger.exception("LIVE interpretation retry failed for run %s", snapshot.run_id)
                    snapshot.error = "Live interpretation or evidence lookup failed"
                    self._transition(snapshot, RunState.FAILED, snapshot.error)
                self.repository.remember_idempotent(lock_key, key, fingerprint, run_id)
                return snapshot
            finally:
                self.repository.release_active(run_id)

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

    def generate_previews(
        self,
        run_id: str,
        idempotency_key: str | None = None,
        selected_note_id: str | None = None,
        edit_plan: EditPlan | None = None,
    ) -> RunSnapshot:
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        fingerprint = self._fingerprint(
            f"{run_id}:{selected_note_id or 'default'}:"
            f"{edit_plan.model_dump_json() if edit_plan else ''}"
        )
        with self.repository.locked(run_id):
            replay = self.repository.recall_idempotent(f"{run_id}:previews", key, fingerprint)
            if replay is not None:
                return replay
            with self._exclusive_media_pipeline():
                snapshot = self._generate_previews_locked(run_id, selected_note_id, edit_plan)
                self.repository.remember_idempotent(f"{run_id}:previews", key, fingerprint, run_id)
                return snapshot

    def _generate_previews_locked(
        self, run_id: str, selected_note_id: str | None = None, edit_plan: EditPlan | None = None
    ) -> RunSnapshot:
        snapshot = self.repository.get(run_id)
        if snapshot.state is not RunState.EVIDENCE_ANCHORED:
            raise ValueError("previews require EVIDENCE_ANCHORED state")
        if snapshot.edit_plan is not None:
            plan_previews(self, snapshot, edit_plan)
            return snapshot
        selected_feedback = self._feedback_from_notes(
            snapshot,
            snapshot.feedback.interpreter_source if snapshot.feedback else "fixture.interpreter",
            selected_note_id,
        )
        if selected_feedback is None:
            raise ValueError("select one request marked ready for automatic editing")
        if snapshot.feedback is None or selected_feedback.raw_text != snapshot.feedback.raw_text:
            raise ValueError("the selected request does not match the anchored scene evidence")
        selected_note = next(
            item
            for item in snapshot.notes
            if item.classification is SafetyClassification.AUTO_PREVIEWABLE
            and item.raw_text == selected_feedback.raw_text
            and (selected_note_id is None or item.note_id == selected_note_id)
        )
        snapshot.selected_note_id = selected_note.note_id
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
        self._transition(
            snapshot,
            RunState.PREVIEWS_READY,
            f"Two constrained previews rendered for {snapshot.selected_note_id}",
        )
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
        planned = isinstance(candidate, EditCandidate)
        uploaded = snapshot.asset.source_kind == "upload" or planned
        output_duration = (
            candidate.plan.output_duration if planned else snapshot.asset.duration_seconds
        )
        visual_range = (
            TimeRange(start_seconds=0, end_seconds=output_duration)
            if uploaded
            else TimeRange(start_seconds=24, end_seconds=29)
        )
        audio_range = TimeRange(start_seconds=0, end_seconds=output_duration if uploaded else 30)
        frozen_spec = RevisionSpec.freeze(
            run_id=run_id,
            asset_id=snapshot.asset.asset_id,
            candidate=candidate,
            evidence=snapshot.evidence,
            locked_elements=[
                LockedElement(
                    element_id="original_video" if uploaded else "cta_end_card",
                    kind="VIDEO_CONTENT" if uploaded else "CTA_OVERLAY",
                    time_range=visual_range,
                    description="Follow the approved edit and preserve other sampled video moments."
                    if uploaded
                    else "Bottom-right publish CTA remains visible for the end card.",
                ),
                LockedElement(
                    element_id="master_audio",
                    kind="AUDIO",
                    time_range=audio_range,
                    description=(
                        "Follow the approved audio timing and level changes across the video."
                        if uploaded
                        else "Audio RMS may vary by at most 3 dB; peak stays below -1 dBFS."
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
                    time_range=visual_range,
                    roi=(0, 0, 1280, 720) if uploaded else CTA_ROI,
                    threshold={
                        "minimum_frame_similarity": CTA_SIMILARITY_THRESHOLD,
                        "minimum_passing_ratio": 1.0 if uploaded else CTA_REQUIRED_RATIO,
                    },
                ),
                VerificationManifest(
                    check_id="locked_audio",
                    time_range=audio_range,
                    threshold={
                        "maximum_rms_delta_db": AUDIO_RMS_TOLERANCE_DB,
                        **(
                            {"maximum_peak_delta_db": 0.1}
                            if uploaded
                            else {"maximum_peak_dbfs": AUDIO_PEAK_LIMIT_DBFS}
                        ),
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
        baseline_proof = self._baseline_proof_for(snapshot)

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
        baseline_label = (
            "approved-reference" if snapshot.spec.schema_version in {"3.0", "3.1"} else "v1"
        )
        for label, values in ((baseline_label, baseline_values), (version_label, current_values)):
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
        query = build_version_diff_query(snapshot.run_id, version_label, baseline_label)
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

    def _baseline_proof_for(self, snapshot: RunSnapshot) -> VerificationProof:
        if snapshot.spec is None:
            raise RuntimeError("immutable spec is missing")
        baseline_proof = self._baseline_proofs.get(snapshot.run_id)
        if baseline_proof is None:
            original = self.repository.source_path(snapshot.run_id)
            baseline_proof = self.verifier.verify(
                source=original,
                candidate=approved_reference(original, snapshot.spec)
                if snapshot.spec.schema_version in {"3.0", "3.1"}
                else original,
                spec=snapshot.spec,
                version_label="v1",
            )
            self._baseline_proofs[snapshot.run_id] = baseline_proof
        elif baseline_proof.spec_hash != snapshot.spec.spec_hash:
            raise RuntimeError("cached baseline proof does not match the approved spec")
        return baseline_proof

    def _attach_cta_evidence(self, snapshot: RunSnapshot, destination, version_label: str) -> None:
        if snapshot.proof is None or snapshot.spec is None:
            raise RuntimeError("verification proof or immutable spec is missing")
        manifest = snapshot.spec.manifest_for("locked_cta")
        second = (manifest.time_range.start_seconds + manifest.time_range.end_seconds) / 2
        original_second = (
            snapshot.spec.approved_candidate.plan.source_time(second)
            if isinstance(snapshot.spec.approved_candidate, EditCandidate)
            else second
        )
        evidence_dir = self.settings.runtime_dir / "runs" / snapshot.run_id / "evidence"
        baseline_name = "baseline-cta.png"
        current_name = f"{version_label}-cta.png"
        baseline_path = evidence_dir / baseline_name
        if not baseline_path.exists():
            write_frame_png(
                self.repository.source_path(snapshot.run_id), original_second, baseline_path
            )
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
                self.repository.remember_idempotent(f"{run_id}:version", key, fingerprint, run_id)
                return snapshot

    def render_approved_version(
        self, run_id: str, idempotency_key: str | None = None
    ) -> RunSnapshot:
        """Render the approved candidate into the full source, then verify it."""
        self._assert_mutable_mode()
        key = self._validate_idempotency_key(idempotency_key)
        with self.repository.locked(run_id):
            snapshot = self.repository.get(run_id)
            if snapshot.spec is None:
                raise ValueError("automatic render requires an approved preview")
            fingerprint = self._fingerprint(f"{run_id}:{snapshot.spec.spec_hash}")
            replay = self.repository.recall_idempotent(
                f"{run_id}:automatic-version", key, fingerprint
            )
            if replay is not None:
                return replay
            snapshot = self.repository.get(run_id)
            if snapshot.state not in {
                RunState.HUMAN_APPROVED,
                RunState.BLOCKED,
                RunState.FAILED,
            }:
                raise ValueError(
                    "automatic render requires HUMAN_APPROVED, BLOCKED, or retryable FAILED state"
                )
            assert snapshot.spec is not None
            with self._exclusive_media_pipeline():
                build_dir = self.settings.runtime_dir / "runs" / run_id / "render"
                staging = build_dir / f".automatic-{new_ulid()}.mp4"
                version_label = f"approved-{snapshot.spec.approved_candidate.candidate_id.lower()}"
                try:
                    snapshot.spec = RevisionSpec.model_validate_json(
                        snapshot.spec.model_dump_json()
                    )
                    if snapshot.spec.schema_version in {"3.0", "3.1"}:
                        staging.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(
                            approved_reference(self.repository.source_path(run_id), snapshot.spec),
                            staging,
                        )
                    else:
                        generate_full_revision(
                            source=self.repository.source_path(run_id),
                            destination=staging,
                            candidate=snapshot.spec.approved_candidate,
                            executor=self.executor,
                        )
                    with staging.open("rb") as stream:
                        snapshot = self._upload_and_verify_locked(
                            run_id=run_id,
                            version_label=version_label,
                            stream=stream,
                            size=staging.stat().st_size,
                        )
                    snapshot.generated_version_url = f"/api/runs/{run_id}/generated-video"
                    self.repository.append_event(
                        run_id,
                        snapshot.state,
                        "Approved option applied to the full source video",
                    )
                    self.repository.remember_idempotent(
                        f"{run_id}:automatic-version", key, fingerprint, run_id
                    )
                    return snapshot
                finally:
                    if staging.exists():
                        staging.unlink()
                    if build_dir.exists() and not any(build_dir.iterdir()):
                        build_dir.rmdir()

    def verify_demo_version(
        self,
        *,
        run_id: str,
        version_label: str,
    ) -> RunSnapshot:
        if self.settings.mode is not ExecutionMode.FIXTURE:
            raise ValueError("demo versions are only available in FIXTURE mode")
        snapshot = self.repository.get(run_id)
        if snapshot.asset.source_kind == "upload":
            raise ValueError("Sample revisions cannot be used with an uploaded original")
        if snapshot.spec is None:
            raise ValueError("immutable spec is missing")
        fixture_names = {
            ("A", "v2"): "revisionproof_v2_blocked_A.mp4",
            ("A", "v3"): "revisionproof_v3_ready_A.mp4",
            ("B", "v2"): "revisionproof_v2_blocked.mp4",
            ("B", "v3"): "revisionproof_v3_ready.mp4",
        }
        fixture_name = fixture_names.get(
            (snapshot.spec.approved_candidate.candidate_id, version_label)
        )
        if fixture_name is None:
            raise ValueError("demo version requires candidate A or B and version v2 or v3")
        fixture_path = self.settings.runtime_dir / "demo" / fixture_name
        if not fixture_path.exists():
            raise FileNotFoundError(
                "candidate-specific demo fixture is missing; run scripts/generate_demo_assets.py"
            )
        with fixture_path.open("rb") as stream:
            content_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
            stream.seek(0)
            return self.upload_and_verify(
                run_id=run_id,
                version_label=version_label,
                stream=stream,
                size=fixture_path.stat().st_size,
                idempotency_key=f"{run_id}:demo-version:{version_label}",
                content_sha256=content_sha256,
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
        attempts = sum(event.state is RunState.VERSION_UPLOADED for event in snapshot.events)
        if attempts >= self.settings.max_verification_attempts_per_run:
            raise ValueError("verification attempt limit reached for this run; create a new run")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", version_label):
            raise ValueError(
                "version_label must use 1-64 letters, numbers, dots, dashes, or underscores"
            )
        if size <= 0 or size > self.settings.max_upload_bytes:
            raise ValueError(f"upload must be between 1 byte and {self.settings.max_upload_mb} MB")

        destination = (
            self.settings.runtime_dir / "runs" / run_id / "versions" / f"{version_label}.mp4"
        )
        staging_destination = destination.parent / f".upload-{new_ulid()}.mp4"
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with staging_destination.open("wb") as output:
                shutil.copyfileobj(stream, output)
            info = probe_media(staging_destination, self.executor)
            validate_hackathon_media(info, max_duration_seconds=self.settings.max_duration_seconds)
            expected_duration = (
                snapshot.spec.approved_candidate.plan.output_duration
                if isinstance(snapshot.spec.approved_candidate, EditCandidate)
                else snapshot.asset.duration_seconds
            )
            if abs(info.duration_seconds - expected_duration) > 0.15:
                raise ValueError("Revised video duration must match the approved timeline")
            snapshot.generated_version_url = None
            snapshot.change_map = None
            snapshot.memory_saved = False
            self._transition(snapshot, RunState.VERSION_UPLOADED, f"{version_label} uploaded")
            self._transition(snapshot, RunState.VERIFYING, "Deterministic verification started")
            snapshot.proof = None
            snapshot.proof = self.verifier.verify(
                source=self.repository.source_path(run_id),
                candidate=staging_destination,
                spec=snapshot.spec,
                version_label=version_label,
            )
            self._attach_cta_evidence(snapshot, staging_destination, version_label)
            if self.settings.mode is ExecutionMode.LIVE:
                self._persist_live_verification(snapshot, staging_destination, version_label)
            if self.settings.intelligence_enabled:
                self.repository.append_event(
                    run_id, RunState.VERIFYING, "Building the full-video Change Map"
                )
                snapshot.change_map = self.intelligence.build_map(
                    snapshot,
                    self.repository.source_path(run_id),
                    staging_destination,
                    self.executor,
                )
                self.repository.append_event(
                    run_id,
                    RunState.VERIFYING,
                    "Change Map aggregated through mcp-clickhouse.run_query"
                    if snapshot.change_map.status == "ready"
                    and self.settings.mode is ExecutionMode.LIVE
                    else "Change Map sampled locally"
                    if snapshot.change_map.status == "ready"
                    else "Change Map unavailable; no full-video difference claim was made",
                )
            staging_destination.replace(destination)
            self.repository.set_version_path(run_id, destination)
            try:
                self._prune_verification_artifacts(snapshot, destination)
            except OSError:
                logger.exception(
                    "Verification artifact pruning will retry on a future upload: %s",
                    run_id,
                )
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
            if staging_destination.exists():
                staging_destination.unlink()
            raise
        return snapshot

    def _prune_verification_artifacts(self, snapshot: RunSnapshot, current_version) -> None:
        run_root = (self.settings.runtime_dir / "runs" / snapshot.run_id).resolve()
        versions_root = (run_root / "versions").resolve()
        current_version = current_version.resolve()
        if versions_root.parent != run_root or current_version.parent != versions_root:
            raise RuntimeError("refusing to prune version files outside the run workspace")
        for path in versions_root.iterdir():
            if path != current_version and (path.is_file() or path.is_symlink()):
                path.unlink()

        evidence_root = (run_root / "evidence").resolve()
        if not evidence_root.exists():
            return
        if evidence_root.parent != run_root or snapshot.proof is None:
            raise RuntimeError("refusing to prune evidence outside the run workspace")
        keep_evidence = {
            path.rsplit("/", 1)[-1]
            for check in snapshot.proof.checks
            for path in check.evidence_urls
        }
        for path in evidence_root.iterdir():
            if path.name not in keep_evidence and (path.is_file() or path.is_symlink()):
                path.unlink()

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
                if snapshot.spec is None:
                    raise ValueError("Delivery requires an approved edit.")
                RevisionSpec.model_validate_json(snapshot.spec.model_dump_json())
                if snapshot.spec.schema_version in {"3.0", "3.1"}:
                    from revisionproof.editing.verify import file_hash

                    reference = approved_reference(
                        self.repository.source_path(run_id), snapshot.spec
                    )
                    version = self.repository.version_path(run_id)
                    if file_hash(reference) != file_hash(version):
                        raise ValueError(
                            "The verified export changed. Verify it again before delivery."
                        )
                snapshot.delivery_approved = True
                self.repository.append_event(
                    run_id, RunState.READY, "Human approved the verified version for delivery"
                )
            self.repository.remember_idempotent(
                f"{run_id}:delivery-approval", key, fingerprint, run_id
            )
            return snapshot

    def search_memory(self, run_id: str, engine: SearchEngine) -> EditMemorySearch:
        with self.repository.locked(run_id):
            snapshot = self.repository.get(run_id)
            result = self.intelligence.search(snapshot, engine)
            snapshot.edit_memory = result
            return result

    def save_memory(self, run_id: str, token: str | None = None) -> MemorySaveResult:
        self._assert_mutable_mode()
        with self.repository.locked(run_id):
            snapshot = self.repository.get(run_id)
            result = self.intelligence.save(snapshot, token)
            if result.status == "saved":
                self.repository.append_event(
                    run_id,
                    snapshot.state,
                    "Verified and human-approved edit saved to workspace memory",
                )
            return result
