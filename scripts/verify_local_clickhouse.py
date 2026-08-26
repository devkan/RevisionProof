from __future__ import annotations

import argparse

from revisionproof.bootstrap import _provision_users
from revisionproof.settings import Settings

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
EXTRA_ROLE = "revisionproof_extra_test"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify RevisionProof role convergence against loopback ClickHouse only."
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--admin-username", default="revisionproof")
    parser.add_argument("--admin-password", default="revisionproof-local")
    args = parser.parse_args()
    if args.host not in LOOPBACK_HOSTS or args.port != 8123:
        raise ValueError(
            "this adversarial permission check is restricted to loopback port 8123"
        )

    try:
        import clickhouse_connect
    except ImportError as exc:
        raise RuntimeError("install the backend live extra first") from exc
    admin = clickhouse_connect.get_client(
        host=args.host,
        port=args.port,
        username=args.admin_username,
        password=args.admin_password,
        database="default",
        secure=False,
        verify=False,
    )
    settings = Settings(
        clickhouse_host=args.host,
        clickhouse_port=args.port,
        clickhouse_secure=False,
        clickhouse_verify=False,
        clickhouse_writer_password="writer-local-test",
        clickhouse_mcp_password="mcp-local-test",
    )
    try:
        _provision_users(admin, settings)
        admin.command(f"CREATE ROLE IF NOT EXISTS {EXTRA_ROLE}")
        admin.command("GRANT SELECT ON system.one TO revisionproof_writer_user")
        admin.command(f"GRANT {EXTRA_ROLE} TO revisionproof_writer_user")
        admin.command(f"GRANT {EXTRA_ROLE} TO revisionproof_writer")
        _provision_users(admin, settings)

        rows = admin.query(
            "SELECT user_name, role_name, granted_role_name FROM system.role_grants "
            "WHERE user_name IN "
            "('revisionproof_writer_user','revisionproof_mcp_user',"
            "'revisionproof_view_definer_user') "
            "OR role_name IN "
            "('revisionproof_writer','revisionproof_mcp_reader','revisionproof_view_definer') "
            "ORDER BY user_name, role_name, granted_role_name"
        ).result_rows
        expected = [
            ("revisionproof_mcp_user", None, "revisionproof_mcp_reader"),
            (
                "revisionproof_view_definer_user",
                None,
                "revisionproof_view_definer",
            ),
            ("revisionproof_writer_user", None, "revisionproof_writer"),
        ]
        if rows != expected:
            raise RuntimeError(f"role membership did not converge: {rows!r}")
        grants = [
            str(row[0])
            for row in admin.query(
                "SHOW GRANTS FOR revisionproof_writer_user"
            ).result_rows
        ]
        if any("system.one" in grant for grant in grants):
            raise RuntimeError("direct writer grant survived convergence")
    finally:
        admin.command(f"DROP ROLE IF EXISTS {EXTRA_ROLE}")
        admin.close()
    print(
        "PASS excessive direct and inherited grants converged to exact RevisionProof roles"
    )


if __name__ == "__main__":
    main()
