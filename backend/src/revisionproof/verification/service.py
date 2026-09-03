from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from revisionproof.contracts import (
    RevisionSpec,
    Verdict,
    VerificationCheck,
    VerificationProof,
)
from revisionproof.media.executor import MediaExecutor
from revisionproof.state_machine import release_verdict
from revisionproof.verification.metrics import (
    apply_punch_in,
    audio_levels_db,
    normalized_similarity,
    read_frame,
    roi_similarity,
)

PATCH_SIMILARITY_THRESHOLD = 0.95
PATCH_WINNER_MARGIN = 0.0005
PATCH_REQUIRED_RATIO = 0.80
CTA_SIMILARITY_THRESHOLD = 0.94
CTA_REQUIRED_RATIO = 0.60
AUDIO_RMS_TOLERANCE_DB = 3.0
AUDIO_PEAK_LIMIT_DBFS = -1.0
CTA_ROI = (840, 570, 340, 90)


class DeterministicVerifier:
    def __init__(self, executor: MediaExecutor) -> None:
        self.executor = executor

    def verify(
        self,
        *,
        source: Path,
        candidate: Path,
        spec: RevisionSpec,
        version_label: str,
    ) -> VerificationProof:
        checks = [
            self._approved_patch(source, candidate, spec),
            self._locked_cta(source, candidate, spec),
            self._locked_audio(source, candidate, spec),
        ]
        verdict, publish_allowed = release_verdict([check.verdict for check in checks])
        return VerificationProof(
            version_label=version_label,
            spec_hash=spec.spec_hash,
            verdict=verdict,
            publish_allowed=publish_allowed,
            checks=checks,
            generated_at=datetime.now(UTC),
        )

    def _approved_patch(
        self, source: Path, candidate: Path, spec: RevisionSpec
    ) -> VerificationCheck:
        manifest = spec.manifest_for("approved_patch")
        time_range = manifest.time_range
        duration = time_range.end_seconds - time_range.start_seconds
        sample_times = [
            time_range.start_seconds + duration * fraction for fraction in (0.1, 0.3, 0.5, 0.7, 0.9)
        ]
        expected_scale = spec.approved_candidate.scale
        competing_scales = [1.0, 1.05 if expected_scale == 1.12 else 1.12]
        expected_scores: list[float] = []
        winner_margins: list[float] = []
        winning_frames = 0
        for second in sample_times:
            source_frame = read_frame(source, second)
            actual = read_frame(candidate, second)
            expected_score = normalized_similarity(
                apply_punch_in(source_frame, expected_scale), actual
            )
            competing_score = max(
                normalized_similarity(apply_punch_in(source_frame, scale), actual)
                for scale in competing_scales
            )
            expected_scores.append(expected_score)
            winner_margins.append(expected_score - competing_score)
            if (
                expected_score >= manifest.threshold["minimum_similarity"]
                and expected_score - competing_score >= manifest.threshold["minimum_winner_margin"]
            ):
                winning_frames += 1
        ratio = winning_frames / len(sample_times)
        average_similarity = sum(expected_scores) / len(expected_scores)
        minimum_winner_margin = min(winner_margins)
        verdict = (
            Verdict.PASS if ratio >= manifest.threshold["minimum_passing_ratio"] else Verdict.FAIL
        )
        return VerificationCheck(
            check_id="approved_patch",
            label="Approved punch-in matches",
            verdict=verdict,
            failure_code=None if verdict is Verdict.PASS else "APPROVED_PATCH_MISMATCH",
            measured={
                "normalized_similarity": round(average_similarity, 4),
                "winning_frames": winning_frames,
                "sampled_frames": len(sample_times),
                "ratio": ratio,
                "minimum_winner_margin_observed": round(minimum_winner_margin, 6),
            },
            threshold=manifest.threshold,
            evidence_time_range=time_range,
        )

    def _locked_cta(self, source: Path, candidate: Path, spec: RevisionSpec) -> VerificationCheck:
        manifest = spec.manifest_for("locked_cta")
        full_video = any(element.kind == "VIDEO_CONTENT" for element in spec.locked_elements)
        duration = manifest.time_range.end_seconds - manifest.time_range.start_seconds
        sample_times = [
            manifest.time_range.start_seconds + duration * fraction
            for fraction in (0.1, 0.3, 0.5, 0.7, 0.9)
        ]
        if full_video:
            sample_times = []
            for index in range(math.ceil(duration * 2)):
                start, end = index * 0.5, min((index + 1) * 0.5, duration)
                # As in Change Map, a sub-50 ms codec tail is not another video sample.
                # Use the partial bin's midpoint, away from the last frame boundary.
                if end - start >= 0.05:
                    sample_times.append(manifest.time_range.start_seconds + (start + end) / 2)
        if manifest.roi is None:
            raise ValueError("locked CTA manifest is missing its ROI")
        scores = []
        patch = spec.approved_candidate
        for second in sample_times:
            expected = read_frame(source, second)
            if (
                full_video
                and patch.time_range.start_seconds <= second < patch.time_range.end_seconds
            ):
                expected = apply_punch_in(expected, patch.scale)
            scores.append(roi_similarity(expected, read_frame(candidate, second), manifest.roi))
        passing = sum(score >= manifest.threshold["minimum_frame_similarity"] for score in scores)
        ratio = passing / len(scores)
        verdict = (
            Verdict.PASS if ratio >= manifest.threshold["minimum_passing_ratio"] else Verdict.FAIL
        )
        return VerificationCheck(
            check_id="locked_cta",
            label="Full video follows the approved edit"
            if full_video
            else "Locked CTA remains visible",
            verdict=verdict,
            failure_code=None
            if verdict is Verdict.PASS
            else "UNEXPECTED_VIDEO_CHANGE"
            if full_video
            else "LOCKED_OVERLAY_MISSING",
            measured={
                "passing_frames": passing,
                "sampled_frames": len(scores),
                "ratio": ratio,
                "roi_x": manifest.roi[0],
                "roi_y": manifest.roi[1],
                "roi_width": manifest.roi[2],
                "roi_height": manifest.roi[3],
            },
            threshold=manifest.threshold,
            evidence_time_range=manifest.time_range,
        )

    def _locked_audio(self, source: Path, candidate: Path, spec: RevisionSpec) -> VerificationCheck:
        manifest = spec.manifest_for("locked_audio")
        duration = manifest.time_range.end_seconds - manifest.time_range.start_seconds
        source_rms, source_peak = audio_levels_db(
            source,
            start_seconds=manifest.time_range.start_seconds,
            duration_seconds=duration,
            executor=self.executor,
        )
        candidate_rms, candidate_peak = audio_levels_db(
            candidate,
            start_seconds=manifest.time_range.start_seconds,
            duration_seconds=duration,
            executor=self.executor,
        )
        delta = abs(candidate_rms - source_rms)
        passed = (
            delta <= manifest.threshold["maximum_rms_delta_db"]
            and candidate_peak <= manifest.threshold["maximum_peak_dbfs"]
        )
        verdict = Verdict.PASS if passed else Verdict.FAIL
        return VerificationCheck(
            check_id="locked_audio",
            label="Locked audio level is unchanged",
            verdict=verdict,
            failure_code=None if passed else "LOCKED_AUDIO_CHANGED",
            measured={
                "source_rms_dbfs": round(source_rms, 2),
                "source_peak_dbfs": round(source_peak, 2),
                "candidate_rms_dbfs": round(candidate_rms, 2),
                "rms_delta_db": round(delta, 2),
                "candidate_peak_dbfs": round(candidate_peak, 2),
            },
            threshold=manifest.threshold,
            evidence_time_range=manifest.time_range,
        )


def mark_proof_not_checked(proof: VerificationProof, failure_code: str) -> None:
    for check in proof.checks:
        check.verdict = Verdict.NOT_CHECKED
        check.failure_code = failure_code
    proof.verdict = Verdict.NOT_CHECKED
    proof.publish_allowed = False
    proof.generated_at = datetime.now(UTC)


def apply_mcp_feature_diff(
    proof: VerificationProof,
    spec: RevisionSpec,
    rows: list[dict[str, Any]],
) -> None:
    values: dict[str, tuple[float, float]] = {}
    for row in rows:
        feature_name = str(row.get("feature_name", ""))
        try:
            baseline_value = float(row["baseline_value"])
            current_value = float(row["current_value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("mcp-clickhouse feature diff contains invalid numbers") from exc
        if not math.isfinite(baseline_value) or not math.isfinite(current_value):
            raise RuntimeError("mcp-clickhouse feature diff contains non-finite numbers")
        if feature_name in values:
            raise RuntimeError(f"mcp-clickhouse feature diff duplicated {feature_name}")
        values[feature_name] = (baseline_value, current_value)

    required = {
        "patch_similarity",
        "patch_passing_ratio",
        "patch_winner_margin",
        "cta_passing_ratio",
        "audio_rms_dbfs",
        "audio_peak_dbfs",
    }
    missing = sorted(required - values.keys())
    if missing:
        raise RuntimeError("mcp-clickhouse feature diff is missing: " + ", ".join(missing))

    checks = {check.check_id: check for check in proof.checks}
    patch = checks["approved_patch"]
    patch_manifest = spec.manifest_for("approved_patch")
    patch_similarity = values["patch_similarity"][1]
    patch_ratio = values["patch_passing_ratio"][1]
    patch_margin = values["patch_winner_margin"][1]
    patch.measured.update(
        {
            "mcp_normalized_similarity": patch_similarity,
            "mcp_passing_ratio": patch_ratio,
            "mcp_winner_margin": patch_margin,
        }
    )
    patch_passed = (
        patch_similarity >= patch_manifest.threshold["minimum_similarity"]
        and patch_ratio >= patch_manifest.threshold["minimum_passing_ratio"]
        and patch_margin >= patch_manifest.threshold["minimum_winner_margin"]
    )
    patch.verdict = Verdict.PASS if patch_passed else Verdict.FAIL
    patch.failure_code = None if patch_passed else "APPROVED_PATCH_MISMATCH"

    cta = checks["locked_cta"]
    cta_manifest = spec.manifest_for("locked_cta")
    cta_ratio = values["cta_passing_ratio"][1]
    cta.measured["mcp_passing_ratio"] = cta_ratio
    cta_passed = cta_ratio >= cta_manifest.threshold["minimum_passing_ratio"]
    cta.verdict = Verdict.PASS if cta_passed else Verdict.FAIL
    cta.failure_code = (
        None
        if cta_passed
        else "UNEXPECTED_VIDEO_CHANGE"
        if any(e.kind == "VIDEO_CONTENT" for e in spec.locked_elements)
        else "LOCKED_OVERLAY_MISSING"
    )

    audio = checks["locked_audio"]
    audio_manifest = spec.manifest_for("locked_audio")
    source_rms, candidate_rms = values["audio_rms_dbfs"]
    _, candidate_peak = values["audio_peak_dbfs"]
    audio_delta = abs(candidate_rms - source_rms)
    audio.measured.update(
        {
            "mcp_source_rms_dbfs": source_rms,
            "mcp_candidate_rms_dbfs": candidate_rms,
            "mcp_rms_delta_db": audio_delta,
            "mcp_candidate_peak_dbfs": candidate_peak,
        }
    )
    audio_passed = (
        audio_delta <= audio_manifest.threshold["maximum_rms_delta_db"]
        and candidate_peak <= audio_manifest.threshold["maximum_peak_dbfs"]
    )
    audio.verdict = Verdict.PASS if audio_passed else Verdict.FAIL
    audio.failure_code = None if audio_passed else "LOCKED_AUDIO_CHANGED"

    proof.verdict, proof.publish_allowed = release_verdict(
        [check.verdict for check in proof.checks]
    )
    proof.generated_at = datetime.now(UTC)
