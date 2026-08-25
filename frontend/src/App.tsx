import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Clock3,
  FileCheck2,
  Film,
  Fingerprint,
  LockKeyhole,
  Play,
  Search,
  ShieldAlert,
  Sparkles,
  Upload,
  XCircle,
} from 'lucide-react'
import { api } from './api'
import type { DemoAsset, PatchCandidate, RunSnapshot, Verdict } from './types'

const DEFAULT_FEEDBACK = 'Can we make the product reveal feel more intentional?'

function formatTime(seconds: number) {
  const minute = Math.floor(seconds / 60)
  const second = Math.floor(seconds % 60)
  return `${minute}:${second.toString().padStart(2, '0')}`
}

function VerdictPill({ verdict }: { verdict: Verdict }) {
  const Icon = verdict === 'PASS' ? CheckCircle2 : verdict === 'FAIL' ? XCircle : ShieldAlert
  return (
    <span className={`verdict verdict-${verdict.toLowerCase()}`}>
      <Icon size={14} /> {verdict}
    </span>
  )
}

function CandidateCard({
  candidate,
  approved,
  onApprove,
  busy,
}: {
  candidate: PatchCandidate
  approved: boolean
  onApprove: () => void
  busy: boolean
}) {
  return (
    <article className={`candidate-card ${approved ? 'candidate-approved' : ''}`}>
      <div className="candidate-heading">
        <span className="candidate-letter">{candidate.candidate_id}</span>
        <div>
          <p>{candidate.scale.toFixed(2)}× center punch-in</p>
          <span>
            {formatTime(candidate.time_range.start_seconds)}–{formatTime(candidate.time_range.end_seconds)}
          </span>
        </div>
        {approved && <span className="approved-label"><Check size={13} /> Approved</span>}
      </div>
      {candidate.preview_url && <video src={candidate.preview_url} controls muted playsInline />}
      {!approved && (
        <button className="secondary-button full-button" onClick={onApprove} disabled={busy}>
          Approve option {candidate.candidate_id} <ArrowRight size={15} />
        </button>
      )}
    </article>
  )
}

export default function App() {
  const [assets, setAssets] = useState<DemoAsset[]>([])
  const [run, setRun] = useState<RunSnapshot | null>(null)
  const [feedback, setFeedback] = useState(DEFAULT_FEEDBACK)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const runId = run?.run_id

  useEffect(() => {
    api.assets().then(setAssets).catch((reason: Error) => setError(reason.message))
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
    })
    return () => stream.close()
  }, [runId])

  const activeAsset = run?.asset ?? assets[0]
  const progress = useMemo(() => {
    if (!run) return 0
    if (run.state === 'READY') return 100
    if (run.state === 'BLOCKED') return 84
    if (run.state === 'HUMAN_APPROVED') return 68
    if (run.state === 'PREVIEWS_READY') return 50
    if (run.state === 'EVIDENCE_ANCHORED') return 32
    return 15
  }, [run])

  async function action(work: () => Promise<RunSnapshot>) {
    setBusy(true)
    setError(null)
    try {
      setRun(await work())
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unexpected request failure')
    } finally {
      setBusy(false)
    }
  }

  function start() {
    if (!activeAsset) return
    void action(() => api.createRun(activeAsset.asset_id, feedback))
  }

  function uploadManual(file?: File) {
    if (!run || !file) return
    void action(() => api.uploadVersion(run.run_id, file.name.replace(/\.mp4$/i, ''), file))
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RevisionProof home">
          <span className="brand-mark"><Fingerprint size={20} /></span>
          <span>Revision<span>Proof</span></span>
        </a>
        <div className="header-meta">
          <span className={`mode-badge mode-${(run?.mode ?? 'FIXTURE').toLowerCase()}`}>
            <CircleDot size={12} /> {run?.mode ?? 'FIXTURE'} MODE
          </span>
          <span className="run-id">{run ? `RUN ${run.run_id.slice(-8)}` : 'NEW PROOF'}</span>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="eyebrow"><LockKeyhole size={14} /> APPROVAL, MADE EXECUTABLE</div>
          <h1>Know exactly<br /><em>what changed.</em></h1>
          <p>Turn ambiguous feedback into an approved patch, then block any version that breaks what was already locked.</p>
          <div className="hero-rule"><span style={{ width: `${progress}%` }} /></div>
        </section>

        {error && <div className="error-banner"><ShieldAlert size={17} /><span>{error}</span></div>}

        <section className="workspace-grid">
          <div className="primary-column">
            <section className="panel intake-panel">
              <div className="panel-heading">
                <div><span className="step-number">01</span><h2>Interpret the note</h2></div>
                <span className="panel-status">{run ? 'CAPTURED' : 'WAITING'}</span>
              </div>
              {activeAsset && (
                <div className="asset-strip">
                  <Film size={18} />
                  <div><strong>{activeAsset.title}</strong><span>{activeAsset.width}×{activeAsset.height} · {activeAsset.duration_seconds}s · {activeAsset.codec}</span></div>
                  <Play size={16} />
                </div>
              )}
              <label htmlFor="feedback">Client feedback</label>
              <textarea id="feedback" value={feedback} onChange={(event) => setFeedback(event.target.value)} disabled={Boolean(run)} />
              {!run && (
                <button className="primary-button" onClick={start} disabled={busy || !activeAsset || feedback.length < 8}>
                  <Sparkles size={16} /> {busy ? 'Interpreting…' : 'Interpret & locate evidence'}
                </button>
              )}
              {run?.feedback && (
                <div className="interpretation">
                  <span className="micro-label">INTERPRETED INTENT</span>
                  <p>{run.feedback.intent}</p>
                  <div className="chip-row"><span>PUNCH_IN</span><span>“{run.feedback.target_phrase}”</span></div>
                  <small>Source: {run.feedback.interpreter_source}</small>
                </div>
              )}
            </section>

            {run?.evidence.length ? (
              <section className="panel evidence-panel">
                <div className="panel-heading">
                  <div><span className="step-number">02</span><h2>Anchor the evidence</h2></div>
                  <span className="panel-status panel-status-good">3 MATCHES</span>
                </div>
                <div className="evidence-list">
                  {run.evidence.map((item, index) => (
                    <article className={index === 0 ? 'evidence-primary' : ''} key={item.segment_id}>
                      <div className="time-code"><Clock3 size={13} /> {formatTime(item.time_range.start_seconds)}–{formatTime(item.time_range.end_seconds)}</div>
                      <div><strong>{item.visual_summary}</strong><p>“{item.transcript}”</p><small>{item.source}</small></div>
                      <span className="score">{Math.round(item.score * 100)}%</span>
                    </article>
                  ))}
                </div>
                {run.state === 'EVIDENCE_ANCHORED' && (
                  <button className="primary-button" onClick={() => void action(() => api.previews(run.run_id))} disabled={busy}>
                    <Film size={16} /> {busy ? 'Rendering A/B…' : 'Render constrained previews'}
                  </button>
                )}
              </section>
            ) : null}

            {run?.candidates.length ? (
              <section className="panel">
                <div className="panel-heading">
                  <div><span className="step-number">03</span><h2>Choose the approved patch</h2></div>
                  <span className="panel-status">HUMAN GATE</span>
                </div>
                <p className="section-copy">Both options preserve timing and audio. Only the center crop strength changes.</p>
                <div className="candidate-grid">
                  {run.candidates.map((candidate) => (
                    <CandidateCard
                      key={candidate.candidate_id}
                      candidate={candidate}
                      approved={run.spec?.approved_candidate.candidate_id === candidate.candidate_id}
                      busy={busy || Boolean(run.spec)}
                      onApprove={() => void action(() => api.approve(run.run_id, candidate.candidate_id))}
                    />
                  ))}
                </div>
              </section>
            ) : null}

            {run?.spec && (
              <section className="panel spec-panel">
                <div className="panel-heading">
                  <div><span className="step-number">04</span><h2>Verify the revision</h2></div>
                  <span className="panel-status panel-status-good"><LockKeyhole size={12} /> SPEC FROZEN</span>
                </div>
                <div className="hash-block"><Fingerprint size={17} /><div><span>SHA-256 REVISION SPEC</span><code>{run.spec.spec_hash}</code></div></div>
                <p className="section-copy">Try the intentional failure first. v2 keeps the punch-in but removes the locked CTA. v3 repairs it.</p>
                <div className="version-actions">
                  <button className="danger-button" onClick={() => void action(() => api.demoVersion(run.run_id, 'v2'))} disabled={busy || run.state === 'READY'}>
                    <ShieldAlert size={16} /> Verify demo v2
                  </button>
                  <button className="primary-button" onClick={() => void action(() => api.demoVersion(run.run_id, 'v3'))} disabled={busy || run.state === 'HUMAN_APPROVED'}>
                    <FileCheck2 size={16} /> Verify repaired v3
                  </button>
                  <button className="quiet-button" onClick={() => fileInput.current?.click()} disabled={busy || run.state === 'READY'}>
                    <Upload size={15} /> Upload MP4
                  </button>
                  <input ref={fileInput} hidden type="file" accept="video/mp4" onChange={(event) => uploadManual(event.target.files?.[0])} />
                </div>
              </section>
            )}

            {run?.proof && (
              <section className={`gate-panel gate-${run.proof.publish_allowed ? 'ready' : 'blocked'}`}>
                <div className="gate-summary">
                  <div className="gate-icon">{run.proof.publish_allowed ? <CheckCircle2 /> : <ShieldAlert />}</div>
                  <div><span>RELEASE GATE · {run.proof.version_label.toUpperCase()}</span><h2>{run.proof.publish_allowed ? 'PUBLISH READY' : 'PUBLISH BLOCKED'}</h2><p>{run.proof.publish_allowed ? 'Every approved and locked invariant passed.' : 'A locked invariant regressed. Approval cannot be reused.'}</p></div>
                </div>
                <div className="check-list">
                  {run.proof.checks.map((check) => (
                    <article key={check.check_id}>
                      <div><strong>{check.label}</strong><span>{formatTime(check.evidence_time_range.start_seconds)}–{formatTime(check.evidence_time_range.end_seconds)}</span></div>
                      {check.failure_code && <code>{check.failure_code}</code>}
                      <VerdictPill verdict={check.verdict} />
                    </article>
                  ))}
                </div>
              </section>
            )}
          </div>

          <aside className="trace-column">
            <section className="panel sticky-panel">
              <div className="trace-heading"><span>PROOF TRACE</span><span className="live-dot" /></div>
              <div className="trace-list">
                {(run?.events ?? []).map((event) => (
                  <div className="trace-event" key={event.sequence}>
                    <span className="trace-node"><Check size={11} /></span>
                    <div><strong>{event.state.replaceAll('_', ' ')}</strong><p>{event.message}</p><small>{new Date(event.occurred_at).toLocaleTimeString()}</small></div>
                  </div>
                ))}
                {!run && <div className="empty-trace"><Search size={22} /><p>Evidence and verification events will appear here.</p></div>}
              </div>
              <div className="integration-box">
                <span className="micro-label">RUNTIME TRUTH</span>
                <dl>
                  <div><dt>Mode</dt><dd>{run?.mode ?? 'FIXTURE'}</dd></div>
                  <div><dt>Interpreter</dt><dd>{run?.feedback?.interpreter_source ?? 'Not run'}</dd></div>
                  <div><dt>Evidence</dt><dd>{run?.evidence[0]?.source ?? 'Not queried'}</dd></div>
                  <div><dt>Verdict owner</dt><dd>OpenCV + FFmpeg</dd></div>
                </dl>
              </div>
              {run && <a className="api-link" href={`/api/runs/${run.run_id}`} target="_blank" rel="noreferrer">Inspect raw run JSON <ChevronRight size={14} /></a>}
            </section>
          </aside>
        </section>
      </main>
      <footer><span>RevisionProof / v2</span><span>Evidence before confidence.</span></footer>
    </div>
  )
}
