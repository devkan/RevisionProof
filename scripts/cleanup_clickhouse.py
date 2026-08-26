from __future__ import annotations

import argparse
import getpass
import os
import re

DATABASE = "revisionproof"
PROJECT_ID_RE = re.compile(r"^revisionproof-[a-z0-9-]{6,16}$")
CLOUD_HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.clickhouse\.cloud$")
USERS = (
    "revisionproof_writer_user",
    "revisionproof_mcp_user",
    "revisionproof_view_definer_user",
)
ROLES = (
    "revisionproof_writer",
    "revisionproof_mcp_reader",
    "revisionproof_view_definer",
)


def verify_deployment_metadata(admin, project_id: str, host: str) -> None:
    rows = admin.query(
        "SELECT project_id, clickhouse_host FROM revisionproof.deployment_metadata"
    ).result_rows
    actual = [(str(row[0]), str(row[1])) for row in rows]
    if actual != [(project_id, host)]:
        raise RuntimeError(
            "refusing cleanup: ClickHouse deployment metadata does not match confirmations"
        )


def cleanup(admin) -> None:
    # Views depend on the non-login definer user, so remove the sentinel-verified
    # database first. Dropping users before their views fails closed in ClickHouse.
    admin.command(f"DROP DATABASE IF EXISTS {DATABASE} SYNC")
    for user in USERS:
        admin.command(f"DROP USER IF EXISTS {user}")
    for role in ROLES:
        admin.command(f"DROP ROLE IF EXISTS {role}")
    remaining = admin.query(
        "SELECT count() FROM system.databases WHERE name = {database:String}",
        parameters={"database": DATABASE},
    ).result_rows[0][0]
    if int(remaining) != 0:
        raise RuntimeError("ClickHouse cleanup verification failed")
    remaining_users = admin.query(
        "SELECT count() FROM system.users WHERE name IN {users:Array(String)}",
        parameters={"users": list(USERS)},
    ).result_rows[0][0]
    remaining_roles = admin.query(
        "SELECT count() FROM system.roles WHERE name IN {roles:Array(String)}",
        parameters={"roles": list(ROLES)},
    ).result_rows[0][0]
    if int(remaining_users) != 0 or int(remaining_roles) != 0:
        raise RuntimeError("ClickHouse identity cleanup verification failed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete only a sentinel-verified RevisionProof ClickHouse deployment."
    )
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--username", default="default")
    parser.add_argument("--confirm-host", required=True)
    parser.add_argument("--confirm-project", required=True)
    parser.add_argument("--confirm-database", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise ValueError(
            "cleanup is dry by default; pass --execute only after inventory review"
        )
    if args.confirm_database != DATABASE:
        raise ValueError(f"--confirm-database must be exactly {DATABASE}")
    if args.confirm_host != args.host:
        raise ValueError("--confirm-host must exactly match --host")
    if not CLOUD_HOST_RE.fullmatch(args.host) or args.port != 8443:
        raise ValueError("cleanup requires a ClickHouse Cloud TLS host on port 8443")
    if not PROJECT_ID_RE.fullmatch(args.confirm_project):
        raise ValueError("cleanup requires a dedicated revisionproof-* project")

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
        secure=True,
        verify=True,
    )
    try:
        verify_deployment_metadata(admin, args.confirm_project, args.confirm_host)
        cleanup(admin)
    finally:
        admin.close()
    print("PASS removed only the sentinel-verified RevisionProof ClickHouse deployment")


if __name__ == "__main__":
    main()
