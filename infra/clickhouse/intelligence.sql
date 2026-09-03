-- Additive extension. Requires ClickHouse >= 26.2. No existing tables are replaced.
CREATE TABLE IF NOT EXISTS revisionproof.revision_frame_pairs
(
    workspace_id String,
    run_id FixedString(26),
    version_label String,
    spec_hash FixedString(64),
    analysis_id FixedString(26),
    sample_ms UInt32,
    visual_delta Float64,
    residual_delta Float64,
    cta_delta Float64,
    audio_delta_db Float64,
    requested UInt8,
    measured_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (workspace_id, run_id, analysis_id, sample_ms);

-- Max + uniq are insensitive to duplicate retry blocks. Never sum duplicate samples.
CREATE TABLE IF NOT EXISTS revisionproof.revision_change_windows
(
    workspace_id String,
    run_id FixedString(26),
    version_label String,
    spec_hash FixedString(64),
    analysis_id FixedString(26),
    second UInt16,
    samples AggregateFunction(uniqExact, UInt32),
    visual_delta SimpleAggregateFunction(max, Float64),
    residual_delta SimpleAggregateFunction(max, Float64),
    cta_delta SimpleAggregateFunction(max, Float64),
    audio_delta_db SimpleAggregateFunction(max, Float64),
    requested SimpleAggregateFunction(max, UInt8)
)
ENGINE = AggregatingMergeTree
ORDER BY (workspace_id, run_id, analysis_id, second, version_label, spec_hash);

GRANT SELECT ON revisionproof.revision_frame_pairs TO revisionproof_view_definer;
GRANT INSERT, SELECT ON revisionproof.revision_change_windows TO revisionproof_view_definer;

CREATE MATERIALIZED VIEW IF NOT EXISTS revisionproof.revision_change_windows_mv
TO revisionproof.revision_change_windows
DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS
SELECT workspace_id, run_id, version_label, spec_hash, analysis_id,
    toUInt16(intDiv(sample_ms, 1000)) AS second,
    uniqExactState(sample_ms) AS samples,
    max(visual_delta) AS visual_delta, max(residual_delta) AS residual_delta,
    max(cta_delta) AS cta_delta, max(audio_delta_db) AS audio_delta_db,
    max(requested) AS requested
FROM revisionproof.revision_frame_pairs
GROUP BY workspace_id, run_id, version_label, spec_hash, analysis_id, second;

CREATE VIEW IF NOT EXISTS revisionproof.revision_change_map
DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS
SELECT workspace_id, run_id, version_label, spec_hash, analysis_id, second,
    uniqExactMerge(samples) AS sample_count,
    max(visual_delta) AS visual_delta, max(residual_delta) AS residual_delta,
    max(cta_delta) AS cta_delta, max(audio_delta_db) AS audio_delta_db,
    max(requested) AS requested
FROM revisionproof.revision_change_windows
GROUP BY workspace_id, run_id, version_label, spec_hash, analysis_id, second;

CREATE TABLE IF NOT EXISTS revisionproof.approved_edits
(
    workspace_id String,
    memory_id FixedString(64),
    run_id FixedString(26),
    spec_hash FixedString(64),
    intent String,
    target_phrase String,
    candidate_id String,
    scale Float32,
    duration_seconds Float32,
    embedding_model String,
    embedding Array(Float32),
    embedding_qbit QBit(Float32, 768) MATERIALIZED CAST(embedding, 'QBit(Float32, 768)'),
    proof_json String,
    approved_at DateTime64(3, 'UTC'),
    INDEX approved_edit_hnsw embedding TYPE vector_similarity('hnsw', 'L2Distance', 768) GRANULARITY 100000000,
    CONSTRAINT embedding_dimensions CHECK length(embedding) = 768,
    CONSTRAINT safe_candidate CHECK (candidate_id = 'A' AND abs(scale - 1.05) < 0.0001)
        OR (candidate_id = 'B' AND abs(scale - 1.12) < 0.0001),
    CONSTRAINT safe_duration CHECK duration_seconds >= 4 AND duration_seconds <= 8
)
ENGINE = MergeTree
ORDER BY (workspace_id, embedding_model, memory_id);

GRANT SELECT ON revisionproof.approved_edits TO revisionproof_view_definer;

CREATE VIEW IF NOT EXISTS revisionproof.approved_edit_memory
DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS
SELECT workspace_id, memory_id, run_id, spec_hash, intent, target_phrase,
    candidate_id, scale, duration_seconds, embedding_model, embedding, embedding_qbit, approved_at
FROM revisionproof.approved_edits;

-- 26.2 cannot push a vector search through the ordinary security-definer view.
-- Keep ORDER BY/LIMIT inside this parameterized view to preserve both HNSW and least privilege.
CREATE VIEW IF NOT EXISTS revisionproof.approved_edit_neighbors
DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS
SELECT memory_id, intent, target_phrase, candidate_id, scale, duration_seconds,
    approved_at, spec_hash, L2Distance(embedding, {reference_vector:Array(Float32)}) AS distance
FROM revisionproof.approved_edits
WHERE workspace_id = {workspace:String} AND embedding_model = {model:String}
ORDER BY distance ASC LIMIT 15;

GRANT INSERT ON revisionproof.revision_frame_pairs TO revisionproof_writer;
GRANT INSERT ON revisionproof.approved_edits TO revisionproof_writer;
GRANT SELECT ON revisionproof.revision_change_map TO revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.approved_edit_memory TO revisionproof_mcp_reader;
GRANT SELECT ON revisionproof.approved_edit_neighbors TO revisionproof_mcp_reader;
