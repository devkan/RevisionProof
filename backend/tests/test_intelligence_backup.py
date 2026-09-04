from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = "revisionproof-backup-test"


@pytest.fixture
def backup_script(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "backup_intelligence_test", ROOT / "scripts/backup_clickhouse_intelligence.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approved_row(workspace=WORKSPACE) -> dict:
    return {
        "workspace_id": workspace,
        "memory_id": "a" * 64,
        "run_id": "01J00000000000000000000000",
        "spec_hash": "b" * 64,
        "intent": "Apply a six-second center punch-in",
        "target_phrase": "RevisionProof",
        "candidate_id": "B",
        "scale": 1.12,
        "duration_seconds": 6,
        "embedding_model": "text-embedding-005",
        "embedding": [1.0] + [0.0] * 767,
        "proof_json": '{"verdict":"PASS","publish_allowed":true}',
        "approved_at": "2026-09-03 00:00:00.000",
    }


def frame_row(workspace=WORKSPACE) -> dict:
    return {
        "workspace_id": workspace,
        "run_id": "01J00000000000000000000000",
        "version_label": "v3",
        "spec_hash": "b" * 64,
        "analysis_id": "01J00000000000000000000001",
        "sample_ms": 250,
        "visual_delta": 0.01,
        "residual_delta": 0.001,
        "cta_delta": 0,
        "audio_delta_db": 0.1,
        "requested": 0,
        "measured_at": "2026-09-03 00:00:00.000",
    }


def recipe_row(workspace=WORKSPACE) -> dict:
    row = approved_row(workspace)
    row.pop("scale")
    row["duration_seconds"] = 12
    row["operations_json"] = '{"source_duration":12,"operations":[]}'
    return row


def encoded_rows(rows) -> bytes:
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


class ChunkedStream(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.read_sizes: list[int] = []

    def read(self, size=-1):
        assert 0 < size <= 1024 * 1024, "export must stream bounded blocks"
        self.read_sizes.append(size)
        return super().read(min(size, 113))


class FakeClient:
    def __init__(self, *, exported=None, counts=None):
        self.exported = exported or {
            "approved_edits": encoded_rows([approved_row()]),
            "approved_edit_recipes": encoded_rows([recipe_row()]),
            "revision_frame_pairs": encoded_rows([frame_row()]),
        }
        self.counts = {
            "approved_edits": 0,
            "approved_edit_recipes": 0,
            "revision_frame_pairs": 0,
            "revision_change_windows": 0,
            **(counts or {}),
        }
        self.streams: list[ChunkedStream] = []
        self.selects: list[tuple[str, dict, str]] = []
        self.queries: list[tuple[str, dict]] = []
        self.inserts: list[tuple[str, list[str], bytes, str]] = []
        self.events: list[tuple[str, str]] = []

    def raw_stream(self, query, *, parameters, fmt):
        table = next(table for table in self.exported if f"revisionproof.{table} " in query)
        self.selects.append((query, parameters, fmt))
        stream = ChunkedStream(self.exported[table])
        self.streams.append(stream)
        return stream

    def query(self, query, *, parameters):
        table = next(table for table in self.counts if f"revisionproof.{table} " in query)
        self.queries.append((query, parameters))
        self.events.append(("query", table))
        return SimpleNamespace(result_rows=[(self.counts[table],)])

    def raw_insert(self, table, *, column_names, insert_block, fmt):
        assert isinstance(insert_block, io.BufferedReader), "restore must pass a file stream"
        assert not insert_block.closed
        chunks = []
        while chunk := insert_block.read(97):
            chunks.append(chunk)
        data = b"".join(chunks)
        self.inserts.append((table, column_names, data, fmt))
        short_name = table.removeprefix("revisionproof.")
        self.events.append(("insert", short_name))
        self.counts[short_name] = len(data.splitlines())


@pytest.fixture
def exported_backup(backup_script, tmp_path):
    directory = tmp_path / "export"
    manifest = backup_script.export_workspace(FakeClient(), directory, WORKSPACE)
    return directory, manifest


def rewrite_manifest(directory, manifest):
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_export_streams_only_own_workspace_and_commits_checksummed_manifest(
    backup_script, tmp_path
) -> None:
    directory = tmp_path / "new-export"
    client = FakeClient()
    result = backup_script.export_workspace(client, directory, WORKSPACE)
    stored = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert stored == result
    assert result["format_version"] == backup_script.FORMAT_VERSION
    assert result["workspace"] == WORKSPACE
    assert result["created_at"]
    assert set(result["tables"]) == set(backup_script.TABLE_COLUMNS)
    assert client.inserts == []
    assert len(client.selects) == 3
    for query, parameters, fmt in client.selects:
        assert "WHERE workspace_id = {workspace:String}" in query
        assert parameters == {"workspace": WORKSPACE}
        assert fmt == "JSONEachRow"
        assert "embedding_qbit" not in query
        assert "revision_change_windows" not in query
    for table, raw in client.exported.items():
        assert (directory / f"{table}.jsonl").read_bytes() == raw
        assert result["tables"][table] == {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "rows": 1,
        }
    assert all(stream.closed and len(stream.read_sizes) > 1 for stream in client.streams)


def test_export_never_overwrites_existing_directory_or_partial_export(
    backup_script, exported_backup
) -> None:
    directory, _manifest = exported_backup
    original = (directory / "manifest.json").read_bytes()
    client = FakeClient()
    with pytest.raises(FileExistsError):
        backup_script.export_workspace(client, directory, WORKSPACE)
    assert (directory / "manifest.json").read_bytes() == original
    assert client.selects == []


def test_failed_export_has_no_complete_manifest_and_cannot_be_restored(
    backup_script, tmp_path
) -> None:
    directory = tmp_path / "interrupted-export"
    client = FakeClient(
        exported={
            "approved_edits": encoded_rows([approved_row()]),
            "approved_edit_recipes": encoded_rows([recipe_row()]),
            "revision_frame_pairs": encoded_rows([frame_row("other-project")]),
        }
    )
    with pytest.raises(ValueError, match="different workspace"):
        backup_script.export_workspace(client, directory, WORKSPACE)
    assert (directory / "approved_edits.jsonl").exists()
    assert not (directory / "manifest.json").exists()
    target = FakeClient()
    with pytest.raises(FileNotFoundError):
        backup_script.restore_workspace(target, directory, WORKSPACE, True)
    assert target.queries == [] and target.inserts == []


def test_restore_dry_run_validates_all_destinations_without_writing(
    backup_script, exported_backup
) -> None:
    directory, manifest = exported_backup
    client = FakeClient()
    result = backup_script.restore_workspace(client, directory, WORKSPACE, False)
    assert result == {"applied": False, "workspace": WORKSPACE, "tables": manifest["tables"]}
    assert client.inserts == []
    assert len(client.queries) == 4
    assert all(parameters == {"workspace": WORKSPACE} for _, parameters in client.queries)


def test_restore_accepts_previous_format_without_recipe_rows(
    backup_script, exported_backup
) -> None:
    directory, manifest = exported_backup
    manifest["format_version"] = 1
    manifest["tables"].pop("approved_edit_recipes")
    (directory / "approved_edit_recipes.jsonl").unlink()
    rewrite_manifest(directory, manifest)
    client = FakeClient()
    result = backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert result["applied"] is True
    assert [table for table, *_ in client.inserts] == [
        "revisionproof.approved_edits",
        "revisionproof.revision_frame_pairs",
    ]


def test_restore_applies_streams_only_after_all_empty_checks_and_confirms_counts(
    backup_script, exported_backup
) -> None:
    directory, manifest = exported_backup
    client = FakeClient()
    result = backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert result["applied"] is True
    assert client.events[:4] == [
        ("query", "approved_edits"),
        ("query", "approved_edit_recipes"),
        ("query", "revision_frame_pairs"),
        ("query", "revision_change_windows"),
    ]
    assert len(client.inserts) == 3
    assert len(client.queries) == 7
    for table, columns, data, fmt in client.inserts:
        name = table.removeprefix("revisionproof.")
        assert columns == backup_script.TABLE_COLUMNS[name]
        assert data == (directory / f"{name}.jsonl").read_bytes()
        assert len(data.splitlines()) == manifest["tables"][name]["rows"]
        assert fmt == "JSONEachRow"


@pytest.mark.parametrize(
    "table",
    ["approved_edits", "approved_edit_recipes", "revision_frame_pairs", "revision_change_windows"],
)
@pytest.mark.parametrize("apply", [False, True])
def test_any_nonempty_destination_refuses_before_any_insert(
    backup_script, exported_backup, table, apply
) -> None:
    directory, _manifest = exported_backup
    client = FakeClient(counts={table: 1})
    with pytest.raises(ValueError, match="non-empty workspace table"):
        backup_script.restore_workspace(client, directory, WORKSPACE, apply)
    assert client.inserts == []


@pytest.mark.parametrize("field,value", [("workspace", "other-project"), ("format_version", 3)])
def test_manifest_workspace_and_version_tamper_fails_before_destination_checks(
    backup_script, exported_backup, field, value
) -> None:
    directory, manifest = exported_backup
    manifest[field] = value
    rewrite_manifest(directory, manifest)
    client = FakeClient()
    with pytest.raises(ValueError, match="manifest"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


@pytest.mark.parametrize("mutation", ["missing-table", "extra-table", "path-table"])
def test_manifest_cannot_select_an_unexpected_table_or_path(
    backup_script, exported_backup, mutation
) -> None:
    directory, manifest = exported_backup
    if mutation == "missing-table":
        manifest["tables"].pop("approved_edits")
    elif mutation == "extra-table":
        manifest["tables"]["unrelated_project_data"] = {"sha256": "a" * 64, "rows": 1}
    else:
        manifest["tables"]["../approved_edits"] = manifest["tables"].pop("approved_edits")
    rewrite_manifest(directory, manifest)
    client = FakeClient()
    with pytest.raises(ValueError, match="manifest"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


@pytest.mark.parametrize("mutation", ["checksum", "rows", "extra-metadata"])
def test_manifest_checksums_and_exact_row_counts_are_verified(
    backup_script, exported_backup, mutation
) -> None:
    directory, manifest = exported_backup
    info = manifest["tables"]["revision_frame_pairs"]
    if mutation == "checksum":
        info["sha256"] = "0" * 64
    elif mutation == "rows":
        info["rows"] = 900
    else:
        info["path"] = "../not-allowed.jsonl"
    rewrite_manifest(directory, manifest)
    client = FakeClient()
    with pytest.raises(ValueError, match="checksum or row count mismatch"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


@pytest.mark.parametrize(
    "table", ["approved_edits", "approved_edit_recipes", "revision_frame_pairs"]
)
def test_modified_file_content_is_rejected_even_when_json_is_valid(
    backup_script, exported_backup, table
) -> None:
    directory, _manifest = exported_backup
    path = directory / f"{table}.jsonl"
    row = json.loads(path.read_text(encoding="utf-8"))
    row["run_id"] = "01J00000000000000000000099"
    path.write_bytes(encoded_rows([row]))
    client = FakeClient()
    with pytest.raises(ValueError, match="checksum"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


@pytest.mark.parametrize("mutation", ["workspace", "extra-column", "missing-column"])
def test_rows_cannot_escape_workspace_or_schema_even_with_recomputed_checksum(
    backup_script, exported_backup, mutation
) -> None:
    directory, manifest = exported_backup
    row = frame_row()
    if mutation == "workspace":
        row["workspace_id"] = "other-project"
    elif mutation == "extra-column":
        row["secret"] = "unexpected"
    else:
        row.pop("spec_hash")
    data = encoded_rows([row])
    (directory / "revision_frame_pairs.jsonl").write_bytes(data)
    manifest["tables"]["revision_frame_pairs"] = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": 1,
    }
    rewrite_manifest(directory, manifest)
    client = FakeClient()
    with pytest.raises(ValueError, match="unexpected columns|different workspace"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


def test_symlinked_data_file_is_rejected_before_read_or_destination_query(
    backup_script, exported_backup, monkeypatch
) -> None:
    directory, _manifest = exported_backup
    target = directory / "approved_edits.jsonl"
    actual = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == target or actual(path))
    inspect = Mock(side_effect=AssertionError("linked files must not be opened"))
    monkeypatch.setattr(backup_script, "inspect_file", inspect)
    client = FakeClient()
    with pytest.raises(ValueError, match="inside the export directory"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    inspect.assert_not_called()
    assert client.queries == [] and client.inserts == []


def test_resolved_data_path_outside_export_is_rejected(
    backup_script, exported_backup, monkeypatch, tmp_path
) -> None:
    directory, _manifest = exported_backup
    target = directory / "approved_edits.jsonl"
    actual = Path.resolve
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda path, *args, **kwargs: (
            tmp_path / "outside.jsonl" if path == target else actual(path, *args, **kwargs)
        ),
    )
    client = FakeClient()
    with pytest.raises(ValueError, match="inside the export directory"):
        backup_script.restore_workspace(client, directory, WORKSPACE, True)
    assert client.queries == [] and client.inserts == []


def test_bounded_import_size_rejects_oversized_rows(backup_script, tmp_path) -> None:
    path = tmp_path / "oversized.jsonl"
    row = approved_row()
    row["intent"] = "x" * backup_script.MAX_LINE_BYTES
    path.write_bytes(encoded_rows([row]))
    with pytest.raises(ValueError, match="bounded import size"):
        backup_script.inspect_file(path, backup_script.TABLE_COLUMNS["approved_edits"], WORKSPACE)


def test_empty_export_roundtrip_does_not_insert_any_empty_blocks(backup_script, tmp_path) -> None:
    directory = tmp_path / "empty-export"
    source = FakeClient(
        exported={
            "approved_edits": b"",
            "approved_edit_recipes": b"",
            "revision_frame_pairs": b"",
        }
    )
    manifest = backup_script.export_workspace(source, directory, WORKSPACE)
    assert all(info["rows"] == 0 for info in manifest["tables"].values())
    target = FakeClient()
    result = backup_script.restore_workspace(target, directory, WORKSPACE, True)
    assert result["applied"]
    assert target.inserts == []


def test_restore_count_mismatch_stops_without_second_insert(backup_script, exported_backup) -> None:
    directory, _manifest = exported_backup

    class BrokenTarget(FakeClient):
        def raw_insert(self, *args, **kwargs):
            super().raw_insert(*args, **kwargs)
            self.counts["approved_edits"] = 0

    target = BrokenTarget()
    with pytest.raises(RuntimeError, match="Stop; do not blindly retry"):
        backup_script.restore_workspace(target, directory, WORKSPACE, True)
    assert len(target.inserts) == 1
    assert target.inserts[0][0] == "revisionproof.approved_edits"


def test_cli_restore_defaults_to_dry_run_and_closes_client(
    backup_script, exported_backup, monkeypatch, capsys
) -> None:
    directory, _manifest = exported_backup
    client = Mock()
    client.query.return_value = SimpleNamespace(result_rows=[("26.2.19.43",)])
    connector = SimpleNamespace(get_client=Mock(return_value=client))
    monkeypatch.setitem(sys.modules, "clickhouse_connect", connector)
    monkeypatch.setenv("REVISIONPROOF_CLICKHOUSE_ADMIN_PASSWORD", "test-only-password")
    monkeypatch.setattr(backup_script, "verify_intelligence_schema", Mock())
    restore = Mock(return_value={"applied": False})
    monkeypatch.setattr(backup_script, "restore_workspace", restore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backup_clickhouse_intelligence.py",
            "restore",
            "--directory",
            str(directory),
            "--workspace",
            WORKSPACE,
            "--host",
            "127.0.0.1",
            "--port",
            "18123",
            "--confirm-host",
            "127.0.0.1",
            "--confirm-project",
            "local",
            "--insecure-local",
        ],
    )
    backup_script.main()
    restore.assert_called_once_with(client, directory, WORKSPACE, False)
    client.close.assert_called_once()
    assert "test-only-password" not in capsys.readouterr().out


@pytest.mark.parametrize("workspace", ["../other", "ab", "a' OR 1=1 --", "x" * 65])
def test_cli_rejects_invalid_workspace_before_connecting(
    backup_script, monkeypatch, tmp_path, workspace
) -> None:
    connector = SimpleNamespace(get_client=Mock())
    monkeypatch.setitem(sys.modules, "clickhouse_connect", connector)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backup_clickhouse_intelligence.py",
            "restore",
            "--directory",
            str(tmp_path),
            "--workspace",
            workspace,
            "--host",
            "127.0.0.1",
            "--port",
            "18123",
            "--confirm-host",
            "127.0.0.1",
            "--confirm-project",
            "local",
            "--insecure-local",
        ],
    )
    with pytest.raises(ValueError, match="Invalid workspace"):
        backup_script.main()
    connector.get_client.assert_not_called()
