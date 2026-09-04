from __future__ import annotations

import asyncio

from revisionproof.evidence.live import McpClickHouseReader
from revisionproof.settings import Settings


async def verify() -> None:
    settings = Settings(
        clickhouse_host="localhost",
        clickhouse_port=8123,
        clickhouse_secure=False,
        clickhouse_verify=False,
        clickhouse_writer_password="writer-local-test",
        clickhouse_mcp_password="mcp-local-test",
    )
    reader = McpClickHouseReader(settings)
    rows = await reader.run_query("SELECT count() AS segment_count FROM search_segments")
    if len(rows) != 1 or int(rows[0]["segment_count"]) < 0:
        raise RuntimeError("official mcp-clickhouse returned an invalid view result")
    try:
        await reader.run_query("SELECT count() FROM segments")
    except RuntimeError:
        pass
    else:
        raise RuntimeError("MCP reader unexpectedly read the segments base table")
    print(
        "PASS official mcp-clickhouse run_query read the view and denied the base table; "
        f"segments={rows[0]['segment_count']}"
    )


if __name__ == "__main__":
    asyncio.run(verify())
