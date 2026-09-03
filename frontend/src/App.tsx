import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Clock3,
  Download,
  ExternalLink,
  Film,
  Fingerprint,
  Info,
  LockKeyhole,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Upload,
  WandSparkles,
  XCircle,
  ZoomIn,
} from 'lucide-react'
import { api } from './api'
import { DEFAULT_FEEDBACK } from './demoFeedback'
import { feedbackValidationMessage } from './feedbackValidation'
import { isTerminalRunState } from './runStream'
import { VideoLightbox, type VideoLightboxContent } from './VideoLightbox'
import { ChangeMap, EditMemory, SaveApprovedMemory } from './RevisionIntelligence'
import { SourceUpload, type UploadedSource } from './SourceUpload'
import { fileValidation, limitsFor, rangeValidation } from './uploadValidation'
import type {
  DemoAsset,
  PatchCandidate,
  RevisionNote,
  RunSnapshot,
  RuntimeStatus,
  SafetyClassification,
  Verdict,
  TimeRange,
} from './types'

type ProcessingPhase =
  | 'interpreting'
  | 'rendering-previews'
  | 'approving'
  | 'building-video'
  | 'verifying-upload'
  | 'delivery-approval'
  | 'retrying'
  | 'uploading-source'

const PROCESSING_COPY: Record<ProcessingPhase, { title: string; detail: string }> = {
  'uploading-source': { title: 'Preparing your video…', detail: 'Uploading, checking the file, and preparing your selected section for editing.' },
  interpreting: {
    title: 'Reviewing every client request…',
    detail: 'Gemini is separating safe automatic edits from requests that need details or an editor.',
  },
  'rendering-previews': {
    title: 'Creating two preview options…',
    detail: 'Creating a subtle and a stronger center punch-in of the selected scene.',
  },
  approving: {
    title: 'Freezing your approved option…',
    detail: 'Saving your selected edit and the video and audio checks it must pass.',
  },
  'building-video': {
    title: 'Building and checking the full video…',
    detail: 'Applying the selected edit, checking locked elements, and mapping changes across the video.',
  },
  'verifying-upload': {
    title: 'Checking the external edit…',
    detail: 'RevisionProof is comparing the uploaded full MP4 with the frozen edit and locked elements.',
  },
  'delivery-approval': {
    title: 'Recording final delivery approval…',
    detail: 'The verified result is being marked as approved for delivery.',
  },
  retrying: {
    title: 'Retrying the preserved feedback…',
    detail: 'Your original note is safe. RevisionProof is reconnecting to the live interpretation path.',
  },
}

const CLASSIFICATION_CONTENT: Record<
  SafetyClassification,
  { label: string; helper: string }
> = {
  AUTO_PREVIEWABLE: {
    label: 'Ready to automate',
    helper: 'Precise enough to preview and apply safely.',
  },
  NEEDS_CLARIFICATION: {
    label: 'Needs details',
    helper: 'RevisionProof will not guess what the client meant.',
  },
  MANUAL_CREATIVE: {
    label: 'Needs an editor',
    helper: 'Requires new creative material or a subjective choice.',
  },
}

function formatTime(seconds: number) {
  const minute = Math.floor(seconds / 60)
  const second = Math.floor(seconds % 60)
  return `${minute}:${second.toString().padStart(2, '0')}`
}

function VerdictPill({ verdict }: { verdict: Verdict }) {
  const Icon = verdict === 'PASS' ? CheckCircle2 : verdict === 'FAIL' ? XCircle : ShieldAlert
  return (
    <span className={`verdict verdict-${verdict.toLowerCase()}`}>
      <Icon size={16} /> {verdict.replace('_', ' ')}
    </span>
  )
}

function ProcessingBanner({ phase }: { phase: ProcessingPhase }) {
  const copy = PROCESSING_COPY[phase]
  return (
    <section className="processing-banner" role="status" aria-live="polite" aria-busy="true">
      <span className="spinner" aria-hidden="true" />
      <div>
        <strong>{copy.title}</strong>
        <p>{copy.detail}</p>
      </div>
    </section>
  )
}

function RequestRow({
  note,
  selected,
  executable,
  disabled,
  onSelect,
}: {
  note: RevisionNote
  selected: boolean
  executable: boolean
  disabled: boolean
  onSelect: () => void
}) {
  const content =
    note.classification === 'AUTO_PREVIEWABLE' && !executable
      ? {
          label: 'Ready in another proof',
          helper: 'This proof already grounds one deterministic edit. Start a new proof for this request.',
        }
      : CLASSIFICATION_CONTENT[note.classification]
  const Icon = executable
    ? CheckCircle2
    : note.classification === 'NEEDS_CLARIFICATION'
      ? AlertTriangle
      : Info

  return (
    <article className={`request-row request-${note.classification.toLowerCase()} ${selected ? 'request-selected' : ''}`}>
      <label className="request-select">
        <input
          type="checkbox"
          checked={selected}
          disabled={!executable || disabled}
          onChange={onSelect}
          aria-label={`${selected ? 'Deselect' : 'Select'} request: ${note.raw_text}`}
        />
      </label>
      <div className="request-body">
        <div className="request-heading">
          <span className={`request-status status-${note.classification.toLowerCase()}`}>
            <Icon size={16} /> {content.label}
          </span>
          <span className="confidence">{Math.round(note.confidence * 100)}% confidence</span>
        </div>
        <h3>{note.raw_text}</h3>
        <p>{note.intent}</p>
        <small>{content.helper}</small>
        {note.clarification_question && (
          <div className="clarification-callout">
            <strong>Ask the client:</strong> {note.clarification_question}
          </div>
        )}
      </div>
    </article>
  )
}

function CandidateCard({
  candidate,
  approved,
  onChoose,
  onViewLarge,
  busy,
}: {
  candidate: PatchCandidate
  approved: boolean
  onChoose: () => void
  onViewLarge: () => void
  busy: boolean
}) {
  const strength = candidate.candidate_id === 'A' ? 'Subtle' : 'Stronger'
  return (
    <article className={`candidate-card ${approved ? 'candidate-approved' : ''}`}>
      <div className="candidate-heading">
        <span className="candidate-letter">{candidate.candidate_id}</span>
        <div>
          <h3>{strength} center punch-in</h3>
          <p>{candidate.scale.toFixed(2)}× · {formatTime(candidate.time_range.start_seconds)}–{formatTime(candidate.time_range.end_seconds)}</p>
        </div>
        {approved && <span className="approved-label"><Check size={15} /> Selected</span>}
      </div>
      {candidate.preview_url && (
        <video src={candidate.preview_url} controls muted playsInline preload="metadata" />
      )}
      <div className="candidate-actions">
        {candidate.preview_url && (
          <button className="secondary-button" type="button" onClick={onViewLarge}>
            <ZoomIn size={17} /> View larger
          </button>
        )}
        {!approved && (
          <button className="primary-button candidate-choice" onClick={onChoose} disabled={busy}>
            <WandSparkles size={17} /> Choose {candidate.candidate_id} and build full video
          </button>
        )}
      </div>
    </article>
  )
}

export default function App() {
  const [assets, setAssets] = useState<DemoAsset[]>([])
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null)
  const [run, setRun] = useState<RunSnapshot | null>(null)
  const [feedback, setFeedback] = useState(DEFAULT_FEEDBACK)
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [processing, setProcessing] = useState<ProcessingPhase | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [videoPreview, setVideoPreview] = useState<VideoLightboxContent | null>(null)
  const [uploadedSource, setUploadedSource] = useState<UploadedSource | null>(null)
  const [selectedRange, setSelectedRange] = useState<TimeRange>({ start_seconds: 0, end_seconds: 6 })
  const [uploadProgress, setUploadProgress] = useState(0)
  const sourcePlayer = useRef<HTMLVideoElement>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const runId = run?.run_id
  const busy = processing !== null
  const feedbackError = run ? null : feedbackValidationMessage(feedback)
  const rangeError = uploadedSource && !run ? rangeValidation(selectedRange, uploadedSource.asset.duration_seconds) : null
  useEffect(() => () => { if (uploadedSource) URL.revokeObjectURL(uploadedSource.asset.source_url) }, [uploadedSource])

  useEffect(() => {
    Promise.all([api.assets(), api.runtime()])
      .then(([nextAssets, nextRuntime]) => {
        setAssets(nextAssets)
        setRuntime(nextRuntime)
      })
      .catch((reason: Error) => setError(reason.message))
  }, [])

  useEffect(() => {
    if (!runId) return
    const stream = new EventSource(`/api/runs/${runId}/events`)
    stream.addEventListener('run_state', (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as RunSnapshot['events'][number]
      setRun((current) => {
        if (!current || current.events.some((item) => item.sequence === payload.sequence)) return current
        return { ...current, state: payload.state, events: [...current.events, payload] }
      })
      if (isTerminalRunState(payload.state)) stream.close()
    })
    stream.onerror = () => stream.close()
    return () => stream.close()
  }, [runId])

  const activeAsset = run?.asset ?? uploadedSource?.asset ?? assets[0]
  const executableNotes = useMemo(
    () =>
      run?.notes.filter(
        (note) => note.classification === 'AUTO_PREVIEWABLE' && run.feedback?.raw_text === note.raw_text,
      ) ?? [],
    [run],
  )
  const unsupportedCount = useMemo(
    () => run?.notes.filter((note) => note.classification !== 'AUTO_PREVIEWABLE').length ?? 0,
    [run?.notes],
  )
  const currentStep = !run ? 1 : !run.candidates.length ? 2 : !run.spec ? 3 : 4

  async function action(phase: ProcessingPhase, work: () => Promise<RunSnapshot>) {
    setProcessing(phase)
    setError(null)
    try {
      const next = await work()
      setRun(next)
      return next
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unexpected request failure')
      return null
    } finally {
      setProcessing(null)
    }
  }

  function start() {
    if (!activeAsset || !runtime?.mutable) return
    setSelectedNoteId(null)
    if (uploadedSource) {
      const problem = fileValidation(uploadedSource.file, limitsFor(runtime)) ?? rangeError
      if (problem) { setError(problem); return }
      setUploadProgress(0)
      void action('uploading-source', () => api.uploadSource(uploadedSource.file, feedback, selectedRange, setUploadProgress))
    } else void action('interpreting', () => api.createRun(activeAsset.asset_id, feedback))
  }

  function renderPreviews() {
    if (!run || !selectedNoteId) return
    void action('rendering-previews', () => api.previews(run.run_id, selectedNoteId))
  }

  async function chooseAndBuild(candidateId: 'A' | 'B') {
    if (!run) return
    setError(null)
    setProcessing('approving')
    try {
      const approved = await api.approve(run.run_id, candidateId)
      setRun(approved)
      setProcessing('building-video')
      setRun(await api.renderApprovedVersion(run.run_id))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Automatic video build failed')
    } finally {
      setProcessing(null)
    }
  }

  function retryAutomaticBuild() {
    if (!run) return
    void action('building-video', () => api.renderApprovedVersion(run.run_id))
  }

  function uploadManual(file?: File) {
    if (!run || !file) return
    const problem = fileValidation(file, limitsFor(runtime))
    if (problem) { setError(problem); return }
    void action('verifying-upload', () =>
      api.uploadVersion(run.run_id, `external-${Date.now()}`, file),
    )
  }

  function resetProof() {
    if (busy) return
    setRun(null)
    setSelectedNoteId(null)
    setError(null)
    setFeedback(uploadedSource ? 'Apply a center punch-in to the selected section.' : DEFAULT_FEEDBACK)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function editRequest() {
    if (busy) return
    setRun(null)
    setSelectedNoteId(null)
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RevisionProof home">
          <span className="brand-mark"><Fingerprint size={22} /></span>
          <span>Revision<span>Proof</span></span>
        </a>
        <div className="header-meta">
          <span className={`mode-badge mode-${(run?.mode ?? runtime?.mode ?? 'UNAVAILABLE').toLowerCase()}`}>
            <CircleDot size={13} /> {run?.mode ?? runtime?.mode ?? 'CHECKING'}
          </span>
          <button className="new-proof-button" onClick={resetProof} disabled={busy || !run}>
            <RefreshCw size={16} /> New proof
          </button>
        </div>
      </header>

      <main id="top">
        <section className="workspace-intro">
          <div>
            <span className="eyebrow">VIDEO REVISION WORKSPACE</span>
            <h1>Turn client notes into a verified video.</h1>
            <p>Review what can be automated, choose an A/B edit, then get the full checked MP4.</p>
          </div>
          <ol className="step-rail" aria-label="Revision workflow progress">
            {['Source & notes', 'Review requests', 'Compare A/B', 'Build & verify'].map((label, index) => {
              const step = index + 1
              const state = step < currentStep ? 'done' : step === currentStep ? 'active' : 'waiting'
              return (
                <li className={`step-${state}`} key={label}>
                  <span>{state === 'done' ? <Check size={16} /> : step}</span>
                  <strong>{label}</strong>
                </li>
              )
            })}
          </ol>
        </section>

        {processing && <ProcessingBanner phase={processing} />}
        {error && (
          <div className="error-banner" role="alert">
            <ShieldAlert size={22} />
            <div><strong>RevisionProof could not finish that step.</strong><p>{error}</p></div>
          </div>
        )}
        {run?.state === 'FAILED' && run.retryable && !processing && (
          <div className="recovery-banner">
            <div><strong>Your original feedback is preserved.</strong><p>{run.error ?? 'The live request failed closed.'}</p></div>
            <button className="secondary-button" onClick={editRequest}>Edit request</button>
            <button className="secondary-button" onClick={() => void action('retrying', () => api.retryRun(run.run_id))}>
              Retry review
            </button>
          </div>
        )}
        {runtime && runtime.mode !== 'LIVE' && (
          <div className="runtime-banner">
            <CircleDot size={18} />
            <span><strong>{runtime.mode}</strong> · {runtime.message}</span>
          </div>
        )}

        <section className="workspace-grid">
          <div className="primary-column">
            <section className="workspace-section source-section">
              <div className="section-heading">
                <div><span className="step-number">01</span><div><h2>Source video and client notes</h2><p>Start with the exact video and the client’s original wording.</p></div></div>
                <span className={`section-state ${run && run.state !== 'FAILED' ? 'state-complete' : ''}`}>{run?.state === 'FAILED' ? 'Review interrupted' : run ? 'Reviewed' : 'Ready'}</span>
              </div>
              {!run && <SourceUpload runtime={runtime} selected={uploadedSource} disabled={busy || !runtime?.mutable} onSelect={(source) => {
                setUploadedSource(source); setError(null)
                setSelectedRange({ start_seconds: 0, end_seconds: source ? Math.min(6, source.asset.duration_seconds) : 6 })
                setFeedback(source ? 'Apply a center punch-in to the selected section.' : DEFAULT_FEEDBACK)
              }} />}
              {processing === 'uploading-source' && <div className="upload-progress" role="status"><progress value={uploadProgress} max={100} /><span>{uploadProgress < 100 ? `Uploading ${uploadProgress}%` : 'Upload complete. Preparing video and reviewing your request…'}</span></div>}
              {run?.asset.source_kind === 'upload' && <p className="input-help">Your video · prepared at 1280×720 with aspect ratio preserved. Selected section: {run.selected_range?.start_seconds.toFixed(1)}–{run.selected_range?.end_seconds.toFixed(1)}s.</p>}
              <div className="source-layout">
                {activeAsset && (
                  <div className="source-video-card">
                    <video ref={sourcePlayer} src={activeAsset.source_url} controls muted playsInline preload="metadata" />
                    <div className="source-video-meta">
                      <div><strong>{activeAsset.title}</strong><span>{activeAsset.width}×{activeAsset.height} · {activeAsset.duration_seconds}s · {activeAsset.codec}</span></div>
                      <button
                        className="secondary-button"
                        type="button"
                        aria-label="View original video larger"
                        onClick={() => setVideoPreview({
                          src: activeAsset.source_url,
                          title: 'Original video',
                          detail: `${activeAsset.title} · ${activeAsset.width}×${activeAsset.height}`,
                        })}
                      >
                        <ZoomIn size={17} /> View larger
                      </button>
                    </div>
                  </div>
                )}
                <div className="feedback-field">
                  <label htmlFor="feedback">Client feedback</label>
                  <textarea
                    id="feedback"
                    value={feedback}
                    onChange={(event) => setFeedback(event.target.value)}
                    disabled={Boolean(run) || busy}
                    aria-describedby={feedbackError ? 'feedback-help' : 'feedback-guidance'}
                    aria-invalid={Boolean(feedbackError)}
                  />
                  <p className={`input-help ${feedbackError ? 'input-help-error' : ''}`} id={feedbackError ? 'feedback-help' : 'feedback-guidance'}>
                    {feedbackError ?? 'Supported now: center punch-in only. Text, subtitles and logos must be added in a video editor. Use one request per line.'}
                  </p>
                  {uploadedSource && !run && <fieldset className="edit-range" disabled={busy}>
                    <legend>Choose the section to edit</legend>
                    <p className="input-help">Watch your video, then select 4–8 seconds for a center punch-in. Other edits remain for an editor.</p>
                    <div className="range-fields"><label>Start (seconds)<input type="number" min={0} max={activeAsset?.duration_seconds} step="0.1" value={Number.isFinite(selectedRange.start_seconds) ? selectedRange.start_seconds : ''} onChange={(event) => setSelectedRange((range) => ({ ...range, start_seconds: event.target.valueAsNumber }))} /></label><label>End (seconds)<input type="number" min={4} max={activeAsset?.duration_seconds} step="0.1" value={Number.isFinite(selectedRange.end_seconds) ? selectedRange.end_seconds : ''} onChange={(event) => setSelectedRange((range) => ({ ...range, end_seconds: event.target.valueAsNumber }))} /></label></div>
                    <button type="button" className="secondary-button" onClick={() => {
                      const start = Math.max(0, Math.min(Math.round((sourcePlayer.current?.currentTime ?? 0) * 10) / 10, uploadedSource.asset.duration_seconds - 4))
                      setSelectedRange({ start_seconds: start, end_seconds: Math.min(start + 6, uploadedSource.asset.duration_seconds) })
                    }}>Start at current playback position</button>
                    {rangeError ? <p className="upload-warning" role="alert">{rangeError}</p> : <p className="input-help">{selectedRange.start_seconds.toFixed(1)}–{selectedRange.end_seconds.toFixed(1)}s · {(selectedRange.end_seconds - selectedRange.start_seconds).toFixed(1)} seconds selected</p>}
                  </fieldset>}
                  {!run && (
                    <button className="primary-button" onClick={start} disabled={busy || !activeAsset || !runtime?.mutable || Boolean(feedbackError) || Boolean(rangeError)}>
                      <Sparkles size={18} /> Review what can be automated
                    </button>
                  )}
                </div>
              </div>
            </section>

            {run?.notes.length ? (
              <section className="workspace-section request-section">
                <div className="section-heading">
                  <div><span className="step-number">02</span><div><h2>Choose a safe request</h2><p>Only checked requests can change the video.</p></div></div>
                  <span className="section-state state-active">Your decision</span>
                </div>
                <div className="request-summary" role="status">
                  <span className="summary-supported"><CheckCircle2 size={18} /> {executableNotes.length} ready</span>
                  <span><AlertTriangle size={18} /> {run.notes.filter((note) => note.classification === 'NEEDS_CLARIFICATION').length} need details</span>
                  <span><Info size={18} /> {run.notes.filter((note) => note.classification === 'MANUAL_CREATIVE').length} need an editor</span>
                </div>
                {unsupportedCount > 0 && (
                  <div className="partial-plan-callout">
                    <ShieldAlert size={20} />
                    <div><strong>{executableNotes.length ? 'Partial execution is explicit.' : 'This request cannot be automated yet.'}</strong><p>{executableNotes.length ? `RevisionProof will apply only the request you select below. The other ${unsupportedCount} request${unsupportedCount === 1 ? '' : 's'} will remain unchanged.` : 'This version creates center punch-ins. Edit your request to ask only for a zoom, or use a video editor for text, captions and other changes.'}</p></div>
                  </div>
                )}
                <div className="request-list">
                  {run.notes.map((note) => {
                    const executable = note.classification === 'AUTO_PREVIEWABLE' && run.feedback?.raw_text === note.raw_text
                    return (
                      <RequestRow
                        key={note.note_id}
                        note={note}
                        executable={executable}
                        selected={selectedNoteId === note.note_id}
                        disabled={busy || Boolean(run.candidates.length)}
                        onSelect={() => setSelectedNoteId((current) => current === note.note_id ? null : note.note_id)}
                      />
                    )
                  })}
                </div>
                {!run.candidates.length && run.state !== 'FAILED' && (
                  <div className="section-action-bar">
                    <div><strong>{executableNotes.length ? selectedNoteId ? '1 request selected' : 'Select one ready request' : 'Update the request to continue'}</strong><p>{executableNotes.length ? 'This demo applies one deterministic edit per proof.' : 'Your video, selected section and original wording will be kept.'}</p></div>
                    <button className="secondary-button" onClick={editRequest} disabled={busy}>Edit request</button>
                    {executableNotes.length > 0 && <button className="primary-button" onClick={renderPreviews} disabled={busy || !selectedNoteId}>
                      <Film size={18} /> Create A/B previews
                    </button>}
                  </div>
                )}
              </section>
            ) : null}

            {runtime?.intelligence_enabled && run?.feedback && (
              <EditMemory key={run.run_id} run={run} runtime={runtime} disabled={busy} />
            )}

            {run?.candidates.length ? (
              <section className="workspace-section compare-section">
                <div className="section-heading">
                  <div><span className="step-number">03</span><div><h2>Compare and choose</h2><p>Both options preserve timing and audio. Only the center crop strength changes.</p></div></div>
                  <span className="section-state state-active">Choose A or B</span>
                </div>
                {run.evidence[0] && (
                  <div className="evidence-summary">
                    <Clock3 size={20} />
                    <div><strong>{run.evidence[0].source === 'user.selected_range' ? 'Selected section' : 'Matched scene'} {formatTime(run.evidence[0].time_range.start_seconds)}–{formatTime(run.evidence[0].time_range.end_seconds)}</strong><p>{run.evidence[0].visual_summary}</p></div>
                    <span>{run.evidence[0].source === 'user.selected_range' ? 'Selected by you' : `${Math.round(run.evidence[0].score * 100)}% match`}</span>
                  </div>
                )}
                <div className="candidate-grid">
                  {run.candidates.map((candidate) => (
                    <CandidateCard
                      key={candidate.candidate_id}
                      candidate={candidate}
                      approved={run.spec?.approved_candidate.candidate_id === candidate.candidate_id}
                      busy={busy || Boolean(run.spec)}
                      onChoose={() => void chooseAndBuild(candidate.candidate_id)}
                      onViewLarge={() => {
                        if (!candidate.preview_url) return
                        setVideoPreview({
                          src: candidate.preview_url,
                          title: `Option ${candidate.candidate_id} · ${candidate.scale.toFixed(2)}× punch-in`,
                          detail: `${formatTime(candidate.time_range.start_seconds)}–${formatTime(candidate.time_range.end_seconds)} · centered crop`,
                        })
                      }}
                    />
                  ))}
                </div>
              </section>
            ) : null}

            {run?.spec && !run.proof && !processing && (
              <section className="workspace-section build-recovery-section">
                <div><AlertTriangle size={24} /><div><h2>The option is approved, but the full video is not ready.</h2><p>Retry the automatic build. Your frozen approval will not change.</p></div></div>
                <button className="primary-button" onClick={retryAutomaticBuild}><WandSparkles size={18} /> Build full video</button>
              </section>
            )}

            {run?.proof && (
              <section className={`result-section result-${run.proof.publish_allowed ? 'ready' : 'blocked'}`}>
                <div className="result-heading">
                  <div className="result-icon">{run.proof.publish_allowed ? <CheckCircle2 size={28} /> : <ShieldAlert size={28} />}</div>
                  <div><span>04 · FULL VIDEO VERIFICATION</span><h2>{run.proof.publish_allowed ? 'Your revised video is ready.' : 'The revised video is blocked.'}</h2><p>{run.proof.publish_allowed ? 'The selected edit was applied and every locked element still passes.' : 'One or more checks did not pass. Review the results below; delivery stays disabled.'}</p></div>
                </div>

                {run.generated_version_url && (
                  <div className="final-video-block">
                    <video src={run.generated_version_url} controls playsInline preload="metadata" />
                    <div className="final-video-actions">
                      <button className="secondary-button" onClick={() => setVideoPreview({ src: run.generated_version_url!, title: 'Full revised video', detail: `Option ${run.spec?.approved_candidate.candidate_id} applied to the complete ${run.asset.duration_seconds}-second source` })}>
                        <ZoomIn size={17} /> View larger
                      </button>
                      <a className="download-button" href={run.generated_version_url} download><Download size={17} /> Download MP4</a>
                    </div>
                  </div>
                )}

                <ChangeMap key={run.change_map?.analysis_id} run={run} />

                <div className="check-list">
                  {run.proof.checks.map((check) => (
                    <article key={check.check_id}>
                      <div className="check-name"><strong>{check.label}</strong><span>{formatTime(check.evidence_time_range.start_seconds)}–{formatTime(check.evidence_time_range.end_seconds)}</span></div>
                      <div className="check-metrics">
                        <span>Measured: {JSON.stringify(check.measured)}</span>
                        <span>Required: {JSON.stringify(check.threshold)}</span>
                        {check.failure_code && <code>{check.failure_code}</code>}
                        {check.evidence_urls.length === 2 && (
                          <div className="evidence-frames">
                            <figure><img src={check.evidence_urls[0]} alt="Original video verification frame" /><figcaption>ORIGINAL</figcaption></figure>
                            <figure><img src={check.evidence_urls[1]} alt={`${run.proof?.version_label} verification frame`} /><figcaption>REVISED</figcaption></figure>
                          </div>
                        )}
                      </div>
                      <VerdictPill verdict={check.verdict} />
                    </article>
                  ))}
                </div>

                <div className="delivery-action">
                  <div><strong>{run.delivery_approved ? 'Delivery approved' : 'Final human gate'}</strong><p>{run.delivery_approved ? 'This verified version is approved for delivery.' : 'Confirm only after you watch the full result.'}</p></div>
                  <button className="delivery-button" onClick={() => void action('delivery-approval', () => api.approveForDelivery(run.run_id))} disabled={busy || !run.proof.publish_allowed || run.delivery_approved || !runtime?.mutable}>
                    {run.delivery_approved ? <CheckCircle2 size={18} /> : <LockKeyhole size={18} />}
                    {run.delivery_approved ? 'Approved for delivery' : 'Approve for delivery'}
                  </button>
                </div>
                {runtime?.intelligence_enabled && <SaveApprovedMemory key={run.run_id} run={run} runtime={runtime} disabled={busy} onSaved={() => setRun((current) => current ? { ...current, memory_saved: true } : current)} />}
              </section>
            )}

            {run?.spec && (
              <details className="external-verification">
                <summary><ExternalLink size={17} /> Verify a video edited somewhere else</summary>
                <div>
                  <p>Use this only when an editor or another tool produced a separate full MP4. RevisionProof already builds its own result above.</p>
                  <button className="secondary-button" onClick={() => fileInput.current?.click()} disabled={busy || run.state === 'READY'}><Upload size={17} /> Choose external MP4</button>
                  <input ref={fileInput} hidden type="file" accept="video/mp4" onChange={(event) => uploadManual(event.target.files?.[0])} />
                  <small>Limits: MP4 · H.264/AAC · 1280×720 · up to 60 seconds · up to 24 MiB.</small>
                </div>
              </details>
            )}
          </div>

          <aside className="trace-column">
            <section className="proof-panel">
              <div className="trace-heading"><span>PROOF TRACE</span><span className={`live-dot live-dot-${(run?.mode ?? runtime?.mode ?? 'UNAVAILABLE').toLowerCase()}`} /></div>
              <div className="trace-list">
                {(run?.events ?? []).map((event) => (
                  <div className="trace-event" key={event.sequence}>
                    <span className="trace-node">{event.state === 'FAILED' || event.state === 'BLOCKED' ? <AlertTriangle size={13} /> : <Check size={13} />}</span>
                    <div><strong>{event.state.replaceAll('_', ' ')}</strong><p>{event.message}</p><small>{new Date(event.occurred_at).toLocaleTimeString()}</small></div>
                  </div>
                ))}
                {!run && <div className="empty-trace"><Search size={28} /><p>Run evidence and verification will appear here.</p></div>}
              </div>
              <div className="integration-box">
                <span className="micro-label">RUNTIME TRUTH</span>
                <dl>
                  <div><dt>Mode</dt><dd>{run?.mode ?? runtime?.mode ?? 'Checking'}</dd></div>
                  <div><dt>Interpreter</dt><dd>{run?.feedback?.interpreter_source ?? (run?.notes.length ? run.mode === 'LIVE' ? 'google.vertex.gemini' : run.asset.source_kind === 'upload' ? 'local.range_rules' : 'fixture.interpreter' : 'Not completed')}</dd></div>
                  <div><dt>Evidence</dt><dd>{run?.evidence[0]?.source ?? 'Not queried'}</dd></div>
                  <div><dt>Verdict owner</dt><dd>OpenCV + FFmpeg</dd></div>
                </dl>
              </div>
              {run && <a className="api-link" href={`/api/runs/${run.run_id}`} target="_blank" rel="noreferrer">Inspect raw run JSON <ChevronRight size={17} /></a>}
            </section>
          </aside>
        </section>
      </main>
      <footer><span>RevisionProof / v4</span><span>Only selected, verifiable edits run.</span></footer>
      {videoPreview && <VideoLightbox content={videoPreview} onClose={() => setVideoPreview(null)} />}
    </div>
  )
}
