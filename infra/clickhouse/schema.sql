CREATE DATABASE IF NOT EXISTS revisionproof;

CREATE TABLE IF NOT EXISTS revisionproof.assets
(
    asset_id FixedString(26),
    title String,
    gcs_uri String,
    duration_seconds Float32,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (asset_id, created_at);

CREATE TABLE IF NOT EXISTS revisionproof.segments
(
    segment_id FixedString(26),
    asset_id FixedString(26),
    start_seconds Float32,
    end_seconds Float32,
    transcript String,
    visual_summary String,
    embedding Array(Float32),
    created_at DateTime64(3, 'UTC'),
    CONSTRAINT embedding_768 CHECK length(embedding) = 768
)
ENGINE = MergeTree
ORDER BY (asset_id, start_seconds, segment_id);

CREATE TABLE IF NOT EXISTS revisionproof.revision_notes
(
    run_id FixedString(26),
    raw_text String,
    interpreted_json String,
    interpreter_source LowCardinality(String),
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (run_id, created_at);

CREATE TABLE IF NOT EXISTS revisionproof.patch_candidates
(
    run_id FixedString(26),
    candidate_id LowCardinality(String),
    patch_type LowCardinality(String),
    scale Float32,
    start_seconds Float32,
    end_seconds Float32,
    preview_gcs_uri String,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (run_id, candidate_id, created_at);

CREATE TABLE IF NOT EXISTS revisionproof.revision_specs
(
    run_id FixedString(26),
    spec_hash FixedString(64),
    canonical_json String,
    approved_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(approved_at)
ORDER BY run_id;

CREATE TABLE IF NOT EXISTS revisionproof.version_features
(
    run_id FixedString(26),
    version_label String,
    feature_name LowCardinality(String),
    feature_value Float64,
    time_start Float32,
    time_end Float32,
    extracted_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(extracted_at)
ORDER BY (run_id, version_label, feature_name, time_start);

CREATE TABLE IF NOT EXISTS revisionproof.version_checks
(
    run_id FixedString(26),
    version_label String,
    check_id LowCardinality(String),
    verdict LowCardinality(String),
    failure_code Nullable(String),
    measured_json String,
    threshold_json String,
    checked_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(checked_at)
ORDER BY (run_id, version_label, check_id);

CREATE TABLE IF NOT EXISTS revisionproof.run_events
(
    run_id FixedString(26),
    sequence UInt32,
    state LowCardinality(String),
    message String,
    occurred_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (run_id, sequence);

CREATE VIEW IF NOT EXISTS revisionproof.search_segments
DEFINER = CURRENT_USER SQL SECURITY DEFINER AS
SELECT segment_id, asset_id, start_seconds, end_seconds, transcript, visual_summary, embedding
FROM revisionproof.segments;

CREATE VIEW IF NOT EXISTS revisionproof.version_feature_diff
DEFINER = CURRENT_USER SQL SECURITY DEFINER AS
SELECT
    current.run_id,
    current.version_label AS current_version,
    baseline.version_label AS baseline_version,
    current.feature_name,
    baseline.feature_value AS baseline_value,
    current.feature_value AS current_value,
    abs(current.feature_value - baseline.feature_value) AS absolute_delta
FROM
(
    SELECT
        run_id,
        version_label,
        feature_name,
        time_start,
        time_end,
        argMax(feature_value, extracted_at) AS feature_value
    FROM revisionproof.version_features
    GROUP BY run_id, version_label, feature_name, time_start, time_end
) AS current
INNER JOIN
(
    SELECT
        run_id,
        version_label,
        feature_name,
        time_start,
        time_end,
        argMax(feature_value, extracted_at) AS feature_value
    FROM revisionproof.version_features
    GROUP BY run_id, version_label, feature_name, time_start, time_end
) AS baseline
    ON current.run_id = baseline.run_id
    AND current.feature_name = baseline.feature_name
    AND current.time_start = baseline.time_start
    AND current.time_end = baseline.time_end;
