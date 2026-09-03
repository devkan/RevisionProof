"""Additive migration. Exact host/project confirmation; no destructive SQL."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
from pathlib import Path

from revisionproof.intelligence.schema import (
    TABLES,
    migrate_intelligence,
    require_supported_version,
)

ROOT = Path(__file__).resolve().parents[1]


def validate_target(
    host: str, port: int, confirm_host: str, project: str, local: bool
) -> None:
    if host != confirm_host:
        raise ValueError("--confirm-host must exactly match --host")
    if local:
        if (
            host not in {"localhost", "127.0.0.1", "::1"}
            or port not in {8123, 18123}
            or project != "local"
        ):
            raise ValueError(
                "local migration is restricted to loopback and --confirm-project local"
            )
    elif not (
        re.fullmatch(r"[a-z0-9][a-z0-9.-]*\.clickhouse\.cloud", host)
        and port == 8443
        and re.fullmatch(r"revisionproof-[a-z0-9-]{6,24}", project)
    ):
        raise ValueError(
            "Cloud migration requires the dedicated RevisionProof TLS service"
        )


def verify_target(admin, project: str, host: str) -> None:
    actual = admin.query(
        "SELECT project_id, clickhouse_host FROM revisionproof.deployment_metadata"
    ).result_rows
    if [tuple(map(str, row)) for row in actual] != [(project, host)]:
        raise RuntimeError("Refusing migration: exact deployment sentinel mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--username", default="default")
    parser.add_argument("--confirm-host", required=True)
    parser.add_argument("--confirm-project", required=True)
    parser.add_argument("--insecure-local", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
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
    admin = clickhouse_connect.get_client(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
        secure=not args.insecure_local,
        verify=not args.insecure_local,
    )
    try:
        if not args.insecure_local:
            verify_target(admin, args.confirm_project, args.host)
        version = str(admin.query("SELECT version()").result_rows[0][0])
        require_supported_version(version)
        result = (
            migrate_intelligence(admin, ROOT)
            if args.apply
            else {"would_ensure": list(TABLES)}
        )
        print(
            json.dumps(
                {
                    "applied": args.apply,
                    "host": args.host,
                    "project": args.confirm_project,
                    "version": version,
                    **result,
                },
                indent=2,
            )
        )
    finally:
        admin.close()


if __name__ == "__main__":
    main()
