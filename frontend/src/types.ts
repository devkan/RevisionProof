export type ExecutionMode = 'LIVE' | 'FIXTURE' | 'OFFLINE_REHEARSAL' | 'UNAVAILABLE'
export type RunState =
  | 'INDEXED'
  | 'NOTES_PARSED'
  | 'EVIDENCE_ANCHORED'
  | 'PREVIEWS_READY'
  | 'HUMAN_APPROVED'
  | 'VERSION_UPLOADED'
  | 'VERIFYING'
  | 'BLOCKED'
  | 'READY'
  | 'FAILED'

export type Verdict = 'PASS' | 'FAIL' | 'ERROR' | 'NOT_CHECKED'
export type SafetyClassification = 'AUTO_PREVIEWABLE' | 'NEEDS_CLARIFICATION' | 'MANUAL_CREATIVE'

export interface RuntimeStatus {
  mode: ExecutionMode
  mutable: boolean
  live_ready: boolean
  missing_settings: string[]
  message: string
}

export interface TimeRange {
  start_seconds: number
  end_seconds: number
}

export interface DemoAsset {
  asset_id: string
  title: string
  source_url: string
  duration_seconds: number
  width: number
  height: number
  codec: string
}

export interface ParsedFeedback {
  raw_text: string
  intent: string
  patch_type: 'PUNCH_IN'
  target_phrase: string
  rationale: string
  interpreter_source: 'fixture.interpreter' | 'google.vertex.gemini'
}

export interface RevisionNote {
  note_id: string
  raw_text: string
  intent: string
  classification: SafetyClassification
  confidence: number
  target_phrase?: string
  rationale: string
  clarification_question?: string
}

export interface EvidenceAnchor {
  segment_id: string
  time_range: TimeRange
  score: number
  transcript: string
  visual_summary: string
  source: 'fixture.segment_index' | 'mcp-clickhouse.run_query'
}

export interface PatchCandidate {
  candidate_id: 'A' | 'B'
  patch_type: 'PUNCH_IN'
  scale: 1.05 | 1.12
  time_range: TimeRange
  preview_url?: string
}

export interface RevisionSpec {
  schema_version: '2.0'
  run_id: string
  asset_id: string
  approved_candidate: PatchCandidate
  evidence: EvidenceAnchor[]
  locked_elements: Array<{
    element_id: string
    kind: 'CTA_OVERLAY' | 'AUDIO'
    time_range: TimeRange
    description: string
  }>
  verification_manifest: Array<{
    check_id: 'approved_patch' | 'locked_cta' | 'locked_audio'
    required: true
    time_range: TimeRange
    roi?: [number, number, number, number]
    threshold: Record<string, number>
  }>
  approved_at: string
  spec_hash: string
}

export interface VerificationCheck {
  check_id: 'approved_patch' | 'locked_cta' | 'locked_audio'
  label: string
  verdict: Verdict
  failure_code?: string
  measured: Record<string, string | number>
  threshold: Record<string, string | number>
  evidence_time_range: TimeRange
  evidence_urls: string[]
}

export interface VerificationProof {
  version_label: string
  spec_hash: string
  verdict: Verdict
  publish_allowed: boolean
  checks: VerificationCheck[]
  generated_at: string
}

export interface RunEvent {
  sequence: number
  state: RunState
  message: string
  occurred_at: string
}

export interface RunSnapshot {
  run_id: string
  asset: DemoAsset
  mode: ExecutionMode
  state: RunState
  notes: RevisionNote[]
  selected_note_id?: string
  feedback?: ParsedFeedback
  evidence: EvidenceAnchor[]
  candidates: PatchCandidate[]
  spec?: RevisionSpec
  proof?: VerificationProof
  generated_version_url?: string
  delivery_approved: boolean
  retryable: boolean
  events: RunEvent[]
  error?: string
}
