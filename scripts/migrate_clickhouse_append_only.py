from __future__ import annotations

import argparse
import getpass
import os
import re
from pathlib import Path
from typing import Any

from revisionproof.bootstrap import (
    APPEND_ONLY_TABLE_LAYOUTS,
    _apply_sql_files,
    verify_append_only_layouts,
)

ROOT = Path(__file__).resolve().parents[1]
DATABASE = "revisionproof"
PROJECT_ID_RE = re.compile(r"^revisionproof-[a-z0-9-]{6,16}$")
LEGACY_LAYOUTS = {
    "revision_specs": ("ReplacingMergeTree", "run_id"),
    "version_features": (
        "ReplacingMergeTree",
        "run_id, version_label, feature_name, time_start",
    ),
    "version_checks": (
        "ReplacingMergeTree",
        "run_id, version_label, check_id",
    ),
}
CREATE_REPLACEMENTS = {
    "revision_specs": """
        CREATE TABLE revisionproof.revision_specs_append_only_v1
        (
            run_id FixedString(26),
            spec_hash FixedString(64),
            canonical_json String,
            approved_at DateTime64(3, 'UTC')
        )
        ENGINE = MergeTree
        ORDER BY (run_id, spec_hash, approved_at)
    """,
    "version_features": """
        CREATE TABLE revisionproof.version_features_append_only_v1
        (
            run_id FixedString(26),
            version_label String,
            feature_name LowCardinality(String),
            feature_value Float64,
            time_start Float32,
            time_end Float32,
            extracted_at DateTime64(3, 'UTC')
        )
        ENGINE = MergeTree
        ORDER BY (run_id, version_label, feature_name, time_start, extracted_at)
    """,
    "version_checks": """
        CREATE TABLE revisionproof.version_checks_append_only_v1
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
        ENGINE = MergeTree
        ORDER BY (run_id, version_label, check_id, checked_at)
    """,
}


def table_layout(admin: Any, table: str) -> tuple[str, str] | None:
    rows = admin.query(
        "SELECT engine, sorting_key FROM system.tables "
        "WHERE database = {database:String} AND name = {table:String}",
        parameters={"database": DATABASE, "table": table},
    ).result_rows
    if not rows:
        return None
    return str(rows[0][0]), str(rows[0][1])


def table_count(admin: Any, table: str) -> int:
    if table not in {
        *APPEND_ONLY_TABLE_LAYOUTS,
        *LEGACY_LAYOUTS,
    } and not table.endswith(("_append_only_v1", "_pre_append_only_v1")):
        raise ValueError("unexpected migration table")
    return int(admin.query(f"SELECT count() FROM {DATABASE}.{table}").result_rows[0][0])


def migrate(admin: Any) -> dict[str, int]:
    migrated: dict[str, int] = {}
    for table, expected_layout in APPEND_ONLY_TABLE_LAYOUTS.items():
        current_layout = table_layout(admin, table)
        if current_layout == expected_layout:
            continue
        if current_layout != LEGACY_LAYOUTS[table]:
            raise RuntimeError(f"refusing unexpected schema for {DATABASE}.{table}")
        replacement = f"{table}_append_only_v1"
        backup = f"{table}_pre_append_only_v1"
        if (
            table_layout(admin, replacement) is not None
            or table_layout(admin, backup) is not None
        ):
            raise RuntimeError(
                f"refusing partial prior migration for {DATABASE}.{table}"
            )
        admin.command(CREATE_REPLACEMENTS[table])
        admin.command(
            f"INSERT INTO {DATABASE}.{replacement} SELECT * FROM {DATABASE}.{table}"
        )
        before = table_count(admin, table)
        if table_count(admin, replacement) != before:
            raise RuntimeError(f"row count mismatch while migrating {DATABASE}.{table}")
        admin.command(
            f"RENAME TABLE {DATABASE}.{table} TO {DATABASE}.{backup}, "
            f"{DATABASE}.{replacement} TO {DATABASE}.{table}"
        )
        if table_count(admin, table) != before or table_count(admin, backup) != before:
            raise RuntimeError(f"row count mismatch after migrating {DATABASE}.{table}")
        migrated[table] = before
    _apply_sql_files(admin, ROOT)
    verify_append_only_layouts(admin)
    return migrated


def verify_cloud_deployment_metadata(admin: Any, project_id: str, host: str) -> None:
    rows = admin.query(
        "SELECT project_id, clickhouse_host FROM revisionproof.deployment_metadata"
    ).result_rows
    actual = [(str(row[0]), str(row[1])) for row in rows]
    if actual != [(project_id, host)]:
        raise RuntimeError(
            "refusing migration: ClickHouse deployment metadata does not match confirmations"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate the three legacy RevisionProof tables to append-only layouts."
    )
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--username", default="default")
    parser.add_argument("--insecure-local", action="store_true")
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--confirm-host", required=True)
    parser.add_argument("--confirm-project", required=True)
    args = parser.parse_args()
    if args.confirm != DATABASE:
        raise ValueError(f"--confirm must be exactly {DATABASE}")
    if args.confirm_host != args.host:
        raise ValueError("--confirm-host must exactly match --host")
    if args.insecure_local:
        if args.host not in {"localhost", "127.0.0.1", "::1"} or args.port != 8123:
            raise ValueError("--insecure-local is restricted to loopback port 8123")
        if args.confirm_project != "local":
            raise ValueError("local migration requires --confirm-project local")
    elif not args.host.endswith(".clickhouse.cloud") or args.port != 8443:
        raise ValueError(
            "cloud migration requires a .clickhouse.cloud host on TLS port 8443"
        )
    elif not PROJECT_ID_RE.fullmatch(args.confirm_project):
        raise ValueError("cloud migration requires a dedicated revisionproof-* project")
    password = os.environ.get(
        "REVISIONPROOF_CLICKHOUSE_ADMIN_PASSWORD"
    ) or getpass.getpass("ClickHouse admin password: ")
    if not password:
        raise ValueError("ClickHouse admin password is required")
    try:
        import clickhouse_connect
    except ImportError as exc:
        raise RuntimeError("install the backend 'live' extra first") from exc
    admin = clickhouse_connect.get_client(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
        database="default",
        secure=not args.insecure_local,
        verify=not args.insecure_local,
    )
    try:
        if not args.insecure_local:
            verify_cloud_deployment_metadata(
                admin, args.confirm_project, args.confirm_host
            )
        result = migrate(admin)
    finally:
        admin.close()
    print("PASS append-only migration; preserved backups; rows=" + repr(result))


if __name__ == "__main__":
    main()
