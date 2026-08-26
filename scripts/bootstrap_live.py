from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path

from revisionproof.bootstrap import bootstrap_live
from revisionproof.contracts import ExecutionMode
from revisionproof.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def secret_or_prompt(env_name: str, prompt: str) -> str:
    value = os.environ.get(env_name)
    if value:
        return value
    value = getpass.getpass(prompt)
    if not value:
        raise ValueError(f"{env_name} is required")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Provision the RevisionProof ClickHouse schema and users, upload the source "
            "asset to GCS, seed Vertex embeddings, and verify official MCP reads."
        )
    )
    parser.add_argument(
        "--clickhouse-admin-username",
        default=os.environ.get("REVISIONPROOF_CLICKHOUSE_ADMIN_USERNAME", "default"),
    )
    args = parser.parse_args()

    writer_password = secret_or_prompt(
        "REVISIONPROOF_CLICKHOUSE_WRITER_PASSWORD",
        "RevisionProof ClickHouse writer password: ",
    )
    mcp_password = secret_or_prompt(
        "REVISIONPROOF_CLICKHOUSE_MCP_PASSWORD",
        "RevisionProof ClickHouse MCP reader password: ",
    )
    admin_password = secret_or_prompt(
        "REVISIONPROOF_CLICKHOUSE_ADMIN_PASSWORD",
        "ClickHouse Cloud admin password: ",
    )
    settings = Settings(
        mode=ExecutionMode.LIVE,
        clickhouse_writer_password=writer_password,
        clickhouse_mcp_password=mcp_password,
    )
    result = bootstrap_live(
        settings,
        clickhouse_admin_username=args.clickhouse_admin_username,
        clickhouse_admin_password=admin_password,
        repo_root=ROOT,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
