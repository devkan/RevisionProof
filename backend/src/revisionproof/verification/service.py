from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from revisionproof.contracts import (
    RevisionSpec,
    TimeRange,
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
            self._locked_cta(source, candidate),
            self._locked_audio(source, candidate),
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
        time_range = spec.approved_candidate.time_range
        duration = time_range.end_seconds - time_range.start_seconds
        sample_times = [
            time_range.start_seconds + duration * fraction for fraction in (0.1, 0.3, 0.5, 0.7, 0.9)
        ]
        expected_scale = spec.approved_candidate.scale
        competing_scales = [1.0, 1.05 if expected_scale == 1.12 else 1.12]
        expected_scores: list[float] = []
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
            if (
                expected_score >= PATCH_SIMILARITY_THRESHOLD
                and expected_score - competing_score >= PATCH_WINNER_MARGIN
            ):
                winning_frames += 1
        ratio = winning_frames / len(sample_times)
        average_similarity = sum(expected_scores) / len(expected_scores)
        verdict = Verdict.PASS if ratio >= PATCH_REQUIRED_RATIO else Verdict.FAIL
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
            },
            threshold={
                "minimum_similarity": PATCH_SIMILARITY_THRESHOLD,
                "minimum_winner_margin": PATCH_WINNER_MARGIN,
                "minimum_passing_ratio": PATCH_REQUIRED_RATIO,
            },
            evidence_time_range=time_range,
        )

    def _locked_cta(self, source: Path, candidate: Path) -> VerificationCheck:
        sample_times = [24.0, 25.0, 26.0, 27.0, 28.0]
        scores = [
            roi_similarity(read_frame(source, second), read_frame(candidate, second), CTA_ROI)
            for second in sample_times
        ]
        passing = sum(score >= CTA_SIMILARITY_THRESHOLD for score in scores)
        ratio = passing / len(scores)
        verdict = Verdict.PASS if ratio >= CTA_REQUIRED_RATIO else Verdict.FAIL
        return VerificationCheck(
            check_id="locked_cta",
            label="Locked CTA remains visible",
            verdict=verdict,
            failure_code=None if verdict is Verdict.PASS else "LOCKED_OVERLAY_MISSING",
            measured={"passing_frames": passing, "sampled_frames": len(scores), "ratio": ratio},
            threshold={
                "minimum_frame_similarity": CTA_SIMILARITY_THRESHOLD,
                "minimum_passing_ratio": CTA_REQUIRED_RATIO,
            },
            evidence_time_range=TimeRange(start_seconds=24, end_seconds=29),
        )

    def _locked_audio(self, source: Path, candidate: Path) -> VerificationCheck:
        source_rms, _ = audio_levels_db(
            source, start_seconds=0, duration_seconds=30, executor=self.executor
        )
        candidate_rms, candidate_peak = audio_levels_db(
            candidate, start_seconds=0, duration_seconds=30, executor=self.executor
        )
        delta = abs(candidate_rms - source_rms)
        passed = delta <= AUDIO_RMS_TOLERANCE_DB and candidate_peak <= AUDIO_PEAK_LIMIT_DBFS
        verdict = Verdict.PASS if passed else Verdict.FAIL
        return VerificationCheck(
            check_id="locked_audio",
            label="Locked audio level is unchanged",
            verdict=verdict,
            failure_code=None if passed else "LOCKED_AUDIO_CHANGED",
            measured={
                "source_rms_dbfs": round(source_rms, 2),
                "candidate_rms_dbfs": round(candidate_rms, 2),
                "rms_delta_db": round(delta, 2),
                "candidate_peak_dbfs": round(candidate_peak, 2),
            },
            threshold={
                "maximum_rms_delta_db": AUDIO_RMS_TOLERANCE_DB,
                "maximum_peak_dbfs": AUDIO_PEAK_LIMIT_DBFS,
            },
            evidence_time_range=TimeRange(start_seconds=0, end_seconds=30),
        )
