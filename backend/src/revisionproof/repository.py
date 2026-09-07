from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from revisionproof.contracts import RunEvent, RunSnapshot, RunState


class RunNotFoundError(KeyError):
    pass


class RunCapacityBusyError(ValueError):
    def __init__(self, retry_after_seconds: int = 5) -> None:
        super().__init__("run capacity is temporarily busy; retry this request")
        self.retry_after_seconds = retry_after_seconds


class InMemoryRunRepository:
    def __init__(self, max_runs: int = 64) -> None:
        if max_runs < 1:
            raise ValueError("max_runs must be positive")
        self._max_runs = max_runs
        self._runs: OrderedDict[str, RunSnapshot] = OrderedDict()
        self._source_paths: dict[str, Path] = {}
        self._version_paths: dict[str, Path] = {}
        self._locks: dict[str, threading.RLock] = {}
        self._active_runs: dict[str, int] = {}
        self._on_evict: Callable[[str], None] | None = None
        self._idempotency: OrderedDict[tuple[str, str], tuple[str, str]] = OrderedDict()
        self._max_idempotency_records = max_runs * 16
        self._idempotency_lock = threading.RLock()

    def set_eviction_callback(self, callback: Callable[[str], None]) -> None:
        with self._idempotency_lock:
            self._on_evict = callback

    def create(
        self,
        snapshot: RunSnapshot,
        source_path: Path,
        *,
        active: bool = False,
    ) -> RunSnapshot:
        with self._idempotency_lock:
            if snapshot.run_id in self._runs:
                raise ValueError("run already exists")
            if len(self._runs) >= self._max_runs:
                self._evict_oldest_inactive_run()
            self._runs[snapshot.run_id] = snapshot
            self._source_paths[snapshot.run_id] = source_path
            self._locks[snapshot.run_id] = threading.RLock()
            if active:
                self._active_runs[snapshot.run_id] = 1
            self.append_event(snapshot.run_id, snapshot.state, "Source asset indexed")
            return snapshot

    def _evict_oldest_inactive_run(self) -> None:
        run_id = next(
            (candidate for candidate in self._runs if self._active_runs.get(candidate, 0) == 0),
            None,
        )
        if run_id is None:
            raise RunCapacityBusyError
        if self._on_evict is not None:
            self._on_evict(run_id)
        self._runs.pop(run_id, None)
        self._source_paths.pop(run_id, None)
        self._version_paths.pop(run_id, None)
        self._locks.pop(run_id, None)
        stale_keys = [
            record_key
            for record_key, (_, recorded_run_id) in self._idempotency.items()
            if recorded_run_id == run_id
        ]
        for record_key in stale_keys:
            self._idempotency.pop(record_key, None)

    @contextmanager
    def locked(self, run_id: str) -> Iterator[None]:
        with self._idempotency_lock:
            if run_id not in self._runs:
                raise RunNotFoundError(run_id)
            lock = self._locks[run_id]
            self._active_runs[run_id] = self._active_runs.get(run_id, 0) + 1
            self._runs.move_to_end(run_id)
        try:
            with lock:
                yield
        finally:
            self.release_active(run_id)

    def acquire_active(self, run_id: str) -> None:
        with self._idempotency_lock:
            if run_id not in self._runs:
                raise RunNotFoundError(run_id)
            self._active_runs[run_id] = self._active_runs.get(run_id, 0) + 1
            self._runs.move_to_end(run_id)

    def release_active(self, run_id: str) -> None:
        with self._idempotency_lock:
            remaining = self._active_runs.get(run_id, 1) - 1
            if remaining > 0:
                self._active_runs[run_id] = remaining
            else:
                self._active_runs.pop(run_id, None)

    def get(self, run_id: str) -> RunSnapshot:
        with self._idempotency_lock:
            try:
                snapshot = self._runs[run_id]
            except KeyError as exc:
                raise RunNotFoundError(run_id) from exc
            self._runs.move_to_end(run_id)
            return snapshot

    def source_path(self, run_id: str) -> Path:
        with self._idempotency_lock:
            self.get(run_id)
            return self._source_paths[run_id]

    def set_version_path(self, run_id: str, path: Path) -> None:
        with self._idempotency_lock:
            self.get(run_id)
            self._version_paths[run_id] = path

    def version_path(self, run_id: str) -> Path:
        with self._idempotency_lock:
            self.get(run_id)
            return self._version_paths[run_id]

    def append_event(self, run_id: str, state: RunState, message: str) -> RunEvent:
        with self._idempotency_lock:
            snapshot = self.get(run_id)
            event = RunEvent(
                sequence=len(snapshot.events) + 1,
                state=state,
                message=message,
                occurred_at=datetime.now(UTC),
            )
            snapshot.events.append(event)
            return event

    def recall_idempotent(
        self, scope: str, key: str | None, fingerprint: str
    ) -> RunSnapshot | None:
        if key is None:
            return None
        with self._idempotency_lock:
            record = self._idempotency.get((scope, key))
            if record is None:
                return None
            recorded_fingerprint, run_id = record
            if recorded_fingerprint != fingerprint:
                raise ValueError("idempotency key was already used with a different request")
            self._idempotency.move_to_end((scope, key))
            return self.get(run_id)

    def remember_idempotent(
        self, scope: str, key: str | None, fingerprint: str, run_id: str
    ) -> None:
        if key is None:
            return
        with self._idempotency_lock:
            existing = self._idempotency.get((scope, key))
            if existing is not None and existing != (fingerprint, run_id):
                raise ValueError("idempotency key was already used with a different request")
            self._idempotency[(scope, key)] = (fingerprint, run_id)
            self._idempotency.move_to_end((scope, key))
            while len(self._idempotency) > self._max_idempotency_records:
                self._idempotency.popitem(last=False)
