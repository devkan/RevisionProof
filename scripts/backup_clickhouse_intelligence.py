"""Portable, workspace-scoped export/restore. Restore is dry-run unless --apply is explicit."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from migrate_clickhouse_intelligence import validate_target, verify_target
from revisionproof.intelligence.schema import (
    require_supported_version,
    verify_intelligence_schema,
)

TABLE_COLUMNS = {
    "approved_edits": [
        "workspace_id",
        "memory_id",
        "run_id",
        "spec_hash",
        "intent",
        "target_phrase",
        "candidate_id",
        "scale",
        "duration_seconds",
        "embedding_model",
        "embedding",
        "proof_json",
        "approved_at",
    ],
    "approved_edit_recipes": [
        "workspace_id",
        "memory_id",
        "run_id",
        "spec_hash",
        "intent",
        "target_phrase",
        "candidate_id",
        "duration_seconds",
        "operations_json",
        "embedding_model",
        "embedding",
        "proof_json",
        "approved_at",
    ],
    "revision_frame_pairs": [
        "workspace_id",
        "run_id",
        "version_label",
        "spec_hash",
        "analysis_id",
        "sample_ms",
        "visual_delta",
        "residual_delta",
        "cta_delta",
        "audio_delta_db",
        "requested",
        "measured_at",
    ],
}
FORMAT_VERSION = 2
BACKUP_SCHEMAS = {
    1: {
        name: columns
        for name, columns in TABLE_COLUMNS.items()
        if name != "approved_edit_recipes"
    },
    2: TABLE_COLUMNS,
}
MAX_LINE_BYTES = 1024 * 1024


def inspect_file(path: Path, columns: list[str], workspace: str) -> tuple[str, int]:
    digest, count = hashlib.sha256(), 0
    with path.open("rb") as handle:
        while line := handle.readline(MAX_LINE_BYTES + 1):
            if len(line) > MAX_LINE_BYTES:
                raise ValueError("Backup row exceeds the bounded import size")
            digest.update(line)
            row = json.loads(line)
            if set(row) != set(columns) or row["workspace_id"] != workspace:
                raise ValueError(
                    "Backup contains unexpected columns or a different workspace"
                )
            count += 1
    return digest.hexdigest(), count


def export_workspace(client, directory: Path, workspace: str) -> dict:
    # Exclusive directory creation: never overwrite a prior export, including a partial one.
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "format_version": FORMAT_VERSION,
        "workspace": workspace,
        "created_at": datetime.now(UTC).isoformat(),
        "tables": {},
    }
    for table, columns in TABLE_COLUMNS.items():
        path = directory / f"{table}.jsonl"
        query = f"SELECT {', '.join(columns)} FROM revisionproof.{table} WHERE workspace_id = {{workspace:String}}"
        with (
            client.raw_stream(
                query, parameters={"workspace": workspace}, fmt="JSONEachRow"
            ) as stream,
            path.open("xb") as output,
        ):
            while chunk := stream.read(1024 * 1024):
                output.write(chunk)
        checksum, count = inspect_file(path, columns, workspace)
        manifest["tables"][table] = {"sha256": checksum, "rows": count}
    # A complete manifest is the commit marker. A partial export cannot be restored.
    with (directory / "manifest.json").open("x", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2)
    return manifest


def restore_workspace(client, directory: Path, workspace: str, apply: bool) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    columns_by_table = BACKUP_SCHEMAS.get(manifest.get("format_version"))
    if (
        columns_by_table is None
        or manifest.get("workspace") != workspace
        or set(manifest.get("tables", {})) != set(columns_by_table)
    ):
        raise ValueError(
            "Backup manifest does not match the requested workspace/schema"
        )
    # Validate ALL files and destinations before any insert. Never merge into existing data.
    for table, columns in columns_by_table.items():
        path = directory / f"{table}.jsonl"
        if path.is_symlink() or path.resolve().parent != directory.resolve():
            raise ValueError("Backup paths must remain inside the export directory")
        checksum, count = inspect_file(path, columns, workspace)
        if manifest["tables"][table] != {"sha256": checksum, "rows": count}:
            raise ValueError(f"Backup checksum or row count mismatch: {table}")
    for table in [*TABLE_COLUMNS, "revision_change_windows"]:
        rows = client.query(
            f"SELECT count() FROM revisionproof.{table} WHERE workspace_id = {{workspace:String}}",
            parameters={"workspace": workspace},
        ).result_rows[0][0]
        if rows:
            raise ValueError(
                f"Refusing restore into non-empty workspace table: {table}"
            )
    if apply:
        for table, columns in columns_by_table.items():
            if manifest["tables"][table]["rows"]:
                with (directory / f"{table}.jsonl").open("rb") as data:
                    client.raw_insert(
                        f"revisionproof.{table}",
                        column_names=columns,
                        insert_block=data,
                        fmt="JSONEachRow",
                    )
            count = client.query(
                f"SELECT count() FROM revisionproof.{table} WHERE workspace_id = {{workspace:String}}",
                parameters={"workspace": workspace},
            ).result_rows[0][0]
            if int(count) != manifest["tables"][table]["rows"]:
                raise RuntimeError(
                    f"Restore count mismatch: {table}. Stop; do not blindly retry."
                )
    return {"applied": apply, "workspace": workspace, "tables": manifest["tables"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "restore"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--workspace", default="revisionproof-demo")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--username", default="default")
    parser.add_argument("--confirm-host", required=True)
    parser.add_argument("--confirm-project", required=True)
    parser.add_argument("--insecure-local", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", args.workspace):
        raise ValueError("Invalid workspace id")
    validate_target(
        args.host,
        args.port,
        args.confirm_host,
        args.confirm_project,
        args.insecure_local,
    )
    import clickhouse_connect

    password = os.environ.get(
        "REVISIONPROOF_CLICKHOUSE_ADMIN_PASSWORD"
    ) or getpass.getpass("ClickHouse admin password: ")
    client = clickhouse_connect.get_client(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
        secure=not args.insecure_local,
        verify=not args.insecure_local,
    )
    try:
        if not args.insecure_local:
            verify_target(client, args.confirm_project, args.host)
        require_supported_version(
            str(client.query("SELECT version()").result_rows[0][0])
        )
        verify_intelligence_schema(client)
        result = (
            export_workspace(client, args.directory, args.workspace)
            if args.action == "export"
            else restore_workspace(client, args.directory, args.workspace, args.apply)
        )
        print(json.dumps(result, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
