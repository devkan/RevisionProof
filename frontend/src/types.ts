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
  intelligence_enabled?: boolean
  memory_save_policy?: 'operator_key' | 'read_only' | 'local_rehearsal'
  upload_limits?: { max_bytes: number; max_duration_seconds: number; min_duration_seconds: number }
  logo_limits?: { max_bytes: number; max_dimension: number }
}

export type SearchEngine = 'exact' | 'hnsw' | 'qbit'
export interface ChangeWindow {
  second: number
  sample_count: number
  visual_delta: number
  residual_delta: number
  cta_delta: number
  audio_delta_db: number
  requested: boolean
  status: 'requested' | 'unchanged' | 'review'
}
export interface RevisionChangeMap {
  status: 'ready' | 'unavailable'
  version_label: string
  spec_hash: string
  analysis_id: string
  source: string
  sample_fps: number
  duration_seconds: number
  windows: ChangeWindow[]
  message: string
}
export interface ApprovedEditMatch {
  memory_id: string
  kind: 'zoom' | 'recipe'
  intent: string
  target_phrase: string
  candidate_id: 'A' | 'B' | null
  scale: 1.05 | 1.12 | null
  duration_seconds: number
  edit_plan: EditPlan | null
  similarity: number
  approved_at: string
  spec_hash: string
}

export interface SceneSearchHit {
  segment_id: string
  start_seconds: number
  end_seconds: number
  score: number
  transcript: string
  visual_summary: string
}
export interface SceneSearchResult {
  search_id: string
  asset_id: string
  query: string
  source: 'fixture.scene_search' | 'mcp-clickhouse.run_query'
  segments_indexed: number
  matches: SceneSearchHit[]
  message: string
}
export interface EditMemorySearch {
  status: 'ready' | 'empty' | 'unavailable' | 'disabled'
  requested_engine: SearchEngine
  actual_engine: SearchEngine | 'fixture' | 'unavailable' | 'none'
  source: string
  collection_size: number
  elapsed_ms: number
  precision_bits: number | null
  index_verified: boolean
  matches: ApprovedEditMatch[]
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
  source_kind?: 'demo' | 'upload'
}

export interface ParsedFeedback {
  raw_text: string
  intent: string
  patch_type: 'PUNCH_IN' | 'EDIT_PLAN'
  target_phrase: string
  rationale: string
  interpreter_source: 'fixture.interpreter' | 'google.vertex.gemini' | 'local.range_rules' | 'user.structured'
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
  source: 'fixture.segment_index' | 'mcp-clickhouse.run_query' | 'user.selected_range'
}

export interface ZoomCandidate {
  candidate_id: 'A' | 'B'
  patch_type: 'PUNCH_IN'
  scale: 1.05 | 1.12
  time_range: TimeRange
  preview_url?: string
}

export interface EditOperation {
  kind: 'zoom' | 'text' | 'subtitle' | 'cut' | 'remove_silence' | 'speed' | 'volume' | 'logo'
  start: number
  end: number
  text: string
  position: 'top' | 'center' | 'bottom' | 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right'
  threshold_db: number
  min_silence: number
  detected: boolean
  rate: number
  volume_db: number
  asset_id: string
  asset_sha256: string
}
export interface EditPlan { source_duration: number; operations: EditOperation[] }
export interface EditInterpretation { plan: EditPlan; warnings: string[]; source: string }
export interface LogoAsset {
  asset_id: string
  sha256: string
  preview_url: string
  width: number
  height: number
}
export type TranscriptionLanguage = 'auto' | 'ko' | 'en' | 'mixed'
export interface TranscriptionResult {
  duration: number
  requested_language: TranscriptionLanguage
  detected_languages: Array<'ko' | 'en' | 'other'>
  cues: Array<{ start: number; end: number; text: string; language: 'ko' | 'en' | 'mixed' | 'other' }>
  warnings: string[]
  source: 'google.vertex.gemini'
}
export interface EditCandidate {
  candidate_id: 'A' | 'B'
  patch_type: 'EDIT_PLAN'
  time_range: TimeRange
  preview_url: string
  plan: EditPlan
  reference_sha256: string
}
export type PatchCandidate = ZoomCandidate | EditCandidate

export interface RevisionSpec {
  schema_version: '2.0' | '2.1' | '2.2' | '3.0' | '3.1'
  run_id: string
  asset_id: string
  approved_candidate: PatchCandidate
  evidence: EvidenceAnchor[]
  locked_elements: Array<{
    element_id: string
    kind: 'CTA_OVERLAY' | 'VIDEO_CONTENT' | 'AUDIO'
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
  selected_range?: TimeRange
  mode: ExecutionMode
  state: RunState
  notes: RevisionNote[]
  selected_note_id?: string
  feedback?: ParsedFeedback
  evidence: EvidenceAnchor[]
  candidates: PatchCandidate[]
  edit_plan?: EditPlan
  edit_warnings?: string[]
  spec?: RevisionSpec
  proof?: VerificationProof
  generated_version_url?: string
  change_map?: RevisionChangeMap
  edit_memory?: EditMemorySearch
  memory_saved?: boolean
  delivery_approved: boolean
  retryable: boolean
  events: RunEvent[]
  error?: string
}
