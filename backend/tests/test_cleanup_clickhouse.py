from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_cleanup_module():
    script = Path(__file__).resolve().parents[2] / "scripts" / "cleanup_clickhouse.py"
    spec = importlib.util.spec_from_file_location("cleanup_clickhouse", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeAdmin:
    def __init__(self, query_results: list[int] | None = None) -> None:
        self.commands: list[str] = []
        self.queries: list[tuple[tuple, dict]] = []
        self.query_results = query_results or [0, 0, 0]

    def command(self, query: str) -> None:
        self.commands.append(query)

    def query(self, *args, **kwargs):
        self.queries.append((args, kwargs))
        return SimpleNamespace(result_rows=[(self.query_results.pop(0),)])


def test_cleanup_drops_database_before_dependent_users_and_roles() -> None:
    cleanup_clickhouse = _load_cleanup_module()
    admin = FakeAdmin()

    cleanup_clickhouse.cleanup(admin)

    assert admin.commands[0] == "DROP DATABASE IF EXISTS revisionproof SYNC"
    assert admin.commands[1:4] == [
        "DROP USER IF EXISTS revisionproof_writer_user",
        "DROP USER IF EXISTS revisionproof_mcp_user",
        "DROP USER IF EXISTS revisionproof_view_definer_user",
    ]
    assert admin.commands[4:] == [
        "DROP ROLE IF EXISTS revisionproof_writer",
        "DROP ROLE IF EXISTS revisionproof_mcp_reader",
        "DROP ROLE IF EXISTS revisionproof_view_definer",
    ]
    assert len(admin.queries) == 3
    assert admin.queries[1][1]["parameters"]["users"] == list(cleanup_clickhouse.USERS)
    assert admin.queries[2][1]["parameters"]["roles"] == list(cleanup_clickhouse.ROLES)


@pytest.mark.parametrize(
    ("remaining", "message"),
    [
        ([1, 0, 0], "cleanup verification failed"),
        ([0, 1, 0], "identity cleanup verification failed"),
        ([0, 0, 1], "identity cleanup verification failed"),
    ],
)
def test_cleanup_fails_closed_when_any_resource_remains(remaining: list[int], message: str) -> None:
    cleanup_clickhouse = _load_cleanup_module()
    admin = FakeAdmin(remaining)

    with pytest.raises(RuntimeError, match=message):
        cleanup_clickhouse.cleanup(admin)
