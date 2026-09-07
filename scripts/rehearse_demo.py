from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import (
    ApprovalRequest,
    CreateRunRequest,
    ExecutionMode,
    RunState,
)
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


async def rehearse(index: int) -> dict[str, str | int]:
    runtime = ROOT / "runtime"
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=runtime),
        InMemoryRunRepository(),
    )
    snapshot = await service.create_run(
        CreateRunRequest(
            asset_id=DEMO_ASSET_ID,
            feedback=(
                '1. When the presenter says "RevisionProof," push in slightly.\n'
                "2. Make the middle feel more dynamic.\n"
                "3. Add B-roll that feels more premium and on-brand."
            ),
        )
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    v2 = runtime / "demo" / "revisionproof_v2_blocked.mp4"
    with v2.open("rb") as stream:
        snapshot = service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v2",
            stream=stream,
            size=v2.stat().st_size,
        )
    if snapshot.state is not RunState.BLOCKED:
        raise RuntimeError(f"rehearsal {index}: v2 was not blocked")
    v3 = runtime / "demo" / "revisionproof_v3_ready.mp4"
    with v3.open("rb") as stream:
        snapshot = service.upload_and_verify(
            run_id=snapshot.run_id,
            version_label="v3",
            stream=stream,
            size=v3.stat().st_size,
        )
    if snapshot.state is not RunState.READY or not snapshot.proof:
        raise RuntimeError(f"rehearsal {index}: v3 was not ready")
    snapshot = service.approve_for_delivery(snapshot.run_id)
    if not snapshot.delivery_approved:
        raise RuntimeError(f"rehearsal {index}: delivery was not approved")
    return {
        "rehearsal": index,
        "run_id": snapshot.run_id,
        "final_state": snapshot.state,
        "spec_hash": snapshot.proof.spec_hash,
        "events": len(snapshot.events),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    results = [await rehearse(index) for index in range(1, args.runs + 1)]
    print(json.dumps({"status": "PASS", "results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
