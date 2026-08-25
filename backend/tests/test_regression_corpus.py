import json
from pathlib import Path

import pytest

from revisionproof.assets import DEMO_ASSET_ID
from revisionproof.contracts import ApprovalRequest, CreateRunRequest, Verdict
from revisionproof.service import RevisionProofService


@pytest.mark.asyncio
async def test_twelve_real_video_regressions_have_zero_false_passes(
    service: RevisionProofService, runtime_dir: Path
) -> None:
    manifest_path = Path(__file__).parent / "fixtures" / "regression_manifest.json"
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(cases) == 12
    assert sum(case["expected"] == "FAIL" for case in cases) == 9

    snapshot = await service.create_run(
        CreateRunRequest(asset_id=DEMO_ASSET_ID, feedback="Make the reveal more intentional")
    )
    snapshot = service.generate_previews(snapshot.run_id)
    snapshot = service.approve(snapshot.run_id, ApprovalRequest(candidate_id="B"))
    assert snapshot.spec is not None
    source = service.repository.source_path(snapshot.run_id)

    false_passes = []
    for case in cases:
        proof = service.verifier.verify(
            source=source,
            candidate=runtime_dir / "demo" / case["file"],
            spec=snapshot.spec,
            version_label=case["file"],
        )
        if case["expected"] == "PASS":
            assert proof.verdict is Verdict.PASS, case["file"]
        else:
            if proof.verdict is Verdict.PASS:
                false_passes.append(case["file"])
            failure_codes = {check.failure_code for check in proof.checks}
            assert case["code"] in failure_codes, case["file"]
    assert false_passes == []
