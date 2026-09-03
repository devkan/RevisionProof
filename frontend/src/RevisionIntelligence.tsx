import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, BookOpen, Check, CheckCircle2, ChevronLeft, ChevronRight, LockKeyhole, Pause, Play, RefreshCw, Save, X, ZoomIn } from 'lucide-react'
import { api } from './api'
import type { ChangeWindow, EditMemorySearch, RunSnapshot, RuntimeStatus, SearchEngine } from './types'

function timeLabel(seconds: number) {
  return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`
}

const WINDOW_LABEL = { requested: 'Requested edit', unchanged: 'Unchanged', review: 'Review needed' }

export function ChangeMap({ run }: { run: RunSnapshot }) {
  const map = run.change_map
  const [selected, setSelected] = useState<ChangeWindow | null>(null)
  const [comparing, setComparing] = useState(false)
  if (!map) return null
  const active = selected ?? map.windows.find((w) => w.status === 'review') ?? map.windows.find((w) => w.requested) ?? map.windows[0]
  const flags = map.windows.filter((w) => w.status === 'review').length
  return (
    <section className="change-map" aria-labelledby="change-map-title">
      <div className="intelligence-heading">
        <div><span className="eyebrow">REVISION CHANGE MAP</span><h3 id="change-map-title">See exactly where to look.</h3></div>
        {map.status === 'ready' && <span className={`map-summary ${flags ? 'has-flags' : ''}`}>{flags ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}{flags ? `${flags} seconds to review` : 'No sampled review flags'}</span>}
      </div>
      {map.status === 'unavailable' ? <p className="intelligence-notice" role="status">{map.message}</p> : <>
        <div className="map-legend" aria-label="Timeline legend"><span><i className="legend-requested" />Requested edit</span><span><i className="legend-unchanged" />Unchanged</span><span><i className="legend-review" />Review needed</span></div>
        <div className="map-timeline" aria-label="One-second video comparison windows">
          {map.windows.map((window) => <button type="button" key={window.second}
            className={`map-window map-${window.status} ${active?.second === window.second ? 'map-selected' : ''}`}
            aria-pressed={active?.second === window.second}
            aria-label={`${timeLabel(window.second)} to ${timeLabel(window.second + 1)}: ${WINDOW_LABEL[window.status]}`}
            onClick={() => setSelected(window)}>
            <span>{timeLabel(window.second)}</span>
            {window.status === 'requested' ? <ZoomIn size={17} /> : window.status === 'review' ? <AlertTriangle size={17} /> : <Check size={15} />}
          </button>)}
        </div>
        {active && <div className={`map-detail map-detail-${active.status}`} aria-live="polite">
          <div><strong>{timeLabel(active.second)}–{timeLabel(Math.min(active.second + 1, map.duration_seconds))} · {WINDOW_LABEL[active.status]}</strong>
            <p>{active.status === 'review' ? 'The observed result differs from the approved edit, protected video content, or audio. Watch this moment.' : active.requested ? 'This moment is inside your approved punch-in. Compare the crop side by side.' : 'These samples match the expected unchanged video.'}</p></div>
          <button type="button" className="secondary-button" disabled={!run.generated_version_url} onClick={() => setComparing(true)}><ZoomIn size={18} />Compare this moment</button>
        </div>}
        <details className="intelligence-technical"><summary>How this map was measured</summary><p>{map.message}</p><p>{map.source} · {map.windows.reduce((n, w) => n + w.sample_count, 0)} frame pairs · 1-second windows</p>
          {active && <dl><div><dt>Visual change</dt><dd>{(active.visual_delta * 100).toFixed(2)}%</dd></div><div><dt>Difference from expected edit</dt><dd>{(active.residual_delta * 100).toFixed(2)}%</dd></div><div><dt>Audio level difference</dt><dd>{active.audio_delta_db.toFixed(2)} dB</dd></div></dl>}
        </details>
      </>}
      {comparing && active && run.generated_version_url && <ComparisonDialog original={run.asset.source_url} revised={run.generated_version_url} second={active.second} duration={map.duration_seconds} onClose={() => setComparing(false)} />}
    </section>
  )
}

export function ComparisonDialog({ original, revised, second, duration, onClose }: { original: string; revised: string; second: number; duration: number; onClose: () => void }) {
  const a = useRef<HTMLVideoElement>(null)
  const b = useRef<HTMLVideoElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const [position, setPosition] = useState(second)
  const [playing, setPlaying] = useState(false)
  const [playError, setPlayError] = useState<string | null>(null)
  useEffect(() => {
    const element = dialog.current
    const previousFocus = document.activeElement as HTMLElement | null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    element?.showModal()
    return () => { element?.close(); document.body.style.overflow = previousOverflow; previousFocus?.focus() }
  }, [])
  function seek(value: number) {
    const next = Math.max(0, Math.min(duration - 0.05, value))
    for (const video of [a.current, b.current]) if (video) { video.pause(); video.currentTime = next }
    setPosition(next); setPlaying(false)
  }
  async function toggle() {
    setPlayError(null)
    if (playing) { a.current?.pause(); b.current?.pause(); setPlaying(false); return }
    if (a.current && b.current) b.current.currentTime = a.current.currentTime
    try { await Promise.all([a.current?.play(), b.current?.play()]); setPlaying(true) }
    catch { a.current?.pause(); b.current?.pause(); setPlaying(false); setPlayError('Playback could not start. Try again once both videos load.') }
  }
  return <dialog ref={dialog} className="comparison-dialog" aria-labelledby="comparison-title" onCancel={(event) => { event.preventDefault(); onClose() }} onClick={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <div className="comparison-content">
      <header><div><span className="eyebrow">SIDE-BY-SIDE COMPARISON</span><h2 id="comparison-title">Original and revised · {timeLabel(position)}</h2></div><button type="button" className="secondary-button" onClick={onClose} aria-label="Close video comparison"><X size={20} /></button></header>
      <div className="comparison-players"><figure><figcaption>Original</figcaption><video ref={a} src={original} muted playsInline preload="auto" onLoadedMetadata={() => { if (a.current) a.current.currentTime = second }} onTimeUpdate={() => { if (a.current && playing) { setPosition(a.current.currentTime); if (b.current && Math.abs(b.current.currentTime - a.current.currentTime) > 0.15) b.current.currentTime = a.current.currentTime } }} onEnded={() => { b.current?.pause(); setPlaying(false) }} /></figure><figure><figcaption>Revised</figcaption><video ref={b} src={revised} muted playsInline preload="auto" onLoadedMetadata={() => { if (b.current) b.current.currentTime = second }} /></figure></div>
      <div className="comparison-controls"><button className="secondary-button" onClick={() => seek(position - 1)} aria-label="Previous second"><ChevronLeft size={18} /></button><button className="primary-button" onClick={() => void toggle()}>{playing ? <Pause size={18} /> : <Play size={18} />}{playing ? 'Pause both' : 'Play both'}</button><button className="secondary-button" onClick={() => seek(position + 1)} aria-label="Next second"><ChevronRight size={18} /></button><label htmlFor="comparison-seek">Position</label><input id="comparison-seek" type="range" min={0} max={Math.max(0, duration - 0.05)} step={0.05} value={position} onChange={(e) => seek(Number(e.target.value))} /></div>
      <p className="input-help">Both players are muted and synchronized. Use the full video player to review audio.</p>{playError && <p role="alert">{playError}</p>}
    </div>
  </dialog>
}

export function EditMemory({ run, disabled, runtime }: { run: RunSnapshot; disabled: boolean; runtime?: RuntimeStatus }) {
  // Follow newer server snapshots until the user explicitly reruns the search.
  const [searchResult, setResult] = useState<EditMemorySearch | undefined>()
  const result = searchResult ?? run.edit_memory
  const [engine, setEngine] = useState<SearchEngine>(run.edit_memory?.requested_engine ?? 'hnsw')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function search() {
    setLoading(true); setError(null)
    try { setResult(await api.searchMemory(run.run_id, engine)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Search unavailable') }
    finally { setLoading(false) }
  }
  const readOnly = runtime?.memory_save_policy === 'read_only'
  return <details className="edit-memory memory-compact" aria-busy={loading} onToggle={(event) => { if (event.currentTarget.open && !result && !loading) void search() }}>
    <summary><BookOpen size={18} aria-hidden="true" /><span>Past approved edits <small>Optional reference{result?.matches.length ? ` · ${result.matches.length} found` : ''}</small></span></summary>
    <div className="memory-content">
    <p className="input-help">See what worked for a similar request before choosing A or B. Your current edit is always reviewed separately.</p>
    {loading && <div className="inline-processing" role="status"><span className="spinner" />Finding similar approved edits…</div>}
    {error && <p className="intelligence-notice" role="alert">{error}</p>}
    {!loading && result?.status === 'empty' && <div className="memory-empty"><p><strong>{result.collection_size ? 'No similar approved edits yet.' : 'No saved edits yet.'}</strong></p><p>{readOnly ? 'Saving past edits is turned off in this public demo. Continue with your new A/B previews.' : 'After checking the full video, approve delivery and choose “Save approved edit”. That choice can help with your next request.'}</p></div>}
    {!loading && result?.status === 'unavailable' && <p className="intelligence-notice" role="status">{result.message}</p>}
    {!loading && result?.matches.map((match) => <article className="memory-match" key={match.memory_id}><div><span className="memory-verified"><CheckCircle2 size={16} />Verified + human approved</span><h4>{match.intent}</h4><p>“{match.target_phrase}” · {match.duration_seconds}s center punch-in</p></div><div className="memory-recommendation"><strong>Option {match.candidate_id}</strong><span>{match.scale.toFixed(2)}× crop</span><small>Similarity {match.similarity.toFixed(3)}</small></div></article>)}
    {result?.matches.length ? <p className="input-help">A reference, not an automatic choice. Compare fresh A/B previews before selecting.</p> : null}
    {(error || result?.status === 'unavailable') && <button className="secondary-button" disabled={loading || disabled} onClick={() => void search()}>Retry lookup</button>}
    {Boolean(result?.collection_size) && <details className="intelligence-technical"><summary>How references were found</summary><div className="memory-search-controls"><label htmlFor="memory-engine">Search method</label><select id="memory-engine" value={engine} onChange={(event) => setEngine(event.target.value as SearchEngine)} disabled={loading || disabled}><option value="hnsw">Fast search · HNSW</option><option value="exact">Exact comparison</option><option value="qbit">Adjustable precision · QBit</option></select><button className="secondary-button" onClick={() => void search()} disabled={loading || disabled}><RefreshCw size={16} />{loading ? 'Searching…' : 'Refresh references'}</button></div>{result && <><p>{result.message}</p><dl><div><dt>Method used</dt><dd>{result.actual_engine.toUpperCase()}{result.index_verified ? ' · index verified' : ''}</dd></div><div><dt>Saved edits</dt><dd>{result.collection_size}</dd></div></dl><p className="input-help">{result.source} · Similarity describes how closely requests match, not the chance that an edit will succeed.</p></>}</details>}
    </div>
  </details>
}

export function SaveApprovedMemory({ run, runtime, disabled, onSaved }: { run: RunSnapshot; runtime: RuntimeStatus; disabled: boolean; onSaved: () => void }) {
  const [workspaceKey, setWorkspaceKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const writable = runtime.memory_save_policy !== 'read_only'
  const ready = run.delivery_approved && run.proof?.publish_allowed && run.change_map?.status === 'ready' && !run.change_map.windows.some((w) => w.status === 'review')
  async function save() {
    setSaving(true); setError(null)
    const key = workspaceKey; setWorkspaceKey('')
    try { await api.saveMemory(run.run_id, key); onSaved() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this edit') }
    finally { setSaving(false) }
  }
  return <div className="save-memory" aria-busy={saving}>
    <div><h3>{run.memory_saved ? 'Saved to approved edit memory.' : 'Reuse this decision next time.'}</h3><p>{run.memory_saved ? 'Future similar requests can find this verified edit.' : !writable ? 'This public demo has a read-only library. Workspace owners can enable private saves.' : !ready ? 'Available after final delivery approval, with no Change Map review flags.' : 'Save the edit settings, not the video. Nothing is applied automatically.'}</p></div>
    {!run.memory_saved && writable && <div className="memory-save-controls">{runtime.memory_save_policy === 'operator_key' && <label>Private workspace key<input type="password" autoComplete="off" value={workspaceKey} onChange={(event) => setWorkspaceKey(event.target.value)} disabled={!ready || saving || disabled} /></label>}<button className="secondary-button" onClick={() => void save()} disabled={!ready || saving || disabled || (runtime.memory_save_policy === 'operator_key' && workspaceKey.length < 32)}>{saving ? <span className="spinner" /> : ready ? <Save size={18} /> : <LockKeyhole size={18} />}{saving ? 'Saving approved edit…' : 'Save approved edit'}</button></div>}
    {runtime.memory_save_policy === 'local_rehearsal' && <small>Local rehearsal only. This library resets when the server restarts.</small>}{error && <p role="alert" className="intelligence-notice">{error}</p>}
  </div>
}
