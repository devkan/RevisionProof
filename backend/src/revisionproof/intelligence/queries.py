from __future__ import annotations

import math
import re

from revisionproof.intelligence.models import SearchEngine


def sql_string(value: str) -> str:
    if not value or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise ValueError("invalid query string")
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def normalize_embedding(values: list[float]) -> list[float]:
    if len(values) != 768 or not all(math.isfinite(float(v)) for v in values):
        raise ValueError("embedding must contain exactly 768 finite coordinates")
    norm = math.sqrt(sum(float(v) ** 2 for v in values))
    if not math.isfinite(norm) or norm < 1e-12:
        raise ValueError("embedding must have a finite non-zero norm")
    return [float(v) / norm for v in values]


def memory_filter(workspace: str, model: str) -> str:
    return f"workspace_id = {sql_string(workspace)} AND embedding_model = {sql_string(model)}"


def build_memory_count_query(workspace: str, model: str, memory_id: str | None = None) -> str:
    extra = ""
    if memory_id is not None:
        if not re.fullmatch(r"[a-f0-9]{64}", memory_id):
            raise ValueError("invalid memory id")
        extra = f" AND memory_id = '{memory_id}'"
    return (
        "SELECT uniqExact(memory_id) AS total FROM approved_edit_memory WHERE "
        + memory_filter(workspace, model)
        + extra
    )


def build_memory_search_query(
    workspace: str,
    model: str,
    embedding: list[float],
    engine: SearchEngine,
    precision: int = 16,
) -> str:
    if engine not in {"exact", "hnsw", "qbit"} or not 12 <= precision <= 32:
        raise ValueError("unsupported memory search engine or precision")
    vector = ",".join(format(value, ".9g") for value in normalize_embedding(embedding))
    if engine == "hnsw":
        return (
            "SELECT memory_id, intent, target_phrase, candidate_id, scale, duration_seconds, "
            "approved_at, spec_hash, distance FROM approved_edit_neighbors("
            f"workspace={sql_string(workspace)}, model={sql_string(model)}, "
            f"reference_vector=[{vector}]) ORDER BY distance ASC LIMIT 15"
        )
    distance = (
        f"L2DistanceTransposed(embedding_qbit, reference_vector, {precision})"
        if engine == "qbit"
        else "L2Distance(embedding, reference_vector)"
    )
    # Direct ascending distance is required for the HNSW optimizer pattern.
    settings = " SETTINGS use_skip_indexes = 0" if engine in {"exact", "qbit"} else ""
    return (
        f"WITH CAST([{vector}], 'Array(Float32)') AS reference_vector "
        "SELECT memory_id, intent, target_phrase, candidate_id, scale, duration_seconds, "
        f"approved_at, spec_hash, {distance} AS distance FROM approved_edit_memory "
        f"WHERE {memory_filter(workspace, model)} ORDER BY distance ASC LIMIT 15{settings}"
    )


def build_change_map_query(workspace: str, run_id: str, analysis_id: str) -> str:
    if not all(re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", value) for value in (run_id, analysis_id)):
        raise ValueError("run and analysis ids must be ULIDs")
    return (
        "SELECT second, sample_count, visual_delta, residual_delta, cta_delta, audio_delta_db, "
        "requested FROM revision_change_map "
        f"WHERE workspace_id = {sql_string(workspace)} AND run_id = '{run_id}' "
        f"AND analysis_id = '{analysis_id}' ORDER BY second LIMIT 600"
    )
