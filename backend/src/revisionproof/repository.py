from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from revisionproof.contracts import RunEvent, RunSnapshot, RunState


class RunNotFoundError(KeyError):
    pass


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, RunSnapshot] = {}
        self._source_paths: dict[str, Path] = {}
        self._version_paths: dict[str, Path] = {}
        self._locks: dict[str, threading.RLock] = {}

    def create(self, snapshot: RunSnapshot, source_path: Path) -> RunSnapshot:
        self._runs[snapshot.run_id] = snapshot
        self._source_paths[snapshot.run_id] = source_path
        self._locks[snapshot.run_id] = threading.RLock()
        self.append_event(snapshot.run_id, snapshot.state, "Source asset indexed")
        return snapshot

    @contextmanager
    def locked(self, run_id: str) -> Iterator[None]:
        self.get(run_id)
        with self._locks[run_id]:
            yield

    def get(self, run_id: str) -> RunSnapshot:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise RunNotFoundError(run_id) from exc

    def source_path(self, run_id: str) -> Path:
        self.get(run_id)
        return self._source_paths[run_id]

    def set_version_path(self, run_id: str, path: Path) -> None:
        self.get(run_id)
        self._version_paths[run_id] = path

    def version_path(self, run_id: str) -> Path:
        self.get(run_id)
        return self._version_paths[run_id]

    def append_event(self, run_id: str, state: RunState, message: str) -> RunEvent:
        snapshot = self._runs[run_id]
        event = RunEvent(
            sequence=len(snapshot.events) + 1,
            state=state,
            message=message,
            occurred_at=datetime.now(UTC),
        )
        snapshot.events.append(event)
        return event
