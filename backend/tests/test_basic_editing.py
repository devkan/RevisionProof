import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from revisionproof.api import get_service, router
from revisionproof.contracts import ApprovalRequest, ExecutionMode, RevisionSpec, TimeRange
from revisionproof.editing.interpret import EditDraftOutput, interpret_local
from revisionproof.editing.models import EditOperation, EditPlan, InterpretEditRequest
from revisionproof.editing.render import render_plan, resolve_plan
from revisionproof.editing.verify import file_hash
from revisionproof.media.executor import MediaExecutor
from revisionproof.media.probe import probe_media
from revisionproof.repository import InMemoryRunRepository
from revisionproof.service import RevisionProofService
from revisionproof.settings import Settings
from revisionproof.verification.metrics import apply_punch_in, normalized_similarity, read_frame


def test_live_edit_draft_schema_converts_with_installed_vertex_sdk():
    from google.genai import _transformers

    # Exercise the real SDK conversion that happens before the Vertex request.
    schema = _transformers.t_schema(SimpleNamespace(vertexai=True), EditDraftOutput)
    operation_schema = schema.properties["operations"].items
    assert operation_schema.properties["end"].type == "NUMBER"
    assert set(operation_schema.properties) == {"kind", "start", "end", "text", "position"}
    assert set(operation_schema.required) == set(operation_schema.properties)
    wire = schema.model_dump_json(exclude_none=True)
    for unsupported in ("additional_properties", "default", "maximum", "max_items"):
        assert f'"{unsupported}"' not in wire
    silence = EditDraftOutput.model_validate(
        {
            "operations": [
                {"kind": "remove_silence", "start": 0, "end": 10, "text": "", "position": "bottom"}
            ]
        }
    ).operations[0]
    assert (silence.threshold_db, silence.min_silence, silence.detected) == (-40, 0.7, False)
    # Simplifying the provider schema must never weaken runtime validation.
    for bad in (
        {"kind": "zoom", "start": 0, "end": 0},
        {"kind": "zoom", "start": 0, "end": 61},
        {"kind": "text", "start": 0, "end": 5, "text": "x" * 161},
        {"kind": "zoom", "start": 0, "end": 5, "unexpected": True},
    ):
        with pytest.raises(ValidationError):
            EditDraftOutput.model_validate({"operations": [bad]})
    with pytest.raises(ValidationError):
        EditDraftOutput.model_validate(
            {"operations": [{"kind": "zoom", "start": 0, "end": 5}] * 25}
        )


@pytest.mark.parametrize("index", [0, 1, 2])
def test_pinned_pre_expansion_specs_keep_their_exact_hash_and_json(index):
    # Generated using the contracts at 2591cd8, before EDIT_PLAN existed.
    payload = json.loads((Path(__file__).parent / "fixtures/legacy_specs_2x.json").read_text())[
        index
    ]
    restored = RevisionSpec.model_validate(payload)
    assert restored.model_dump(mode="json") == payload


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    folder = tmp_path_factory.mktemp("basic-edits")
    source = folder / "source.mp4"
    executor = MediaExecutor(90)
    executor.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x720:rate=30:duration=10",
            "-f",
            "lavfi",
            "-i",
            "aevalsrc='if(between(t,3,5),0,0.2*sin(2*PI*440*t))|if(between(t,3,5),0,-0.2*sin(2*PI*440*t))':s=48000:d=10",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "25",
            "-c:a",
            "aac",
            "-ac",
            "2",
            "-shortest",
            str(source),
        ],
        expected_output=source,
    )
    return source, executor


def test_korean_compound_request_preserves_literal_caption():
    result = interpret_local(
        InterpretEditRequest(
            text="4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시",
            duration=10,
        )
    )
    assert [op.kind for op in result.plan.operations] == ["zoom", "text"]
    assert result.plan.operations[1].text == "AI, made practical."
    assert result.plan.operations[1].position == "bottom"
    assert all((op.start, op.end) == (4, 10) for op in result.plan.operations)


def test_cut_union_source_mapping_and_conflicts():
    plan = EditPlan(
        source_duration=10,
        operations=(
            EditOperation(kind="cut", start=2, end=4),
            EditOperation(kind="cut", start=3, end=5),
            EditOperation(kind="cut", start=8, end=10),
        ),
    )
    assert plan.output_duration == 5
    assert plan.source_time(2) == 5
    assert plan.source_time(4.5) == 7.5
    with pytest.raises(ValidationError, match="same position"):
        EditPlan(
            source_duration=10,
            operations=(
                EditOperation(kind="text", start=1, end=3, text="Title"),
                EditOperation(kind="subtitle", start=2, end=4, text="Clash"),
            ),
        )
    with pytest.raises(ValidationError, match="entirely"):
        EditPlan(
            source_duration=10,
            operations=(
                EditOperation(kind="cut", start=1, end=5),
                EditOperation(kind="zoom", start=2, end=4),
            ),
        )


@pytest.mark.parametrize(
    "caption",
    [
        "Let's go!",
        "Zoom into your future",
        "Silence is golden",
        "A cut above the rest",
        "AI at 2–4s",
    ],
)
def test_caption_words_are_not_commands(caption):
    result = interpret_local(
        InterpretEditRequest(text=f'4–10초에 "{caption}" 문구 넣기', duration=10)
    )
    assert len(result.plan.operations) == 1
    assert result.plan.operations[0].kind == "text"
    assert result.plan.operations[0].text == caption
    assert not result.warnings


@pytest.mark.parametrize(
    "text", ["2–4초에 인물을 제거해줘", "2–4초에 로고 제거", "2–4초를 삭제하지 말고 확대"]
)
def test_unsupported_deletion_is_not_a_cut(text):
    result = interpret_local(InterpretEditRequest(text=text, duration=10))
    assert not result.plan.operations and result.warnings


def test_many_silences_are_bounded_and_proposals_remain_optional(tmp_path, monkeypatch):
    audio = np.zeros((60 * 16000, 2), dtype=np.float32)
    for second in range(60):
        audio[second * 16000 + 12800 : (second + 1) * 16000, :] = 0.1
    monkeypatch.setattr("revisionproof.editing.render.decode_channels", lambda *args: audio)
    plan = EditPlan(
        source_duration=60,
        operations=(
            EditOperation(kind="text", start=0.2, end=0.5, text="Keep this title"),
            EditOperation(kind="remove_silence", start=0, end=60),
        ),
    )
    resolved, warnings = resolve_plan(plan, 60, tmp_path / "source.mp4", MediaExecutor(90))
    assert len(resolved.operations) == 24
    assert resolved.operations[0] == plan.operations[0]
    assert any("additional" in message for message in warnings)
    conflict = EditPlan(
        source_duration=10,
        operations=(
            EditOperation(kind="text", start=2, end=3, text="Keep me"),
            EditOperation(kind="cut", start=1, end=4, detected=True),
        ),
    )
    with pytest.raises(ValueError, match="entirely"):
        conflict.validate_selection()


def test_silence_uses_all_channels_without_phase_cancellation(media):
    source, executor = media
    resolved, warnings = resolve_plan(
        EditPlan(
            source_duration=10, operations=(EditOperation(kind="remove_silence", start=0, end=10),)
        ),
        10,
        source,
        executor,
    )
    assert len(resolved.operations) == 1
    cut = resolved.operations[0]
    assert cut.detected and 3.1 <= cut.start <= 3.3 and 4.7 <= cut.end <= 4.9
    assert "Select" in warnings[0]


def test_render_timed_korean_text_and_cut_scene_mapping(media, tmp_path):
    source, executor = media
    plan = EditPlan(
        source_duration=10,
        operations=(
            EditOperation(kind="cut", start=2, end=4),
            EditOperation(kind="subtitle", start=4, end=6, text="AI, made practical. 실용적인 AI"),
            EditOperation(kind="subtitle", start=6, end=8, text="KANAPP · 두 번째 문구"),
            EditOperation(kind="zoom", start=8, end=10),
        ),
    )
    target = render_plan(source, tmp_path / "edited.mp4", plan, "A", executor)
    assert abs(probe_media(target, executor).duration_seconds - 8) < 0.1
    assert normalized_similarity(read_frame(source, 1), read_frame(target, 1)) > 0.97
    # The cut joins to original t=4: the uncaptioned upper scene is correctly mapped.
    assert (
        normalized_similarity(read_frame(source, 4.5)[:450], read_frame(target, 2.5)[:450]) > 0.97
    )
    lower_original = read_frame(source, 4.5)[550:670]
    lower_caption = read_frame(target, 2.5)[550:670]
    assert np.mean(np.abs(lower_original.astype(float) - lower_caption)) > 8
    original = read_frame(source, 8.5)
    zoomed = read_frame(target, 6.5)
    assert normalized_similarity(apply_punch_in(original, 1.05), zoomed) > 0.98
    assert normalized_similarity(original, zoomed) < 0.97


@pytest.mark.asyncio
async def test_plan_workflow_verifies_export_and_rejects_changed_preview(media, tmp_path):
    source, _ = media
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=tmp_path, intelligence_enabled=True),
        InMemoryRunRepository(),
    )
    plan = EditPlan(
        source_duration=10,
        operations=(
            EditOperation(kind="text", start=4, end=4.2, text="AI, made practical."),
            EditOperation(kind="cut", start=2, end=3),
        ),
    )
    with source.open("rb") as stream:
        run = await service.create_uploaded_run(
            stream=stream,
            size=source.stat().st_size,
            filename="test.mp4",
            feedback="4–4.2초 하단에 문구 삽입, 2–3초 삭제",
            selected_range=TimeRange(start_seconds=0, end_seconds=6),
            content_sha256=file_hash(source),
            idempotency_key="basic-upload",
            edit_plan=plan,
        )
    assert run.state == "EVIDENCE_ANCHORED", run.error
    service.generate_previews(run.run_id)
    service.approve(run.run_id, ApprovalRequest(candidate_id="A"))
    assert run.spec.schema_version == "3.0"
    service.render_approved_version(run.run_id)
    assert run.state == "READY", run.proof
    assert run.change_map.status == "ready" and not any(
        w.status == "review" for w in run.change_map.windows
    )
    service.approve_for_delivery(run.run_id)
    assert run.delivery_approved
    with pytest.raises(ValueError, match="Multi-edit"):
        service.save_memory(run.run_id)
    altered = tmp_path / "omitted-caption.mp4"
    render_plan(
        service.repository.source_path(run.run_id),
        altered,
        EditPlan(source_duration=10, operations=(EditOperation(kind="cut", start=2, end=3),)),
        "A",
        service.executor,
    )
    proof = service.verifier.verify(
        source=service.repository.source_path(run.run_id),
        candidate=altered,
        spec=run.spec,
        version_label="omitted",
    )
    assert not proof.publish_allowed and proof.checks[0].failure_code == "APPROVED_EXPORT_CHANGED"
    payload = run.spec.model_dump(mode="json")
    payload["approved_candidate"]["plan"]["operations"][0]["text"] = "changed"
    with pytest.raises(ValidationError, match="hash"):
        RevisionSpec.model_validate(payload)


def test_api_short_korean_request_upload_and_explicit_silence_selection(media, tmp_path):
    source, _ = media
    service = RevisionProofService(
        Settings(mode=ExecutionMode.FIXTURE, runtime_dir=tmp_path), InMemoryRunRepository()
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_service] = lambda: service
    with TestClient(app) as client:
        response = client.post(
            "/api/edit-plans/interpret",
            json={
                "text": "무음 제거",
                "duration": 10,
                "start": 0,
                "end": 10,
            },
        )
        assert response.status_code == 200, response.text
        plan = response.json()["plan"]
        with source.open("rb") as stream:
            response = client.post(
                "/api/runs/upload",
                files={"file": ("test.mp4", stream, "video/mp4")},
                data={
                    "feedback": "무음 제거",
                    "start_seconds": "0",
                    "end_seconds": "6",
                    "edit_plan": json.dumps(plan),
                },
                headers={"Idempotency-Key": "short-korean", "X-Content-SHA256": file_hash(source)},
            )
        assert response.status_code == 201, response.text
        run = response.json()
        assert run["state"] == "EVIDENCE_ANCHORED", run
        assert service.repository.get(run["run_id"]).source_feedback == "무음 제거"
        assert len(run["edit_plan"]["operations"]) == 1
        response = client.post(f"/api/runs/{run['run_id']}/previews", json={"note_id": "edit_plan"})
        assert response.status_code == 409 and "Select" in response.json()["detail"]
        response = client.post(
            f"/api/runs/{run['run_id']}/previews",
            json={"note_id": "edit_plan", "edit_plan": run["edit_plan"]},
        )
        assert response.status_code == 200, response.text
        assert len(response.json()["candidates"]) == 1
