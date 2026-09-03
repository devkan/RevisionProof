from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from revisionproof.bootstrap import (
    VIEW_DEFINER_USER,
    normalize_clickhouse_engine,
    split_sql_statements,
)

TABLES = {
    "revision_frame_pairs": "MergeTree",
    "revision_change_windows": "AggregatingMergeTree",
    "revision_change_windows_mv": "MaterializedView",
    "revision_change_map": "View",
    "approved_edits": "MergeTree",
    "approved_edit_memory": "View",
    "approved_edit_neighbors": "View",
}


def require_supported_version(version: str) -> None:
    match = re.match(r"^(\d+)\.(\d+)", version)
    if not match or tuple(map(int, match.groups())) < (26, 2):
        raise ValueError("Revision intelligence requires ClickHouse 26.2 or newer")


def verify_intelligence_schema(admin: Any) -> None:
    rows = admin.query(
        "SELECT name, engine, definer, create_table_query FROM system.tables "
        "WHERE database = 'revisionproof' AND name IN {names:Array(String)}",
        parameters={"names": list(TABLES)},
    ).result_rows
    if {str(row[0]) for row in rows} != set(TABLES):
        raise RuntimeError("Revision intelligence schema is incomplete")
    for name, engine, definer, ddl in rows:
        logical = str(engine).removeprefix("Shared")
        if logical != TABLES[str(name)]:
            raise RuntimeError(f"Unexpected intelligence table engine: {name}")
        if logical in {"View", "MaterializedView"} and (
            str(definer) != VIEW_DEFINER_USER or "SQL SECURITY DEFINER" not in str(ddl)
        ):
            raise RuntimeError(f"Unsafe intelligence view definer: {name}")
        if name == "approved_edits" and (
            "QBit(Float32, 768)" not in str(ddl) or "approved_edit_hnsw" not in str(ddl)
        ):
            raise RuntimeError("Approved memory vector schema is incomplete")


def migrate_intelligence(admin: Any, root: Path) -> dict[str, Any]:
    require_supported_version(str(admin.query("SELECT version()").result_rows[0][0]))
    before = admin.query(
        "SELECT name, engine FROM system.tables WHERE database = 'revisionproof'"
    ).result_rows
    current = {str(name): normalize_clickhouse_engine(str(engine)) for name, engine in before}
    for name in set(current) & set(TABLES):
        if current[name].removeprefix("Shared") != TABLES[name]:
            raise RuntimeError(f"Refusing to modify a drifted table: {name}")
    # IF NOT EXISTS allows safe reruns, including a previous interrupted additive migration.
    sql = (root / "infra/clickhouse/intelligence.sql").read_text(encoding="utf-8")
    for statement in split_sql_statements(sql):
        admin.command(statement)
    verify_intelligence_schema(admin)
    return {"created": sorted(set(TABLES) - set(current)), "preserved": sorted(current)}
