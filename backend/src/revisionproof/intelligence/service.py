from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import math
import re
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from time import monotonic

from revisionproof.contracts import ExecutionMode, RunSnapshot, RunState, Verdict
from revisionproof.evidence.live import (
    ClickHouseWriter,
    McpClickHouseReader,
    VertexGeminiInterpreter,
    normalize_clickhouse_fixed_string,
)
from revisionproof.ids import new_ulid
from revisionproof.intelligence.change_map import (
    aggregate_fixture_pairs,
    classify_window,
    measure_frame_pairs,
)
from revisionproof.intelligence.models import (
    ApprovedEditMatch,
    EditMemorySearch,
    MemoryAuthorizationError,
    MemorySaveResult,
    RevisionChangeMap,
    SearchEngine,
)
from revisionproof.intelligence.queries import (
    build_change_map_query,
    build_memory_count_query,
    build_memory_search_query,
    normalize_embedding,
)
from revisionproof.media.executor import MediaExecutor
from revisionproof.settings import Settings

logger = logging.getLogger(__name__)


def _count(rows: list[dict], maximum: int | None = None) -> int:
    if len(rows) != 1:
        raise RuntimeError("Invalid approved-memory count")
    value = rows[0].get("total")
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise RuntimeError("Invalid approved-memory count")
    total = int(value)
    if maximum is not None and total > maximum:
        raise RuntimeError("Invalid approved-memory count")
    return total


class RevisionIntelligence:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._fixture_edits: deque[tuple[ApprovedEditMatch, list[float]]] = deque(maxlen=128)
        self._embeddings: dict[str, list[float]] = {}
        self._search_cache: dict[tuple[str, str], tuple[float, EditMemorySearch]] = {}
        self._cache_lock = RLock()

    def forget_run(self, run_id: str) -> None:
        with self._cache_lock:
            self._embeddings.pop(run_id, None)
            for key in [key for key in self._search_cache if key[0] == run_id]:
                self._search_cache.pop(key, None)

    def _embedding(self, snapshot: RunSnapshot) -> list[float]:
        if snapshot.feedback is None:
            raise ValueError("Review a supported request before searching approved memory")
        if snapshot.run_id not in self._embeddings:
            text = f"{snapshot.feedback.intent}\n{snapshot.feedback.target_phrase}"
            if self.settings.mode is ExecutionMode.FIXTURE:
                vector = [0.0] * 768
                for token in re.findall(r"\w+", text.casefold()):
                    position = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16) % 768
                    vector[position] += 1.0
            else:
                vector = VertexGeminiInterpreter(self.settings).embed(text)
            self._embeddings[snapshot.run_id] = normalize_embedding(vector)
        return self._embeddings[snapshot.run_id]

    def search(self, snapshot: RunSnapshot, engine: SearchEngine) -> EditMemorySearch:
        live = self.settings.mode is ExecutionMode.LIVE
        source = "mcp-clickhouse.run_query" if live else "fixture.approved_memory"
        if not self.settings.intelligence_enabled:
            return EditMemorySearch(
                status="disabled",
                requested_engine=engine,
                actual_engine="unavailable",
                source=source,
                message="Approved memory is disabled.",
            )
        cached = self._search_cache.get((snapshot.run_id, engine))
        if cached and monotonic() - cached[0] < 30:
            return cached[1].model_copy(deep=True)
        started = monotonic()
        try:
            if not live:
                vector = self._embedding(snapshot)
                matches = [
                    item.model_copy(
                        update={
                            "similarity": max(
                                -1.0,
                                min(1.0, sum(a * b for a, b in zip(vector, stored, strict=True))),
                            )
                        }
                    )
                    for item, stored in list(self._fixture_edits)
                ]
                matches.sort(key=lambda item: item.similarity, reverse=True)
                result = EditMemorySearch(
                    status="ready" if matches else "empty",
                    requested_engine=engine,
                    actual_engine="fixture",
                    source=source,
                    collection_size=len(matches),
                    matches=matches[:3],
                    message="Local rehearsal memory; not a live vector query.",
                )
            else:
                result = asyncio.run(self._search_live_bounded(snapshot, engine))
            result.elapsed_ms = round((monotonic() - started) * 1000, 1)
        except Exception:
            logger.exception("Approved memory lookup unavailable for run %s", snapshot.run_id)
            result = EditMemorySearch(
                status="unavailable",
                requested_engine=engine,
                actual_engine="unavailable",
                source=source,
                elapsed_ms=round((monotonic() - started) * 1000, 1),
                message="Past edits could not be loaded. Current editing still works.",
            )
        with self._cache_lock:
            self._search_cache[(snapshot.run_id, engine)] = (
                monotonic(),
                result.model_copy(deep=True),
            )
        return result

    async def _search_live_bounded(
        self, snapshot: RunSnapshot, engine: SearchEngine
    ) -> EditMemorySearch:
        async with asyncio.timeout(100):
            return await self._search_live(snapshot, engine)

    async def _search_live(self, snapshot: RunSnapshot, engine: SearchEngine) -> EditMemorySearch:
        reader = McpClickHouseReader(self.settings)
        workspace, model = self.settings.memory_workspace, self.settings.embedding_model
        counts = await reader.run_query(build_memory_count_query(workspace, model))
        total = _count(counts)
        actual = engine
        message = "Verified, human-approved references. Fresh scene evidence is still required."
        if engine == "hnsw" and total < self.settings.memory_hnsw_min_rows:
            actual = "exact"
            message = (
                "Small collection: exact search is used instead of an unnecessary search graph."
            )
        if not total:
            return EditMemorySearch(
                status="empty",
                requested_engine=engine,
                actual_engine="none",
                source="mcp-clickhouse.run_query",
                collection_size=0,
                message="No approved edits yet. Count queried; no vector search ran.",
            )
        vector = await asyncio.to_thread(self._embedding, snapshot)
        query = build_memory_search_query(
            workspace,
            model,
            vector,
            actual,
            self.settings.memory_qbit_precision,
        )
        index_verified = False
        if total and actual == "hnsw":
            plan = await reader.run_query("EXPLAIN indexes = 1 " + query)
            plan_text = "\n".join(str(value) for row in plan for value in row.values())
            index_verified = "approved_edit_hnsw" in plan_text and "vector_similarity" in plan_text
            if not index_verified:
                actual = "exact"
                message = "ClickHouse did not select HNSW for this filter; exact search was used."
                query = build_memory_search_query(workspace, model, vector, "exact")
        rows = await reader.run_query(query) if total else []
        seen: set[str] = set()
        matches = []
        for row in rows:
            memory_id = normalize_clickhouse_fixed_string(row["memory_id"])
            if memory_id in seen:
                continue
            seen.add(memory_id)
            distance = float(row["distance"])
            if not math.isfinite(distance) or distance < 0:
                raise RuntimeError("invalid memory distance")
            # Unit-normalized vectors: cosine similarity = 1 - squared L2 / 2.
            similarity = max(-1.0, min(1.0, 1 - distance * distance / 2))
            if similarity < 0.55:
                continue
            matches.append(
                ApprovedEditMatch(
                    memory_id=memory_id,
                    intent=str(row["intent"]),
                    target_phrase=str(row["target_phrase"]),
                    candidate_id=str(row["candidate_id"]),
                    scale=round(float(row["scale"]), 2),
                    duration_seconds=float(row["duration_seconds"]),
                    similarity=similarity,
                    approved_at=row["approved_at"],
                    spec_hash=normalize_clickhouse_fixed_string(row["spec_hash"]),
                )
            )
        return EditMemorySearch(
            status="ready" if matches else "empty",
            requested_engine=engine,
            actual_engine=actual,
            source="mcp-clickhouse.run_query",
            collection_size=total,
            index_verified=index_verified,
            precision_bits=self.settings.memory_qbit_precision if actual == "qbit" else None,
            matches=matches[:3],
            message=message,
        )

    def build_map(
        self,
        snapshot: RunSnapshot,
        source: Path,
        candidate: Path,
        executor: MediaExecutor,
    ) -> RevisionChangeMap:
        if snapshot.spec is None or snapshot.proof is None:
            raise ValueError("Change Map requires the frozen spec and current proof")
        live = self.settings.mode is ExecutionMode.LIVE
        analysis_id = new_ulid()
        result = RevisionChangeMap(
            status="unavailable",
            version_label=snapshot.proof.version_label,
            spec_hash=snapshot.spec.spec_hash,
            analysis_id=analysis_id,
            source="mcp-clickhouse.run_query" if live else "fixture.frame_analysis",
            duration_seconds=(
                snapshot.spec.approved_candidate.plan.output_duration
                if snapshot.spec.schema_version in {"3.0", "3.1"}
                else snapshot.asset.duration_seconds
            ),
            message="The change map is unavailable. Use the video players and locked checks below.",
        )
        try:
            pairs = measure_frame_pairs(
                source, candidate, snapshot.spec, result.duration_seconds, executor
            )
            if live:
                at = datetime.now(UTC)
                rows = [
                    [
                        self.settings.memory_workspace,
                        snapshot.run_id,
                        result.version_label,
                        result.spec_hash,
                        analysis_id,
                        *[
                            pair[key]
                            for key in (
                                "sample_ms",
                                "visual_delta",
                                "residual_delta",
                                "cta_delta",
                                "audio_delta_db",
                                "requested",
                            )
                        ],
                        at,
                    ]
                    for pair in pairs
                ]
                ClickHouseWriter(self.settings).insert_frame_pairs(rows)
                stored = asyncio.run(
                    McpClickHouseReader(self.settings).run_query(
                        build_change_map_query(
                            self.settings.memory_workspace, snapshot.run_id, analysis_id
                        )
                    )
                )
                windows = [classify_window(row) for row in stored]
                expected = aggregate_fixture_pairs(pairs)
                if [(w.second, w.sample_count) for w in windows] != [
                    (w.second, w.sample_count) for w in expected
                ]:
                    raise RuntimeError("ClickHouse Change Map sample coverage is incomplete")
            else:
                windows = aggregate_fixture_pairs(pairs)
            if not windows:
                raise RuntimeError("Change Map has no measurements")
            result.windows = windows
            result.status = "ready"
            result.message = (
                "Two samples per second. Review flags are diagnostics, "
                "not additional pass/fail checks."
            )
        except Exception:
            logger.exception("Change Map unavailable for run %s", snapshot.run_id)
        return result

    def save(self, snapshot: RunSnapshot, token: str | None) -> MemorySaveResult:
        if snapshot.spec is not None and snapshot.spec.schema_version in {"3.0", "3.1"}:
            raise ValueError(
                "The reusable edit library currently supports center zoom proofs. "
                "Multi-edit plans cannot be saved to it yet."
            )
        if not self.settings.intelligence_enabled:
            raise ValueError("Approved memory is disabled")
        live = self.settings.mode is ExecutionMode.LIVE
        if live and (
            not self.settings.memory_write_token
            or not token
            or not hmac.compare_digest(token.encode(), self.settings.memory_write_token.encode())
        ):
            raise MemoryAuthorizationError(
                "Saving approved memory requires the private workspace key"
            )
        proof = snapshot.proof
        if (
            snapshot.state is not RunState.READY
            or not snapshot.delivery_approved
            or snapshot.spec is None
            or snapshot.feedback is None
            or proof is None
            or not proof.publish_allowed
            or proof.verdict is not Verdict.PASS
            or proof.spec_hash != snapshot.spec.spec_hash
            or {c.check_id for c in proof.checks}
            != {"approved_patch", "locked_cta", "locked_audio"}
            or len(proof.checks) != 3
            or any(c.verdict is not Verdict.PASS for c in proof.checks)
        ):
            raise ValueError("Save requires all checks PASS and final human delivery approval")
        if (
            snapshot.change_map is None
            or snapshot.change_map.status != "ready"
            or snapshot.change_map.spec_hash != proof.spec_hash
            or snapshot.change_map.version_label != proof.version_label
            or not snapshot.change_map.windows
            or any(w.status == "review" for w in snapshot.change_map.windows)
        ):
            raise ValueError("Resolve Change Map review flags before saving a reusable edit")
        identity = (
            f"{self.settings.memory_workspace}:{snapshot.run_id}:"
            f"{proof.spec_hash}:{proof.generated_at.isoformat()}"
        )
        memory_id = hashlib.sha256(identity.encode()).hexdigest()
        origin = "clickhouse.approved_memory" if live else "fixture.approved_memory"
        if snapshot.memory_saved:
            return MemorySaveResult(memory_id=memory_id, status="already_saved", source=origin)
        candidate = snapshot.spec.approved_candidate
        match = ApprovedEditMatch(
            memory_id=memory_id,
            intent=snapshot.feedback.intent,
            target_phrase=snapshot.feedback.target_phrase,
            candidate_id=candidate.candidate_id,
            scale=candidate.scale,
            duration_seconds=candidate.time_range.end_seconds - candidate.time_range.start_seconds,
            similarity=1,
            approved_at=datetime.now(UTC),
            spec_hash=proof.spec_hash,
        )
        vector = self._embedding(snapshot)
        if live:
            query = build_memory_count_query(
                self.settings.memory_workspace, self.settings.embedding_model, memory_id
            )
            reader = McpClickHouseReader(self.settings)
            existing = asyncio.run(reader.run_query(query))
            if _count(existing, maximum=1) == 0:
                sanitized = proof.model_copy(deep=True)
                for check in sanitized.checks:
                    check.evidence_urls = []
                ClickHouseWriter(self.settings).insert_approved_edit(
                    [
                        self.settings.memory_workspace,
                        memory_id,
                        snapshot.run_id,
                        proof.spec_hash,
                        match.intent,
                        match.target_phrase,
                        match.candidate_id,
                        match.scale,
                        match.duration_seconds,
                        self.settings.embedding_model,
                        vector,
                        sanitized.model_dump_json(),
                        match.approved_at,
                    ]
                )
                confirmed = asyncio.run(reader.run_query(query))
                if _count(confirmed, maximum=1) != 1:
                    raise RuntimeError("Approved edit persistence could not be confirmed")
        elif not any(item.memory_id == memory_id for item, _ in self._fixture_edits):
            self._fixture_edits.append((match, vector))
        snapshot.memory_saved = True
        with self._cache_lock:
            self._search_cache.clear()
        return MemorySaveResult(memory_id=memory_id, status="saved", source=origin)
