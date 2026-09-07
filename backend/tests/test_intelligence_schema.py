import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from revisionproof.bootstrap import VIEW_DEFINER_USER, split_sql_statements
from revisionproof.intelligence.schema import (
    TABLES,
    migrate_intelligence,
    require_supported_version,
    verify_intelligence_schema,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/migrate_clickhouse_intelligence.py"


class FakeAdmin:
    def __init__(self, responses):
        self.responses = list(responses)
        self.commands: list[str] = []

    def query(self, *_args, **_kwargs):
        return SimpleNamespace(result_rows=self.responses.pop(0))

    def command(self, statement):
        self.commands.append(statement)


def schema_rows(shared=False):
    rows = []
    for name, engine in TABLES.items():
        ddl = f"CREATE TABLE {name}"
        definer = ""
        if engine in {"View", "MaterializedView"}:
            ddl += f" DEFINER = {VIEW_DEFINER_USER} SQL SECURITY DEFINER AS SELECT 1"
            definer = VIEW_DEFINER_USER
        if name == "approved_edits":
            ddl += " (embedding_qbit QBit(Float32, 768), INDEX approved_edit_hnsw embedding)"
        if name == "approved_edit_recipes":
            ddl += " (embedding_qbit QBit(Float32, 768), INDEX approved_recipe_hnsw embedding)"
        if name == "smart_scene_segments":
            ddl += " (INDEX smart_scene_hnsw embedding) TTL expires_at DELETE"
        actual_engine = f"Shared{engine}" if shared and engine.endswith("MergeTree") else engine
        rows.append((name, actual_engine, definer, ddl))
    return rows


@pytest.mark.parametrize("version", ["26.2", "26.2.19.43", "26.8.1.12", "27.1.0.1"])
def test_supported_version_accepts_qbit_production_release_and_newer(version) -> None:
    require_supported_version(version)


@pytest.mark.parametrize("version", ["25.8.3.1", "26.1.1", "25.12.1.2", "", "latest"])
def test_supported_version_rejects_older_or_unknown_server(version) -> None:
    with pytest.raises(ValueError, match="26.2"):
        require_supported_version(version)


@pytest.mark.parametrize("shared", [False, True])
def test_schema_verifier_accepts_oss_and_cloud_shared_engines(shared) -> None:
    verify_intelligence_schema(FakeAdmin([schema_rows(shared)]))


@pytest.mark.parametrize(
    "mutation", ["missing", "engine", "definer", "qbit", "hnsw", "recipe", "scene_ttl"]
)
def test_schema_verifier_rejects_incomplete_or_unsafe_layout(mutation) -> None:
    rows = schema_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "engine":
        rows[0] = (rows[0][0], "ReplacingMergeTree", *rows[0][2:])
    elif mutation == "definer":
        index = next(i for i, row in enumerate(rows) if row[1] == "View")
        row = rows[index]
        rows[index] = (*row[:2], "default", row[3])
    elif mutation in {"qbit", "hnsw"}:
        index = next(i for i, row in enumerate(rows) if row[0] == "approved_edits")
        row = rows[index]
        marker = "QBit(Float32, 768)" if mutation == "qbit" else "approved_edit_hnsw"
        rows[index] = (*row[:3], row[3].replace(marker, "unexpected"))
    elif mutation == "recipe":
        index = next(i for i, row in enumerate(rows) if row[0] == "approved_edit_recipes")
        row = rows[index]
        rows[index] = (*row[:3], row[3].replace("approved_recipe_hnsw", "unexpected"))
    else:
        index = next(i for i, row in enumerate(rows) if row[0] == "smart_scene_segments")
        row = rows[index]
        rows[index] = (*row[:3], row[3].replace("TTL expires_at", "missing_ttl"))
    with pytest.raises(RuntimeError):
        verify_intelligence_schema(FakeAdmin([rows]))


def test_migration_is_additive_and_preserves_unrelated_tables() -> None:
    admin = FakeAdmin(
        [[("26.2.19.43",)], [("unrelated_existing_data", "MergeTree")], schema_rows()]
    )
    result = migrate_intelligence(admin, ROOT)
    assert result["created"] == sorted(TABLES)
    assert result["preserved"] == ["unrelated_existing_data"]
    assert admin.commands
    assert all("unrelated_existing_data" not in statement for statement in admin.commands)
    assert not any(
        statement.lstrip().startswith(("DROP ", "TRUNCATE ", "DELETE "))
        for statement in admin.commands
    )


def test_migration_rerun_reports_no_new_objects() -> None:
    before = [(name, engine) for name, engine in TABLES.items()]
    admin = FakeAdmin([[("26.2.19.43",)], before, schema_rows()])
    result = migrate_intelligence(admin, ROOT)
    assert result["created"] == []
    assert result["preserved"] == sorted(TABLES)


def test_migration_rejects_old_server_before_any_sql_mutation() -> None:
    admin = FakeAdmin([[("25.6.9.1",)]])
    with pytest.raises(ValueError, match="26.2"):
        migrate_intelligence(admin, ROOT)
    assert admin.commands == []


def test_migration_rejects_drifted_existing_table_before_any_mutation() -> None:
    admin = FakeAdmin([[("26.2.19.43",)], [("approved_edits", "ReplacingMergeTree")]])
    with pytest.raises(RuntimeError, match="drifted table"):
        migrate_intelligence(admin, ROOT)
    assert admin.commands == []


def test_extension_sql_keeps_raw_data_private_and_uses_incremental_aggregation() -> None:
    sql = (ROOT / "infra/clickhouse/intelligence.sql").read_text(encoding="utf-8")
    statements = split_sql_statements(sql)
    grants = [statement for statement in statements if statement.startswith("GRANT")]
    mcp_grants = [grant for grant in grants if "TO revisionproof_mcp_reader" in grant]
    assert mcp_grants
    assert all("GRANT SELECT ON revisionproof." in grant for grant in mcp_grants)
    assert all(
        "approved_edits TO" not in grant
        and "approved_edit_recipes TO" not in grant
        and "revision_frame_pairs TO" not in grant
        for grant in mcp_grants
    )
    assert "AggregateFunction(uniqExact, UInt32)" in sql
    assert "uniqExactState(sample_ms)" in sql
    assert "uniqExactMerge(samples)" in sql
    assert "SQL SECURITY DEFINER" in sql
    assert "{workspace:String}" in sql and "{model:String}" in sql
    assert "ORDER BY distance ASC LIMIT 15" in sql


@pytest.fixture
def migration_script():
    spec = importlib.util.spec_from_file_location("migrate_intelligence_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("host,port", [("localhost", 8123), ("127.0.0.1", 18123), ("::1", 8123)])
def test_local_migration_is_explicit_loopback_only(migration_script, host, port) -> None:
    migration_script.validate_target(host, port, host, "local", True)


@pytest.mark.parametrize(
    "host,port,confirmed,project,local",
    [
        ("localhost", 8123, "different", "local", True),
        ("10.1.1.1", 8123, "10.1.1.1", "local", True),
        ("localhost", 9000, "localhost", "local", True),
        ("localhost", 8123, "localhost", "other-project", True),
        (
            "service.clickhouse.cloud",
            8123,
            "service.clickhouse.cloud",
            "revisionproof-test123",
            False,
        ),
        ("service.clickhouse.cloud", 8443, "service.clickhouse.cloud", "other-hackathon", False),
        ("evil.example.com", 8443, "evil.example.com", "revisionproof-test123", False),
        (
            "service.clickhouse.cloud.evil.com",
            8443,
            "service.clickhouse.cloud.evil.com",
            "revisionproof-test123",
            False,
        ),
    ],
)
def test_migration_rejects_unconfirmed_or_other_project_targets(
    migration_script, host, port, confirmed, project, local
) -> None:
    with pytest.raises(ValueError):
        migration_script.validate_target(host, port, confirmed, project, local)


def test_cloud_migration_requires_matching_deployment_sentinel(migration_script) -> None:
    host = "service.clickhouse.cloud"
    project = "revisionproof-agentic-2026-kan"
    migration_script.validate_target(host, 8443, host, project, False)
    migration_script.verify_target(FakeAdmin([[(project, host)]]), project, host)
    for rows in (
        [],
        [("other-project", host)],
        [(project, "other.clickhouse.cloud")],
        [(project, host)] * 2,
    ):
        with pytest.raises(RuntimeError, match="sentinel mismatch"):
            migration_script.verify_target(FakeAdmin([rows]), project, host)
