import { useEffect, useRef, useState } from 'react'
import {
  AlertTriangle,
  BookOpen,
  Captions,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  Database,
  ExternalLink,
  FileVideo,
  Film,
  Fingerprint,
  Gauge,
  ImagePlus,
  Info,
  Languages,
  ListChecks,
  LockKeyhole,
  Plus,
  RefreshCw,
  Scissors,
  ShieldAlert,
  ShieldCheck,
  Type,
  Upload,
  Volume2,
  VolumeX,
  WandSparkles,
  XCircle,
  ZoomIn,
} from 'lucide-react'
import { api } from './api'
import { RequestDraft } from './EditComposer'
import { candidateTitle, editDetail, EDIT_LABELS, editSummary, operation, outputDuration, planProblem, seconds } from './editing'
import { ChangeMap, EditMemory, SaveApprovedMemory } from './RevisionIntelligence'
import { SourceUpload, type UploadedSource } from './SourceUpload'
import { StudioOperationEditor } from './StudioOperationEditor'
import { fileValidation, formatUploadSize, limitsFor } from './uploadValidation'
import { VideoLightbox, type VideoLightboxContent } from './VideoLightbox'
import { isTerminalRunState } from './runStream'
import { checkedVideoUrl, planAction, reviewedPlan, uploadPreparationRange, type ExternalVideo } from './studioWorkflow'
import type {
  DemoAsset,
  EditOperation,
  PatchCandidate,
  RunSnapshot,
  RuntimeStatus,
  SceneSearchHit,
  TranscriptionLanguage,
  Verdict,
} from './types'
import './editing.css'
import './studio.css'

type StudioView = 'flow' | 'library'
type ProcessingPhase = 'analyzing' | 'previews' | 'approving' | 'verifying' | 'delivery' | 'retrying' | 'logo' | 'subtitles'

const STEPS = ['Video', 'Edits', 'Plan', 'Compare', 'Check', 'Approve'] as const
const PROCESSING_COPY: Record<ProcessingPhase, { title: string; detail: string }> = {
  analyzing: { title: 'Preparing your plan…', detail: 'Checking the file and each edit. Suggested silence cuts will wait for your review.' },
  previews: { title: 'Creating two previews…', detail: 'Applying only the edits you selected. You will choose the version.' },
  approving: { title: 'Saving your choice…', detail: 'Locking the selected preview and its checks.' },
  verifying: { title: 'Building the full video…', detail: 'Applying your edits and checking the result against the source.' },
  delivery: { title: 'Approving the download…', detail: 'Your approval unlocks the verified file.' },
  retrying: { title: 'Retrying your request…', detail: 'Your file and edits are preserved while we reconnect.' },
  logo: { title: 'Checking your logo…', detail: 'Validating the image and saving it for this review.' },
  subtitles: { title: 'Creating subtitles…', detail: 'Transcribing speech into captions you can edit before processing.' },
}

const TOOL_CATALOG: Array<{ kind: EditOperation['kind']; label: string; hint: string; icon: typeof ZoomIn }> = [
  { kind: 'zoom', label: 'Zoom', hint: 'Compare two crop levels', icon: ZoomIn },
  { kind: 'text', label: 'Text overlay', hint: 'Add a title, note, or URL', icon: Type },
  { kind: 'subtitle', label: 'Captions', hint: 'Type or generate timed captions', icon: Captions },
  { kind: 'cut', label: 'Cut clip', hint: 'Remove video and audio together', icon: Scissors },
  { kind: 'remove_silence', label: 'Remove silence', hint: 'Review every suggested cut', icon: VolumeX },
  { kind: 'speed', label: 'Speed', hint: 'Slow down or speed up a clip', icon: Gauge },
  { kind: 'volume', label: 'Volume', hint: 'Mute, lower, or boost a clip', icon: Volume2 },
  { kind: 'logo', label: 'Logo', hint: 'Upload and position your logo', icon: ImagePlus },
]

function formatTime(value: number) {
  const minutes = Math.floor(value / 60)
  const remainder = Math.max(0, value - minutes * 60)
  return `${minutes}:${remainder.toFixed(1).padStart(4, '0')}`
}

function verdictLabel(verdict: Verdict) {
  if (verdict === 'PASS') return 'PASS'
  if (verdict === 'FAIL') return 'BLOCKED'
  if (verdict === 'NOT_CHECKED') return 'NEEDS REVIEW'
  return 'FAILED'
}

function StepBar({ step, maxStep, count, busy, onStep }: { step: number; maxStep: number; count: number; busy: boolean; onStep: (step: number) => void }) {
  return (
    <nav className="studio-stepbar" aria-label="Revision workflow">
      <div className="studio-steps">
        {STEPS.map((label, index) => {
          const number = index + 1
          const complete = number < step && number <= maxStep
          return (
            <button
              type="button"
              key={label}
              className={number === step ? 'is-current' : complete ? 'is-complete' : ''}
              aria-current={number === step ? 'step' : undefined}
              disabled={busy || number > maxStep}
              onClick={() => onStep(number)}
            >
              <span>{complete ? <Check size={13} /> : number}</span>
              <strong>{label}{number === 2 && count ? <em>{count}</em> : null}</strong>
            </button>
          )
        })}
      </div>
      <span>Step {step} of 6</span>
    </nav>
  )
}

function VideoFrame({ asset, label, onLarge, videoRef }: { asset: DemoAsset; label: string; onLarge: () => void; videoRef?: React.RefObject<HTMLVideoElement | null> }) {
  return (
    <figure className="studio-video-frame registration-frame">
      <figcaption><span>{label}</span><span>{asset.width}×{asset.height} · {seconds(asset.duration_seconds)}</span></figcaption>
      <video ref={videoRef} src={asset.source_url} controls muted playsInline preload="metadata" />
      <button type="button" onClick={onLarge}><ZoomIn size={16} />Open large view</button>
    </figure>
  )
}

function CandidateFrame({ candidate, selected, disabled, onChoose, onLarge }: {
  candidate: PatchCandidate
  selected: boolean
  disabled: boolean
  onChoose: () => void
  onLarge: () => void
}) {
  return (
    <article className={`studio-candidate registration-frame ${selected ? 'is-selected' : ''}`}>
      <header><span className="studio-candidate-letter">{candidate.candidate_id}</span><div><strong>{candidateTitle(candidate)}</strong><small>{candidate.patch_type === 'EDIT_PLAN' ? `${candidate.plan.operations.length} revisions` : `${candidate.scale.toFixed(2)}× crop`}</small></div>{selected && <span className="studio-tag is-pass"><Check size={12} />Selected</span>}</header>
      {candidate.preview_url ? <video src={candidate.preview_url} controls muted playsInline preload="metadata" /> : <div className="studio-video-placeholder">Preview unavailable</div>}
      <footer><button type="button" onClick={onLarge} disabled={!candidate.preview_url}><ZoomIn size={15} />Large view</button><button type="button" className="is-primary" disabled={disabled || selected} onClick={onChoose}>{selected ? 'Selected' : `Choose ${candidate.candidate_id}`}</button></footer>
    </article>
  )
}

function ProofTrace({ run, runtime }: { run: RunSnapshot | null; runtime: RuntimeStatus | null }) {
  const uploadState = run ? 'complete' : 'waiting'
  const interpretation = run?.feedback ? run.feedback.interpreter_source : 'not run'
  const scene = run?.evidence[0]?.source ?? 'off · no query'
  const processing = run?.candidates.length ? 'previews ready' : run ? run.state.replaceAll('_', ' ').toLowerCase() : 'not run'
  const verification = run?.proof ? verdictLabel(run.proof.verdict) : 'not run'
  const approval = run?.delivery_approved ? 'human approved' : 'not approved'
  return (
    <details className="studio-trace">
      <summary><span><ShieldCheck size={17} />Technical proof details</span><ChevronRight size={16} /></summary>
      <div className="studio-trace-body">
        <dl>
          <div><dt>Video upload</dt><dd>{uploadState}</dd></div>
          <div><dt>Request interpretation</dt><dd>{interpretation}</dd></div>
          <div><dt>Smart scene search</dt><dd>{scene}</dd></div>
          <div><dt>Revision processing</dt><dd>{processing}</dd></div>
          <div><dt>Result verification</dt><dd>{verification}</dd></div>
          <div><dt>Final approval</dt><dd>{approval}</dd></div>
        </dl>
        <div className="studio-runtime-truth"><span>RUNTIME</span><strong><CircleDot size={12} />{run?.mode ?? runtime?.mode ?? 'CHECKING'}</strong><p>{runtime?.message ?? 'Reading service capability…'}</p></div>
        {run?.events.length ? <ol>{run.events.map((event) => <li key={event.sequence}><span>{event.state === 'FAILED' || event.state === 'BLOCKED' ? <AlertTriangle size={12} /> : <Check size={12} />}</span><div><strong>{event.state.replaceAll('_', ' ')}</strong><small>{event.message}</small></div></li>)}</ol> : null}
        {run && <a href={`/api/runs/${run.run_id}`} target="_blank" rel="noreferrer">Inspect raw run JSON <ExternalLink size={14} /></a>}
      </div>
    </details>
  )
}

export default function StudioApp() {
  const [view, setView] = useState<StudioView>('flow')
  const [step, setStep] = useState(1)
  const [assets, setAssets] = useState<DemoAsset[]>([])
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null)
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null)
  const [uploadedSource, setUploadedSource] = useState<UploadedSource | null>(null)
  const [run, setRun] = useState<RunSnapshot | null>(null)
  const [operations, setOperations] = useState<EditOperation[]>([])
  const [selectedOperation, setSelectedOperation] = useState<number | null>(null)
  const [selectedEdits, setSelectedEdits] = useState<number[]>([])
  const [feedback, setFeedback] = useState('')
  const [usedDraftText, setUsedDraftText] = useState('')
  const [smartSelection, setSmartSelection] = useState<{ searchId: string; hit: SceneSearchHit } | null>(null)
  const [language, setLanguage] = useState<TranscriptionLanguage>('mixed')
  const [processing, setProcessing] = useState<ProcessingPhase | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [videoPreview, setVideoPreview] = useState<VideoLightboxContent | null>(null)
  const [externalVideo, setExternalVideo] = useState<ExternalVideo | null>(null)
  const sourcePlayer = useRef<HTMLVideoElement>(null)
  const logoInput = useRef<HTMLInputElement>(null)
  const externalInput = useRef<HTMLInputElement>(null)
  const runId = run?.run_id
  const busy = processing !== null
  const leftColumn = useRef<HTMLElement>(null)
  const centerColumn = useRef<HTMLDivElement>(null)
  const rightColumn = useRef<HTMLElement>(null)

  useEffect(() => {
    Promise.all([api.assets(), api.runtime()]).then(([nextAssets, nextRuntime]) => {
      setAssets(nextAssets)
      setRuntime(nextRuntime)
    }).catch((reason: Error) => setError(reason.message))
  }, [])

  useEffect(() => () => {
    if (uploadedSource) URL.revokeObjectURL(uploadedSource.asset.source_url)
  }, [uploadedSource])

  useEffect(() => () => {
    if (externalVideo) URL.revokeObjectURL(externalVideo.url)
  }, [externalVideo])

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

  useEffect(() => {
    leftColumn.current?.scrollTo({ top: 0 })
    centerColumn.current?.scrollTo({ top: 0 })
    rightColumn.current?.scrollTo({ top: 0 })
    if (window.matchMedia('(max-width: 939px)').matches) window.scrollTo({ top: 0 })
  }, [step, view])

  const selectedAsset = assets.find((asset) => asset.asset_id === selectedAssetId) ?? null
  const activeAsset = run?.asset ?? uploadedSource?.asset ?? selectedAsset
  const displayOperations = run?.edit_plan?.operations ?? operations
  const draftPlan = { source_duration: activeAsset?.duration_seconds ?? 0, operations }
  const pendingWords = feedback.trim().length > 0 && feedback !== usedDraftText
  const editProblem = activeAsset ? planProblem(draftPlan) ?? (pendingWords ? 'Turn the written request into revision items, or clear it before reviewing the plan.' : null) : 'Select a source video first.'
  const maxStep = !activeAsset ? 1
    : run?.proof?.publish_allowed ? 6
      : run?.spec ? 5
        : run?.candidates.length ? 4
          : operations.length || run?.edit_plan ? 3
            : 2

  const currentOperation = selectedOperation === null ? null : operations[selectedOperation] ?? null
  const selectedPlan = reviewedPlan(run, draftPlan, selectedEdits)
  const checkedVideo = checkedVideoUrl(run, externalVideo)
  const existingPlanAction = planAction(step, run)

  async function action(phase: ProcessingPhase, work: () => Promise<RunSnapshot>) {
    setProcessing(phase)
    setError(null)
    try {
      const next = await work()
      setRun(next)
      return next
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'RevisionProof could not finish that step.')
      return null
    } finally {
      setProcessing(null)
    }
  }

  function chooseSource(source: UploadedSource | null) {
    setExternalVideo(null)
    setError(null)
    setRun(null)
    setOperations([])
    setSelectedOperation(null)
    setSelectedEdits([])
    setFeedback('')
    setUsedDraftText('')
    setSmartSelection(null)
    if (source) {
      setUploadedSource(source)
      setSelectedAssetId(null)
    } else {
      setUploadedSource(null)
      setSelectedAssetId(assets[0]?.asset_id ?? null)
    }
  }

  function useSample() {
    const sample = assets[0]
    if (!sample) return
    setUploadedSource(null)
    setSelectedAssetId(sample.asset_id)
    setError(null)
  }

  function addOperation(kind: EditOperation['kind']) {
    if (!activeAsset || busy || run || operations.length >= 24) return
    if (kind === 'logo') {
      logoInput.current?.click()
      return
    }
    const start = kind === 'subtitle'
      ? operations.filter((item) => item.kind === 'subtitle').at(-1)?.end ?? smartSelection?.hit.start_seconds ?? 0
      : smartSelection?.hit.start_seconds ?? 0
    const end = kind === 'remove_silence'
      ? activeAsset.duration_seconds
      : kind === 'subtitle'
        ? Math.min(start + 3, activeAsset.duration_seconds)
        : smartSelection?.hit.end_seconds ?? Math.min(start + 4, activeAsset.duration_seconds)
    const next = [...operations, operation(kind, start, end)]
    setOperations(next)
    setSelectedOperation(next.length - 1)
    setError(null)
  }

  function changeOperation(update: Partial<EditOperation>) {
    if (selectedOperation === null) return
    setOperations((current) => current.map((item, index) => index === selectedOperation ? { ...item, ...update } : item))
  }

  function deleteOperation() {
    if (selectedOperation === null) return
    setOperations((current) => current.filter((_, index) => index !== selectedOperation))
    setSelectedOperation((current) => current === null ? null : current > 0 ? current - 1 : null)
  }

  function duplicateOperation() {
    if (!currentOperation || operations.length >= 24) return
    const next = [...operations]
    next.splice((selectedOperation ?? 0) + 1, 0, { ...currentOperation })
    setOperations(next)
    setSelectedOperation((selectedOperation ?? 0) + 1)
  }

  function moveOperation(direction: -1 | 1) {
    if (selectedOperation === null) return
    const target = selectedOperation + direction
    if (target < 0 || target >= operations.length) return
    const next = [...operations]
    ;[next[selectedOperation], next[target]] = [next[target], next[selectedOperation]]
    setOperations(next)
    setSelectedOperation(target)
  }

  function quickStart(which: 'intro' | 'captions' | 'silence' | 'pace') {
    if (!activeAsset || busy || run) return
    const duration = activeAsset.duration_seconds
    if (which === 'intro') {
      const start = duration >= 10 ? 4 : Math.round(duration * 0.35 * 10) / 10
      setOperations([operation('zoom', start, Math.min(10, duration)), operation('text', start, Math.min(10, duration), 'AI, made practical.')])
    } else if (which === 'captions') {
      const middle = Math.round(duration / 2 * 10) / 10
      setOperations([operation('subtitle', 0, middle, 'Meet KANAPP.'), operation('subtitle', middle, duration, 'AI, made practical.')])
    } else if (which === 'silence') {
      setOperations([operation('remove_silence', 0, duration)])
    } else {
      const rangeEnd = Math.min(8, duration)
      setOperations([operation('speed', 0, rangeEnd), operation('volume', 0, rangeEnd)])
    }
    setSelectedOperation(0)
    setUsedDraftText('')
    setError(null)
  }

  async function uploadLogo(file?: File) {
    if (!file || !activeAsset || busy || run) return
    if (operations.length >= 24) { setError('Use up to 24 edits in one video. Remove an edit before adding a logo.'); return }
    const maxBytes = runtime?.logo_limits?.max_bytes ?? 2 * 1048576
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      setError('Choose a PNG, JPG or WebP logo.')
      return
    }
    if (!file.size || file.size > maxBytes) {
      setError(`Logo must be no larger than ${formatUploadSize(maxBytes)}.`)
      return
    }
    setProcessing('logo')
    setError(null)
    try {
      const asset = await api.uploadLogo(file)
      const next = [...operations, { ...operation('logo', 0, activeAsset.duration_seconds), asset_id: asset.asset_id, asset_sha256: asset.sha256 }]
      setOperations(next)
      setSelectedOperation(next.length - 1)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The logo could not be uploaded.')
    } finally {
      setProcessing(null)
    }
  }

  async function generateSubtitles() {
    if (!activeAsset || busy || run || runtime?.mode !== 'LIVE') return
    setProcessing('subtitles')
    setError(null)
    try {
      const result = await api.transcribe(language, uploadedSource?.file, uploadedSource ? undefined : activeAsset.asset_id)
      const other = operations.filter((item) => item.kind !== 'subtitle')
      const subtitles = result.cues.slice(0, Math.max(0, 24 - other.length)).map((cue) => ({ ...operation('subtitle', cue.start, cue.end, cue.text), position: 'bottom' as const }))
      if (!subtitles.length) {
        setError(result.warnings[0] ?? 'No clear speech was detected. Add a subtitle manually instead.')
        return
      }
      setOperations([...other, ...subtitles])
      setSelectedOperation(other.length)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Speech could not be transcribed.')
    } finally {
      setProcessing(null)
    }
  }

  async function reviewPlan() {
    if (run?.edit_plan) { setStep(3); return }
    if (!activeAsset || !runtime?.mutable || editProblem) {
      setError(editProblem)
      return
    }
    const notes = feedback.trim() || operations.map(editSummary).join('\n').slice(0, 2000)
    let next: RunSnapshot | null
    if (uploadedSource) {
      const fileProblem = fileValidation(uploadedSource.file, limitsFor(runtime))
      if (fileProblem) { setError(fileProblem); return }
      const preparationRange = uploadPreparationRange(draftPlan, smartSelection?.hit)
      setUploadProgress(0)
      next = await action('analyzing', () => api.uploadSource(
        uploadedSource.file,
        notes,
        preparationRange,
        setUploadProgress,
        draftPlan,
        smartSelection ? { searchId: smartSelection.searchId, segmentId: smartSelection.hit.segment_id } : undefined,
      ))
    } else {
      next = await action('analyzing', () => api.createRun(
        activeAsset.asset_id,
        notes,
        draftPlan,
        smartSelection ? { searchId: smartSelection.searchId, segmentId: smartSelection.hit.segment_id } : undefined,
      ))
    }
    if (!next?.edit_plan) return
    setOperations(next.edit_plan.operations)
    setSelectedEdits(next.edit_plan.operations.flatMap((item, index) => item.detected ? [] : [index]))
    setSelectedOperation(null)
    setStep(3)
  }

  async function createPreviews() {
    if (run?.candidates.length) { setStep(4); return }
    if (!run?.edit_plan || !selectedPlan) return
    const problem = planProblem(selectedPlan)
    if (problem) { setError(problem); return }
    const next = await action('previews', () => api.previews(run.run_id, 'edit_plan', selectedPlan))
    if (next?.candidates.length) setStep(4)
  }

  async function chooseCandidate(candidateId: 'A' | 'B') {
    if (!run || run.spec) return
    const next = await action('approving', () => api.approve(run.run_id, candidateId))
    if (next?.spec) setStep(5)
  }

  async function verifyFullVideo() {
    if (!run?.spec) return
    setExternalVideo(null)
    await action('verifying', () => api.renderApprovedVersion(run.run_id))
  }

  async function uploadExternal(file?: File) {
    if (!run?.spec || !file) return
    const problem = fileValidation(file, limitsFor(runtime))
    if (problem) { setError(problem); return }
    setExternalVideo(null)
    const versionLabel = `external-${Date.now()}`
    const next = await action('verifying', () => api.uploadVersion(run.run_id, versionLabel, file))
    if (next?.proof?.version_label === versionLabel) {
      setExternalVideo({ runId: next.run_id, versionLabel, url: URL.createObjectURL(file) })
    }
  }

  async function approveAndDownload() {
    if (!run?.proof?.publish_allowed) return
    if (!run.delivery_approved) {
      const next = await action('delivery', () => api.approveForDelivery(run.run_id))
      if (!next?.delivery_approved) return
    }
    if (!checkedVideo) return
    const link = document.createElement('a')
    link.href = checkedVideo
    link.download = `revisionproof-${run.run_id}.mp4`
    link.click()
  }

  function seekOriginal(time: number) {
    if (sourcePlayer.current) {
      sourcePlayer.current.currentTime = time
      void sourcePlayer.current.play().catch(() => undefined)
    }
  }

  function editFromRun(index: number | null = null) {
    setExternalVideo(null)
    if (run?.edit_plan) setOperations([...run.edit_plan.operations.filter((item) => !item.detected)])
    setRun(null)
    setSelectedEdits([])
    setSelectedOperation(index)
    setStep(2)
    setError(null)
  }

  function newProof() {
    if (busy) return
    setView('flow')
    setExternalVideo(null)
    setRun(null)
    setOperations([])
    setSelectedOperation(null)
    setSelectedEdits([])
    setFeedback('')
    setUsedDraftText('')
    setSmartSelection(null)
    setStep(activeAsset ? 2 : 1)
    setError(null)
  }

  function openLarge(src: string, title: string, detail: string, startSeconds?: number) {
    setVideoPreview({ src, title, detail, startSeconds })
  }

  function goBack() {
    if (step <= 1) return
    setStep(step - 1)
  }

  function renderLeftColumn() {
    if (step === 1) return (
      <aside ref={leftColumn} className="studio-left studio-scroll-column">
        <section><span className="studio-kicker">SOURCE FILE</span><h2>Use a short video.</h2><ul className="studio-requirements"><li><FileVideo size={16} />MP4, MOV, or WebM</li><li><CheckCircle2 size={16} />Up to {formatUploadSize(limitsFor(runtime).max_bytes)}</li><li><CheckCircle2 size={16} />{limitsFor(runtime).min_duration_seconds}–{limitsFor(runtime).max_duration_seconds} seconds</li><li><ShieldCheck size={16} />Checked before upload</li></ul></section>
        <section className="studio-next-card"><span>NEXT</span><strong>Add edits without changing the original.</strong><p>Review the full plan before anything runs.</p></section>
      </aside>
    )
    if (step === 2) return (
      <aside ref={leftColumn} className="studio-left studio-scroll-column">
        <section><span className="studio-kicker">EDIT TOOLS</span><h2>Choose an edit.</h2><p className="studio-muted">Its settings open beside the edit list.</p></section>
        <div className="studio-tool-list">
          {TOOL_CATALOG.map(({ kind, label, hint, icon: Icon }) => {
            const count = operations.filter((item) => item.kind === kind).length
            return <button type="button" key={kind} disabled={busy || Boolean(run) || operations.length >= 24} onClick={() => addOperation(kind)}><Icon size={18} /><span><strong>{label}</strong><small>{hint}</small></span>{count ? <em>{count}</em> : <Plus size={14} />}</button>
          })}
        </div>
        <section className="studio-subtitle-tool"><div><Languages size={19} /><span><strong>Create from speech</strong><small>Gemini · edit before use</small></span></div><select value={language} onChange={(event) => setLanguage(event.target.value as TranscriptionLanguage)} disabled={busy || Boolean(run)}><option value="auto">Detect Korean + English</option><option value="ko">Korean</option><option value="en">English</option><option value="mixed">Korean + English</option></select><button type="button" onClick={() => void generateSubtitles()} disabled={busy || Boolean(run) || runtime?.mode !== 'LIVE'}>Create captions</button>{runtime?.mode !== 'LIVE' && <small>LIVE only. You can still type captions.</small>}</section>
      </aside>
    )
    const processed = Boolean(run?.candidates.length)
    const verified = Boolean(run?.proof)
    return (
      <aside ref={leftColumn} className="studio-left studio-scroll-column">
        <section><span className="studio-kicker">PROGRESS</span><h2>Your review, step by step.</h2></section>
        <ol className="studio-checklist">
          <li className="is-done"><Check size={14} /><span><strong>Source selected</strong><small>{activeAsset?.title}</small></span></li>
          <li className={displayOperations.length ? 'is-done' : ''}>{displayOperations.length ? <Check size={14} /> : <span>2</span>}<span><strong>Edits added</strong><small>{displayOperations.length} items</small></span></li>
          <li className={processed ? 'is-done' : ''}>{processed ? <Check size={14} /> : <span>3</span>}<span><strong>Previews ready</strong><small>{processed ? `${run?.candidates.length} versions` : 'Not started'}</small></span></li>
          <li className={run?.spec ? 'is-done' : ''}>{run?.spec ? <Check size={14} /> : <span>4</span>}<span><strong>Version selected</strong><small>{run?.spec ? `Version ${run.spec.approved_candidate.candidate_id}` : 'Waiting for you'}</small></span></li>
          <li className={verified ? 'is-done' : ''}>{verified ? <Check size={14} /> : <span>5</span>}<span><strong>Full check</strong><small>{run?.proof ? verdictLabel(run.proof.verdict) : 'Not started'}</small></span></li>
          <li className={run?.delivery_approved ? 'is-done' : ''}>{run?.delivery_approved ? <Check size={14} /> : <span>6</span>}<span><strong>Final approval</strong><small>{run?.delivery_approved ? 'Human approved' : 'Never automatic'}</small></span></li>
        </ol>
      </aside>
    )
  }

  function renderRevisionList() {
    return (
      <section className="studio-revision-list">
        <header><div><span className="studio-kicker">REVISION LIST</span><h3>{displayOperations.length} / 24 queued</h3></div>{displayOperations.length === 24 && <span className="studio-tag is-warning">Limit reached</span>}</header>
        {displayOperations.length ? <ol>{displayOperations.map((item, index) => {
          const selected = step === 2 && !run && selectedOperation === index
          const included = !run?.edit_plan || selectedEdits.includes(index) || Boolean(run.candidates.length)
          return <li key={`${item.kind}-${index}`} className={selected ? 'is-selected' : ''}><button type="button" onClick={() => { if (step === 2 && !run) setSelectedOperation(index) }}><span className="studio-revision-number">{String(index + 1).padStart(2, '0')}</span><span><strong>{item.detected ? 'Proposed quiet cut' : EDIT_LABELS[item.kind]}</strong><small>{editDetail(item)}</small></span><em className={`studio-tag ${included ? 'is-ready' : 'is-muted'}`}>{included ? item.detected ? 'check' : 'ready' : 'skipped'}</em></button></li>
        })}</ol> : <div className="studio-list-empty"><ListChecks size={28} /><strong>No edits yet</strong><p>Choose a tool or write a request.</p></div>}
      </section>
    )
  }

  function renderCenter() {
    if (step === 1) return (
      <section className="studio-center-stage studio-source-stage">
        <header><span className="studio-kicker">01 · VIDEO</span><h1>{activeAsset ? 'Video ready.' : 'Choose a video.'}</h1><p>We check the file before upload.</p></header>
        {!activeAsset ? <div className="studio-drop-zone registration-frame"><Upload size={34} /><strong>Choose a video to upload</strong><p>Your original stays unchanged.</p><SourceUpload runtime={runtime} selected={null} disabled={busy || !runtime?.mutable} onSelect={chooseSource} /><span>or</span><button type="button" className="studio-secondary" onClick={useSample} disabled={!assets.length || busy}>Use sample video</button><small>Try every editing tool with the built-in demo.</small></div> : <><VideoFrame asset={activeAsset} label="VIDEO PREVIEW" videoRef={sourcePlayer} onLarge={() => openLarge(activeAsset.source_url, 'Source video', `${activeAsset.title} · ${activeAsset.width}×${activeAsset.height}`)} /><div className="studio-file-check"><div><CheckCircle2 size={20} /><span><strong>File check passed</strong><small>Ready to add edits without changing the original</small></span></div><dl><div><dt>Name</dt><dd>{activeAsset.title}</dd></div><div><dt>Duration</dt><dd>{seconds(activeAsset.duration_seconds)}</dd></div><div><dt>Resolution</dt><dd>{activeAsset.width}×{activeAsset.height}</dd></div><div><dt>Codec</dt><dd>{activeAsset.codec}</dd></div>{uploadedSource && <div><dt>Size</dt><dd>{formatUploadSize(uploadedSource.file.size)}</dd></div>}</dl><SourceUpload runtime={runtime} selected={uploadedSource} disabled={busy || Boolean(run) || !runtime?.mutable} onSelect={chooseSource} /></div></>}
      </section>
    )

    if (step === 2) return (
      <section className="studio-center-stage studio-revisions-stage">
        <header><span className="studio-kicker">02 · EDITS</span><h1>Choose your edits.</h1><p>Add a tool, then adjust its settings.</p></header>
        {activeAsset && <VideoFrame asset={activeAsset} label="SOURCE TIMELINE" videoRef={sourcePlayer} onLarge={() => openLarge(activeAsset.source_url, 'Original video', `${activeAsset.title} · all times use this source`)} />}
        {displayOperations.length > 0 && activeAsset && <div className="studio-timeline" aria-label="Queued revision ranges"><div>{displayOperations.map((item, index) => <button type="button" key={index} title={`${EDIT_LABELS[item.kind]} ${editDetail(item)}`} style={{ left: `${item.start / activeAsset.duration_seconds * 100}%`, width: `${Math.max(1.5, (item.end - item.start) / activeAsset.duration_seconds * 100)}%`, top: `${(index % 3) * 8}px` }} onClick={() => !run && setSelectedOperation(index)} />)}</div><span>0:00</span><span>{formatTime(activeAsset.duration_seconds)}</span></div>}
        {run ? <div className="studio-callout"><Info size={19} /><div><strong>This plan has been reviewed.</strong><p>Review it here, or reopen these edits as a new draft.</p></div><button type="button" onClick={() => editFromRun()} disabled={busy}>Edit a copy</button></div> : activeAsset ? <RequestDraft key={activeAsset.source_url} text={feedback} onText={setFeedback} duration={activeAsset.duration_seconds} disabled={busy || !runtime?.mutable} onApply={(plan) => { const available = Math.max(0, 24 - operations.length); const additions = plan.operations.slice(0, available); setOperations([...operations, ...additions]); setSelectedOperation(operations.length); setUsedDraftText(feedback); setError(additions.length < plan.operations.length ? 'The draft was clipped at the 24-edit limit.' : null) }} onBusy={(value) => { if (value) setProcessing('analyzing'); else setProcessing(null) }} sourceFile={uploadedSource?.file} assetId={uploadedSource ? undefined : activeAsset.asset_id} mode={runtime?.mode} onSceneSelect={(selection) => setSmartSelection(selection)} /> : null}
        {!run && <section className="studio-quick-starts"><header><span className="studio-kicker">TEMPLATES</span><p>Replace the list. Edit every field.</p></header><div><button type="button" onClick={() => quickStart('intro')}><strong>Promo highlight</strong><small>Zoom + “AI, made practical.”</small></button><button type="button" onClick={() => quickStart('captions')}><strong>Two captions</strong><small>Separate times and editable text</small></button><button type="button" onClick={() => quickStart('silence')}><strong>Remove silence</strong><small>Review suggested cuts in Plan</small></button><button type="button" onClick={() => quickStart('pace')}><strong>Speed + volume</strong><small>1.5× and −6 dB on one clip</small></button><button type="button" onClick={() => logoInput.current?.click()} disabled={busy || operations.length >= 24}><strong>Company logo</strong><small>Full video, bottom right</small></button><button type="button" onClick={() => void generateSubtitles()} disabled={runtime?.mode !== 'LIVE'}><strong>Speech captions</strong><small>Korean + English with Gemini</small></button></div></section>}
      </section>
    )

    if (step === 3) {
      const plan = run?.edit_plan ?? draftPlan
      const chosen = selectedPlan
      return <section className="studio-center-stage studio-plan-stage"><header><span className="studio-kicker">03 · PLAN</span><h1>Review the plan.</h1><p>Remove any edit you do not want in the previews.</p></header>{run?.edit_warnings?.map((warning, index) => <div className="studio-callout is-warning" key={index}><AlertTriangle size={18} /><p>{warning}</p></div>)}<ol className="studio-plan-list">{plan.operations.map((item, index) => { const checked = !run?.edit_plan || Boolean(run.candidates.length) || selectedEdits.includes(index); return <li key={index} className={checked ? '' : 'is-skipped'}><label><input type="checkbox" checked={checked} disabled={!run?.edit_plan || Boolean(run.candidates.length) || busy} onChange={() => setSelectedEdits(checked ? selectedEdits.filter((value) => value !== index) : [...selectedEdits, index])} /><span><strong>{item.detected ? 'Suggested silence cut' : EDIT_LABELS[item.kind]}</strong><small>{editSummary(item)} · source time</small></span></label><span className={`studio-tag ${checked ? item.detected ? 'is-warning' : 'is-ready' : 'is-muted'}`}>{checked ? item.detected ? 'review' : 'included' : 'skipped'}</span><button type="button" onClick={() => activeAsset && openLarge(activeAsset.source_url, 'Original video', `${EDIT_LABELS[item.kind]} · ${editDetail(item)}`, item.start)}><Film size={14} />Watch</button></li>})}</ol><div className="studio-duration-row"><span>Original <strong>{seconds(plan.source_duration)}</strong></span><ChevronRight size={18} /><span>After edits <strong>{seconds(outputDuration(chosen))}</strong></span></div>{run?.edit_plan && !run.candidates.length && selectedPlan.operations.length === 0 && <div className="studio-callout is-warning" role="status"><Info size={18} /><p>Select at least one edit to create previews.</p></div>}{!run && <div className="studio-callout"><Info size={18} /><p>Select Check plan below before creating previews.</p></div>}</section>
    }

    if (step === 4) return <section className="studio-center-stage studio-ab-stage"><header><span className="studio-kicker">04 · COMPARE</span><h1>Compare both versions.</h1><p>Both include the same edits. Version B uses a stronger visual effect when available.</p></header>{run?.evidence[0] && <div className="studio-evidence-line"><Database size={16} /><span><strong>{formatTime(run.evidence[0].time_range.start_seconds)}–{formatTime(run.evidence[0].time_range.end_seconds)}</strong>{run.evidence[0].visual_summary}</span><em>{run.evidence[0].source}</em></div>}<div className="studio-candidate-grid">{run?.candidates.map((candidate) => <CandidateFrame key={candidate.candidate_id} candidate={candidate} selected={run.spec?.approved_candidate.candidate_id === candidate.candidate_id} disabled={busy || Boolean(run.spec)} onChoose={() => void chooseCandidate(candidate.candidate_id)} onLarge={() => candidate.preview_url && openLarge(candidate.preview_url, `Version ${candidate.candidate_id}`, candidateTitle(candidate))} />)}</div>{run?.spec && <div className="studio-callout is-success"><CheckCircle2 size={19} /><div><strong>Version {run.spec.approved_candidate.candidate_id} selected.</strong><p>Next, build the full video and run checks. Final approval comes later.</p></div></div>}</section>

    if (step === 5) return <section className="studio-center-stage studio-verify-stage"><header><span className="studio-kicker">05 · CHECK</span><h1>{run?.proof ? run.proof.publish_allowed ? 'Full video passed.' : 'Download is blocked.' : 'Build and check the full video.'}</h1><p>Automated checks decide PASS or BLOCKED. AI does not set the result.</p></header>{!run?.proof ? <div className="studio-verify-idle registration-frame"><ShieldCheck size={42} /><h2>You stay in control.</h2><p>We apply your chosen version, build the full video, and check the edits and protected content.</p><button type="button" className="studio-primary" onClick={() => void verifyFullVideo()} disabled={busy || !run?.spec}><WandSparkles size={18} />Build & check full video</button><button type="button" onClick={() => externalInput.current?.click()} disabled={busy || !run?.spec}><Upload size={17} />Check an external edit</button></div> : <><div className={`studio-verdict ${run.proof.publish_allowed ? 'is-pass' : 'is-blocked'}`}><span>{run.proof.publish_allowed ? <CheckCircle2 size={30} /> : <ShieldAlert size={30} />}</span><div><em>{verdictLabel(run.proof.verdict)}</em><h2>{run.proof.publish_allowed ? 'Your edits are in place and protected content stayed unchanged.' : 'At least one required check failed.'}</h2><p>{run.proof.publish_allowed ? 'Watch the result before approving the download.' : 'See the measured result and required level below.'}</p></div></div>{run && checkedVideo && <div className="studio-final-video registration-frame"><video src={checkedVideo} controls playsInline preload="metadata" /><button type="button" onClick={() => openLarge(checkedVideo!, 'Checked full video', `Version ${run.spec?.approved_candidate.candidate_id} · ${verdictLabel(run.proof!.verdict)}`)}><ZoomIn size={16} />Open large view</button></div>}<div className="studio-check-grid">{run.proof.checks.map((check) => <article key={check.check_id}><header><strong>{check.label}</strong><span className={`studio-tag ${check.verdict === 'PASS' ? 'is-pass' : 'is-warning'}`}>{check.verdict}</span></header><dl><div><dt>Measured</dt><dd>{JSON.stringify(check.measured)}</dd></div><div><dt>Required</dt><dd>{JSON.stringify(check.threshold)}</dd></div></dl>{check.failure_code && <code>{check.failure_code}</code>}<small>{formatTime(check.evidence_time_range.start_seconds)}–{formatTime(check.evidence_time_range.end_seconds)}</small></article>)}</div><ChangeMap run={run} />{!run.proof.publish_allowed && <div className="studio-callout is-warning"><AlertTriangle size={18} /><div><strong>See what caused the failure.</strong><p>Check whether the issue was already in the source or came from an edit. Approval stays locked.</p></div><button type="button" onClick={() => editFromRun()} disabled={busy}>Open edits</button><button type="button" onClick={() => externalInput.current?.click()} disabled={busy}>Upload corrected edit</button></div>}</>}
      </section>

    return <section className="studio-center-stage studio-approve-stage"><header><span className="studio-kicker">06 · APPROVE</span><h1>Review, then approve.</h1><p>{checkedVideo ? 'Watch the result. Only your approval unlocks the download.' : 'Approve the verified external file for delivery. Keep your original uploaded copy.'}</p></header>{run && checkedVideo && <div className="studio-approval-layout"><div className="studio-final-video registration-frame"><video src={checkedVideo} controls playsInline preload="metadata" /><button type="button" onClick={() => openLarge(checkedVideo!, 'Final checked video', run.asset.title)}><ZoomIn size={16} />Open large view</button></div><dl className="studio-result-table"><div><dt>Check</dt><dd><span className="studio-tag is-pass">PASS</span></dd></div><div><dt>Applied</dt><dd>{run.spec?.approved_candidate.patch_type === 'EDIT_PLAN' ? run.spec.approved_candidate.plan.operations.length : 1} edits</dd></div><div><dt>Selected</dt><dd>Version {run.spec?.approved_candidate.candidate_id}</dd></div><div><dt>Duration</dt><dd>{seconds(run.asset.duration_seconds)} → {run.spec?.approved_candidate.patch_type === 'EDIT_PLAN' ? seconds(outputDuration(run.spec.approved_candidate.plan)) : seconds(run.asset.duration_seconds)}</dd></div><div><dt>Approval</dt><dd>{run.delivery_approved ? 'Approved by you' : 'Waiting for you'}</dd></div></dl></div>}{run && runtime?.intelligence_enabled && <SaveApprovedMemory key={run.run_id} run={run} runtime={runtime} disabled={busy} onSaved={() => setRun((current) => current ? { ...current, memory_saved: true } : current)} />}</section>
  }

  const primaryLabel = existingPlanAction?.label ?? (step === 1 ? 'Continue to edits'
    : step === 2 ? `Check plan (${operations.length})`
      : step === 3 ? run?.edit_plan ? 'Create previews' : 'Check plan'
        : step === 4 ? run?.spec ? 'Continue to checks' : 'Choose A or B above'
          : step === 5 ? run?.proof?.publish_allowed ? 'Continue to approval' : run?.proof ? 'Run checks again' : 'Build & check full video'
            : run?.delivery_approved ? checkedVideo ? 'Download approved video' : 'Delivery approved' : checkedVideo ? 'Approve & download' : 'Approve for delivery')

  const primaryDisabled = busy || !runtime?.mutable || (step === 1 && !activeAsset) || (step === 2 && !run?.edit_plan && Boolean(editProblem)) || (step === 3 && (run?.edit_plan ? Boolean(planProblem(selectedPlan ?? { source_duration: 0, operations: [] })) : Boolean(editProblem))) || (step === 4 && !run?.spec) || (step === 5 && !run?.spec) || (step === 6 && (!run?.proof?.publish_allowed || (run.delivery_approved && !checkedVideo)))

  function primaryAction() {
    if (existingPlanAction) setStep(existingPlanAction.nextStep)
    else if (step === 1) setStep(2)
    else if (step === 2) void reviewPlan()
    else if (step === 3) {
      if (run?.edit_plan) void createPreviews()
      else void reviewPlan()
    }
    else if (step === 4 && run?.spec) setStep(5)
    else if (step === 5 && run?.proof?.publish_allowed) setStep(6)
    else if (step === 5) void verifyFullVideo()
    else if (step === 6) void approveAndDownload()
  }

  return (
    <div className="rp-studio">
      <header className="studio-topbar">
        <button type="button" className="studio-brand" onClick={() => { setView('flow'); setStep(1) }} aria-label="RevisionProof Studio home" disabled={busy}><span><Fingerprint size={19} /></span><strong>RevisionProof</strong></button>
        <span className={`studio-env env-${(run?.mode ?? runtime?.mode ?? 'unavailable').toLowerCase()}`}><CircleDot size={11} />{run?.mode ?? runtime?.mode ?? 'CHECKING'}</span>
        <nav aria-label="Studio navigation"><button type="button" aria-label="Approved edits" title="Approved edits" className={view === 'library' ? 'is-active' : ''} onClick={() => setView('library')} disabled={busy}><BookOpen size={18} /><span>Approved edits</span></button><a href="/" aria-label="Classic UI" title="Classic UI"><ExternalLink size={18} /><span>Classic UI</span></a><button type="button" aria-label="New review" title="New review" onClick={newProof} disabled={busy}><RefreshCw size={18} /><span>New review</span></button></nav>
      </header>

      {view === 'flow' ? <StepBar step={step} maxStep={maxStep} count={displayOperations.length} busy={busy} onStep={setStep} /> : <div className="studio-sideview-title"><button type="button" onClick={() => setView('flow')}><ChevronLeft size={16} />Back to workflow</button><span>Approved edits</span></div>}

      {processing && <div className="studio-processing" role="status" aria-live="polite" aria-busy="true"><span className="studio-spinner" /><div><strong>{PROCESSING_COPY[processing].title}</strong><p>{PROCESSING_COPY[processing].detail}{processing === 'analyzing' && uploadedSource && uploadProgress > 0 ? ` Upload ${uploadProgress}%.` : ''}</p></div></div>}
      {error && <div className="studio-error" role="alert"><ShieldAlert size={19} /><div><strong>That step could not finish.</strong><p>{error}</p></div><button type="button" onClick={() => setError(null)} aria-label="Dismiss error"><XCircle size={17} /></button></div>}
      {run?.state === 'FAILED' && run.retryable && !busy && <div className="studio-recovery"><div><strong>Your video and edits are safe.</strong><p>{run.error ?? 'The request stopped safely.'}</p></div><button type="button" onClick={() => editFromRun()}>Adjust edits</button><button type="button" onClick={() => void action('retrying', () => api.retryRun(run.run_id))}>Retry</button></div>}

      {view === 'library' ? <main className="studio-library-view"><section><span className="studio-kicker">APPROVED EDIT MEMORY</span><h1>Reuse past edits, then check again.</h1><p>A past match can start a new draft. Every video still needs fresh previews, checks, and approval.</p>{runtime?.memory_save_policy === 'read_only' && <div className="studio-callout"><LockKeyhole size={19} /><div><strong>Saving is off on this deployment.</strong><p>Public users can view matches, but cannot add records.</p></div></div>}{run?.feedback && runtime?.intelligence_enabled ? <EditMemory run={run} runtime={runtime} disabled={busy} onApply={(plan, label) => { setOperations([...plan.operations]); setFeedback(label); setUsedDraftText(label); setRun(null); setSelectedOperation(0); setStep(2); setView('flow') }} /> : <div className="studio-library-empty registration-frame"><Database size={36} /><h2>No request to compare yet.</h2><p>Start a review first. Matching approved edits will appear in that context.</p><button type="button" className="studio-primary" onClick={() => setView('flow')}>Return to workflow</button></div>}</section></main> : <>
        <main className="studio-workspace">
          {renderLeftColumn()}
          <div ref={centerColumn} className="studio-center studio-scroll-column">{renderCenter()}</div>
          <aside ref={rightColumn} className="studio-right studio-scroll-column">
            {step === 2 && <StudioOperationEditor operation={currentOperation} index={selectedOperation} duration={activeAsset?.duration_seconds ?? 0} disabled={busy || Boolean(run)} canMoveDown={selectedOperation !== null && selectedOperation < operations.length - 1} canDuplicate={operations.length < 24} onChange={changeOperation} onDelete={deleteOperation} onDuplicate={duplicateOperation} onMove={moveOperation} onSeek={seekOriginal} />}
            {step === 2 && !run && editProblem && (operations.length > 0 || pendingWords) && <div className="studio-callout is-warning" role="status"><AlertTriangle size={18} /><p>{editProblem}</p></div>}
            {renderRevisionList()}
            <ProofTrace run={run} runtime={runtime} />
          </aside>
        </main>
        <footer className="studio-actionbar"><div><span className="studio-kicker">CURRENT STEP</span><p>{step === 1 ? activeAsset ? `File ready · ${activeAsset.title}` : 'Choose a video to begin' : step === 2 ? run ? `${displayOperations.length} edits in the reviewed plan` : `${operations.length} of 24 edits added · nothing has run` : step === 3 ? `${selectedPlan.operations.length} edits selected for preview` : step === 4 ? run?.spec ? `Version ${run.spec.approved_candidate.candidate_id} selected · ${run.proof ? verdictLabel(run.proof.verdict) : 'checks not run'}` : 'Watch both versions before choosing' : step === 5 ? run?.proof ? `${verdictLabel(run.proof.verdict)} · ${run.proof.checks.filter((check) => check.verdict === 'PASS').length} of ${run.proof.checks.length} checks pass` : 'Build the full video to run checks' : 'Final step · only you can approve'}</p></div>{step > 1 && <button type="button" className="studio-back" onClick={goBack} disabled={busy}><ChevronLeft size={16} />Back to {STEPS[step - 2]}</button>}<button type="button" className="studio-primary" onClick={primaryAction} disabled={primaryDisabled}>{primaryLabel}<ChevronRight size={16} /></button></footer>
      </>}

      <input ref={logoInput} hidden type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" aria-label="Upload logo image" onChange={(event) => { void uploadLogo(event.target.files?.[0]); event.target.value = '' }} />
      <input ref={externalInput} hidden type="file" accept="video/mp4" aria-label="Upload external edited video" onChange={(event) => { void uploadExternal(event.target.files?.[0]); event.target.value = '' }} />
      {videoPreview && <VideoLightbox content={videoPreview} onClose={() => setVideoPreview(null)} />}
    </div>
  )
}
