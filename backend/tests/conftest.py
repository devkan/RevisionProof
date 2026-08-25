from pathlib import Path

import pytest

from revisionproof.contracts import ExecutionMode
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def runtime_dir() -> Path:
    return REPO_ROOT / "runtime"


@pytest.fixture
def service(runtime_dir: Path) -> RevisionProofService:
    settings = Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime_dir)
    return RevisionProofService(settings, InMemoryRunRepository())
