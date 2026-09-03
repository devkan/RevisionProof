"""Exercise the real 26.2 schema, official MCP, vector engines and retry-safe MV on loopback."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from revisionproof.bootstrap import _provision_users
from revisionproof.evidence.live import ClickHouseWriter, McpClickHouseReader
from revisionproof.intelligence.queries import build_memory_search_query
from revisionproof.intelligence.schema import (
    migrate_intelligence,
    verify_intelligence_schema,
)
from revisionproof.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18123, choices=[8123, 18123])
    args = parser.parse_args()
    import clickhouse_connect

    admin = clickhouse_connect.get_client(
        host="127.0.0.1",
        port=args.port,
        username="revisionproof",
        password="revisionproof-local",
        secure=False,
    )
    settings = Settings(
        clickhouse_host="127.0.0.1",
        clickhouse_port=args.port,
        clickhouse_secure=False,
        clickhouse_verify=False,
        clickhouse_writer_password="writer-local-test",
        clickhouse_mcp_password="mcp-local-test",
    )
    try:
        migration = migrate_intelligence(admin, ROOT)
        _provision_users(admin, settings)
        verify_intelligence_schema(admin)
        writer = ClickHouseWriter(settings)
        reader = McpClickHouseReader(settings)
        # The benchmark namespace is isolated from product memory, and explicitly synthetic.
        workspace = "benchmark-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        rng = np.random.default_rng(42)
        vectors = rng.normal(size=(12000, 768)).astype(np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        now = datetime.now(UTC)
        rows = [
            [
                workspace,
                hashlib.sha256(f"{workspace}:{i}".encode()).hexdigest(),
                "01M00000000000000000000000",
                "0" * 64,
                f"Synthetic benchmark item {i}",
                "Synthetic only",
                "B",
                1.12,
                6.0,
                "benchmark-768",
                vector.tolist(),
                "{}",
                now,
            ]
            for i, vector in enumerate(vectors)
        ]
        # One batch creates enough granules for EXPLAIN to expose an actual HNSW index.
        client = writer._client()
        try:
            client.insert(
                "approved_edits",
                rows,
                column_names=[
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
                settings={"max_insert_block_size": 20000},
            )
        finally:
            client.close()
        results = {}
        for engine in ("exact", "hnsw", "qbit"):
            query = build_memory_search_query(
                workspace, "benchmark-768", vectors[42].tolist(), engine
            )
            result = asyncio.run(reader.run_query(query))
            if not result:
                raise RuntimeError(f"{engine} returned no results")
            results[engine] = result
        expected = {row["memory_id"] for row in results["exact"]}
        recalls = {
            engine: len(expected & {row["memory_id"] for row in rows}) / len(expected)
            for engine, rows in results.items()
        }
        if any(value < 0.8 for value in recalls.values()):
            raise RuntimeError(f"vector recall below 0.8: {recalls}")
        plan = asyncio.run(
            reader.run_query(
                "EXPLAIN indexes = 1 "
                + build_memory_search_query(
                    workspace, "benchmark-768", vectors[42].tolist(), "hnsw"
                )
            )
        )
        plan_text = "\n".join(str(value) for row in plan for value in row.values())
        if (
            "approved_edit_hnsw" not in plan_text
            or "vector_similarity" not in plan_text
        ):
            raise RuntimeError("HNSW was not selected by ClickHouse:\n" + plan_text)
        pair = [
            workspace,
            "01M00000000000000000000000",
            "test",
            "0" * 64,
            "01M00000000000000000000001",
            8250,
            0.15,
            0.01,
            0.0,
            0.1,
            1,
            now,
        ]
        writer.insert_frame_pairs([pair])
        writer.insert_frame_pairs([pair])
        grouped = asyncio.run(
            reader.run_query(
                "SELECT second, sample_count, visual_delta FROM revision_change_map "
                f"WHERE workspace_id = '{workspace}'"
            )
        )
        if len(grouped) != 1 or int(grouped[0]["sample_count"]) != 1:
            raise RuntimeError("Duplicate insert inflated the Change Map")
        try:
            asyncio.run(
                reader.run_query("SELECT * FROM revisionproof.approved_edits LIMIT 1")
            )
        except RuntimeError:
            pass
        else:
            raise RuntimeError("MCP reader unexpectedly accessed the raw memory table")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "version": admin.query("SELECT version()").result_rows[0][0],
                    "migration": migration,
                    "benchmark_workspace": workspace,
                    "synthetic_rows": len(vectors),
                    "recall_at_15": recalls,
                    "hnsw_explain_verified": True,
                    "duplicate_mv_samples": 1,
                    "mcp_base_table_access": "DENIED",
                },
                indent=2,
            )
        )
    finally:
        admin.close()


if __name__ == "__main__":
    main()
