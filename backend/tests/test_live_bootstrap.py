import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import revisionproof.bootstrap as bootstrap_module
from revisionproof.bootstrap import (
    SEED_SEGMENTS,
    _seed_clickhouse,
    bootstrap_live,
    ensure_deployment_metadata,
    split_sql_statements,
    user_provisioning_commands,
    validate_live_bootstrap_settings,
    verify_append_only_layouts,
    verify_view_security,
)
from revisionproof.contracts import ExecutionMode
from revisionproof.settings import Settings


def live_settings(**overrides) -> Settings:
    values = {
        "mode": ExecutionMode.LIVE,
        "google_cloud_project": "revisionproof-agentic-2026-kan",
        "google_cloud_location": "global",
        "gcs_bucket": "revisionproof-agentic-2026-kan-media",
        "clickhouse_host": "example.clickhouse.cloud",
        "clickhouse_writer_password": "writer-secret",
        "clickhouse_mcp_password": "reader-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_live_bootstrap_requires_locked_project_bucket_and_vertex_pair() -> None:
    validate_live_bootstrap_settings(live_settings())

    with pytest.raises(ValueError, match="dedicated revisionproof"):
        validate_live_bootstrap_settings(live_settings(google_cloud_project="other-project"))
    with pytest.raises(ValueError, match="GCS bucket"):
        validate_live_bootstrap_settings(live_settings(gcs_bucket="other-bucket"))
    with pytest.raises(ValueError, match="Vertex location"):
        validate_live_bootstrap_settings(live_settings(google_cloud_location="us-central1"))
    with pytest.raises(ValueError, match="ClickHouse"):
        validate_live_bootstrap_settings(live_settings(clickhouse_host="localhost"))
    with pytest.raises(ValueError, match="ClickHouse"):
        validate_live_bootstrap_settings(live_settings(clickhouse_secure=False))


def test_user_passwords_are_query_parameters_not_sql_text() -> None:
    settings = live_settings()
    commands = user_provisioning_commands(settings)
    rendered_sql = "\n".join(query for query, _ in commands)

    assert "writer-secret" not in rendered_sql
    assert "reader-secret" not in rendered_sql
    assert any(parameters == {"password": "writer-secret"} for _, parameters in commands)
    assert any(parameters == {"password": "reader-secret"} for _, parameters in commands)
    assert "SET DEFAULT ROLE revisionproof_mcp_reader TO revisionproof_mcp_user" in rendered_sql
    assert "readonly = 2, max_execution_time = 5, max_result_rows = 2000" in rendered_sql
    assert "REVOKE ALL ON *.* FROM revisionproof_writer_user" in rendered_sql
    assert "REVOKE ALL ON *.* FROM revisionproof_mcp_user" in rendered_sql


def test_seed_segments_have_stable_ulids_and_exact_revisionproof_anchor() -> None:
    assert len(SEED_SEGMENTS) == 3
    assert len({segment.segment_id for segment in SEED_SEGMENTS}) == 3
    assert all(len(segment.segment_id) == 26 for segment in SEED_SEGMENTS)
    target = SEED_SEGMENTS[1]
    assert (target.start_seconds, target.end_seconds) == (8, 14)
    assert target.embedding_text == "RevisionProof"
    assert "RevisionProof" in target.transcript


def test_clickhouse_sql_files_split_into_nonempty_statements() -> None:
    root = Path(__file__).resolve().parents[2]
    for relative in ("infra/clickhouse/schema.sql", "infra/clickhouse/roles.sql"):
        statements = split_sql_statements((root / relative).read_text(encoding="utf-8"))
        assert statements
        assert all(not statement.endswith(";") for statement in statements)


def test_views_use_a_non_login_durable_definer() -> None:
    root = Path(__file__).resolve().parents[2]
    schema = (root / "infra" / "clickhouse" / "schema.sql").read_text(encoding="utf-8")
    roles = (root / "infra" / "clickhouse" / "roles.sql").read_text(encoding="utf-8")

    assert "CREATE USER IF NOT EXISTS revisionproof_view_definer_user" in schema
    assert "IDENTIFIED WITH sha256_hash" in schema
    assert "ALTER USER revisionproof_view_definer_user" in roles
    assert schema.count("HOST NONE") == 2
    assert schema.count("DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER") == 2
    assert "DEFINER = CURRENT_USER" not in schema


def test_view_security_requires_exact_definer_and_host_none() -> None:
    safe = FakeAdmin(
        [
            [
                (
                    "search_segments",
                    "CREATE VIEW revisionproof.search_segments "
                    "DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS SELECT 1",
                ),
                (
                    "version_feature_diff",
                    "CREATE VIEW revisionproof.version_feature_diff "
                    "DEFINER = revisionproof_view_definer_user SQL SECURITY DEFINER AS SELECT 1",
                ),
            ],
            [("CREATE USER revisionproof_view_definer_user HOST NONE",)],
        ]
    )
    verify_view_security(safe)

    unsafe = FakeAdmin(
        [
            [
                ("search_segments", "CREATE VIEW search_segments AS SELECT 1"),
                ("version_feature_diff", "CREATE VIEW version_feature_diff AS SELECT 1"),
            ]
        ]
    )
    with pytest.raises(RuntimeError, match="unsafe definer"):
        verify_view_security(unsafe)


class FakeAdmin:
    def __init__(self, responses: list[list[tuple]]) -> None:
        self.responses = responses

    def query(self, *_args, **_kwargs):
        return SimpleNamespace(result_rows=self.responses.pop(0))

    def insert(self, *_args, **_kwargs) -> None:
        raise AssertionError("drift validation must fail before inserting")


class MetadataAdmin:
    def __init__(self, responses: list[list[tuple]]) -> None:
        self.responses = responses
        self.inserted: list[tuple] = []

    def query(self, *_args, **_kwargs):
        return SimpleNamespace(result_rows=self.responses.pop(0))

    def insert(self, table, rows, *, column_names) -> None:
        self.inserted.append((table, rows, column_names))


def test_deployment_metadata_is_created_once_and_must_match() -> None:
    settings = live_settings()
    expected = [(settings.google_cloud_project, settings.clickhouse_host)]
    admin = MetadataAdmin([[], expected])

    ensure_deployment_metadata(admin, settings)

    assert len(admin.inserted) == 1
    assert admin.inserted[0][0] == "revisionproof.deployment_metadata"

    drifted = MetadataAdmin([[("revisionproof-other-2026", settings.clickhouse_host)]])
    with pytest.raises(RuntimeError, match="does not exactly match"):
        ensure_deployment_metadata(drifted, settings)


def test_seed_refuses_existing_asset_drift() -> None:
    admin = FakeAdmin([[("RevisionProof — Product Reveal", "gs://wrong/object.mp4", 30.0)]])

    with pytest.raises(RuntimeError, match="drifted ClickHouse demo asset"):
        _seed_clickhouse(
            admin,
            live_settings(),
            object(),
            "gs://revisionproof-agentic-2026-kan-media/assets/proof.mp4",
        )


def test_seed_refuses_existing_segment_drift() -> None:
    gcs_uri = "gs://revisionproof-agentic-2026-kan-media/assets/proof.mp4"
    target = SEED_SEGMENTS[1]
    admin = FakeAdmin(
        [
            [("RevisionProof — Product Reveal", gcs_uri, 30.0)],
            [
                (
                    target.segment_id,
                    target.start_seconds + 1,
                    target.end_seconds,
                    target.transcript,
                    target.visual_summary,
                    768,
                )
            ],
        ]
    )

    with pytest.raises(RuntimeError, match="refusing to reuse drifted segment"):
        _seed_clickhouse(admin, live_settings(), object(), gcs_uri)


def test_seed_reuses_exact_segments_returned_as_fixed_string_bytes() -> None:
    gcs_uri = "gs://revisionproof-agentic-2026-kan-media/assets/proof.mp4"
    rows = [
        (
            segment.segment_id.encode(),
            segment.start_seconds,
            segment.end_seconds,
            segment.transcript,
            segment.visual_summary,
            768,
        )
        for segment in SEED_SEGMENTS
    ]
    admin = FakeAdmin(
        [
            [("RevisionProof — Product Reveal", gcs_uri, 30.0)],
            rows,
        ]
    )

    assert _seed_clickhouse(admin, live_settings(), object(), gcs_uri) == 0


def test_append_only_layout_check_rejects_legacy_engine() -> None:
    admin = FakeAdmin(
        [
            [
                ("revision_specs", "ReplacingMergeTree", "run_id"),
                (
                    "version_features",
                    "MergeTree",
                    "run_id, version_label, feature_name, time_start, extracted_at",
                ),
                (
                    "version_checks",
                    "MergeTree",
                    "run_id, version_label, check_id, checked_at",
                ),
            ]
        ]
    )

    with pytest.raises(RuntimeError, match="append-only schema drift"):
        verify_append_only_layouts(admin)


def test_append_only_layout_check_accepts_clickhouse_cloud_shared_engine() -> None:
    admin = FakeAdmin(
        [
            [
                (
                    "revision_specs",
                    "SharedMergeTree",
                    "run_id, spec_hash, approved_at",
                ),
                (
                    "version_features",
                    "SharedMergeTree",
                    "run_id, version_label, feature_name, time_start, extracted_at",
                ),
                (
                    "version_checks",
                    "SharedMergeTree",
                    "run_id, version_label, check_id, checked_at",
                ),
            ]
        ]
    )

    verify_append_only_layouts(admin)


def test_bootstrap_orchestrates_every_live_gate_and_closes_admin(
    runtime_dir: Path, monkeypatch
) -> None:
    calls: list[str] = []

    class Admin:
        closed = False

        def close(self) -> None:
            self.closed = True

    admin = Admin()
    monkeypatch.setitem(
        sys.modules,
        "clickhouse_connect",
        SimpleNamespace(get_client=lambda **_kwargs: admin),
    )
    monkeypatch.setattr(bootstrap_module, "_apply_sql_files", lambda *_args: calls.append("schema"))
    monkeypatch.setattr(
        bootstrap_module,
        "ensure_deployment_metadata",
        lambda *_args: calls.append("metadata"),
    )
    monkeypatch.setattr(
        bootstrap_module,
        "verify_append_only_layouts",
        lambda *_args: calls.append("layout"),
    )
    monkeypatch.setattr(bootstrap_module, "_provision_users", lambda *_args: calls.append("users"))
    monkeypatch.setattr(
        bootstrap_module,
        "verify_view_security",
        lambda *_args: calls.append("view-security"),
    )
    monkeypatch.setattr(
        bootstrap_module,
        "_upload_source_asset",
        lambda *_args: ("gs://revisionproof-agentic-2026-kan-media/source.mp4", False),
    )
    monkeypatch.setattr(
        bootstrap_module,
        "_seed_clickhouse",
        lambda *_args: calls.append("seed") or 0,
    )

    class Interpreter:
        def __init__(self, _settings) -> None:
            pass

        def embed(self, _text):
            return [0.0] * 768

    class Reader:
        def __init__(self, _settings) -> None:
            pass

        async def run_query(self, _query):
            calls.append("mcp")
            return [{"segment_id": SEED_SEGMENTS[1].segment_id.encode(), "score": 0.93}]

    monkeypatch.setattr(bootstrap_module, "VertexGeminiInterpreter", Interpreter)
    monkeypatch.setattr(bootstrap_module, "McpClickHouseReader", Reader)

    result = bootstrap_live(
        live_settings(runtime_dir=runtime_dir),
        clickhouse_admin_username="default",
        clickhouse_admin_password="admin-secret",
        repo_root=Path(__file__).resolve().parents[2],
    )

    assert result["status"] == "PASS"
    assert calls == [
        "schema",
        "metadata",
        "layout",
        "users",
        "view-security",
        "seed",
        "mcp",
    ]
    assert admin.closed is True


def test_source_asset_upload_closes_storage_client(runtime_dir: Path, monkeypatch) -> None:
    source = runtime_dir / "demo" / "revisionproof_v1.mp4"

    class Blob:
        metadata = None

        def exists(self, *, client) -> bool:
            assert client is storage_client
            return False

        def upload_from_filename(self, *_args, **_kwargs) -> None:
            pass

    class StorageClient:
        closed = False

        def bucket(self, name):
            assert name == "revisionproof-agentic-2026-kan-media"
            return SimpleNamespace(blob=lambda _name: Blob())

        def close(self) -> None:
            self.closed = True

    storage_client = StorageClient()
    monkeypatch.setattr("google.cloud.storage.Client", lambda **_kwargs: storage_client)

    uri, created = bootstrap_module._upload_source_asset(  # noqa: SLF001
        live_settings(runtime_dir=runtime_dir), source
    )

    assert uri.endswith("/assets/01J00000000000000000000000/revisionproof_v1.mp4")
    assert created is True
    assert storage_client.closed is True
