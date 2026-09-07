import { useRef, useState } from 'react'
import { Captions, Check, Database, Film, Gauge, ImagePlus, Languages, Plus, Search, Scissors, Sparkles, Trash2, Type, Volume2, VolumeX, ZoomIn } from 'lucide-react'
import { api } from './api'
import { EDIT_LABELS, editDetail, editSummary, operation, outputDuration, planProblem, seconds } from './editing'
import type { EditInterpretation, EditOperation, EditPlan, ExecutionMode, SceneSearchHit, SceneSearchResult, TimeRange, TranscriptionLanguage } from './types'

const EDITS = [
  { kind: 'zoom', icon: ZoomIn, hint: 'Bring a moment closer' },
  { kind: 'text', icon: Type, hint: 'A title, message or website' },
  { kind: 'cut', icon: Scissors, hint: 'Delete a time range' },
  { kind: 'remove_silence', icon: VolumeX, hint: 'Review pauses before cutting' },
  { kind: 'speed', icon: Gauge, hint: 'Slow down or speed up a section' },
  { kind: 'volume', icon: Volume2, hint: 'Mute, lower or raise a section' },
  { kind: 'logo', icon: ImagePlus, hint: 'Upload an image and place it' },
] as const

const HAS_TIME = /(\d+(?:\.\d+)?)\s*(?:초|s|seconds?)?\s*(?:[-–—~]|부터|to)\s*(\d+(?:\.\d+)?)/i

export function RequestDraft({ text, onText, duration, disabled, onApply, onBusy, sourceFile, assetId, mode, onSceneSelect }: {
  text: string; onText: (text: string) => void; duration: number; disabled: boolean
  onApply: (plan: EditPlan) => void; onBusy: (busy: boolean) => void
  sourceFile?: File; assetId?: string; mode?: ExecutionMode
  onSceneSelect: (selection: { searchId: string; hit: SceneSearchHit } | null) => void
}) {
  const [draft, setDraft] = useState<EditInterpretation | null>(null)
  const [draftText, setDraftText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [smart, setSmart] = useState(false)
  const [sceneQuery, setSceneQuery] = useState('')
  const [sceneResult, setSceneResult] = useState<SceneSearchResult | null>(null)
  const [selectedScene, setSelectedScene] = useState<SceneSearchHit | null>(null)
  const hasExplicitTime = HAS_TIME.test(text)
  const [manualStart, setManualStart] = useState<number | ''>('')
  const [manualEnd, setManualEnd] = useState<number | ''>('')
  const manualRange = typeof manualStart === 'number' && typeof manualEnd === 'number' && manualEnd > manualStart && manualEnd <= duration ? { start_seconds: manualStart, end_seconds: manualEnd } : undefined
  const hasManualTime = hasExplicitTime || Boolean(manualRange)
  async function findScenes() {
    setLoading(true); onBusy(true); setError(null); setSceneResult(null); setSelectedScene(null); onSceneSelect(null)
    try { setSceneResult(await api.searchScenes(sceneQuery, sourceFile, sourceFile ? undefined : assetId)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Scene search could not finish. Enter the time manually instead.') }
    finally { setLoading(false); onBusy(false) }
  }
  async function interpret() {
    if (!smart && !hasManualTime) { setError('Smart scene finder is off. Enter the scene start and end time.'); return }
    if (smart && !selectedScene) { setError('Find a scene and choose one result before creating the edit draft.'); return }
    setLoading(true); onBusy(true); setError(null); setDraft(null)
    try { setDraft(await api.interpretEdit(text, duration, selectedScene ? { start_seconds: selectedScene.start_seconds, end_seconds: selectedScene.end_seconds } : manualRange)); setDraftText(text) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not prepare a draft. Use the edit buttons below.') }
    finally { setLoading(false); onBusy(false) }
  }
  const current = draft && draftText === text
  return <div className="feedback-field request-draft">
    <label className="smart-toggle"><input type="checkbox" checked={smart} disabled={disabled || loading} onChange={event => { const checked = event.target.checked; setSmart(checked); setError(null); setSceneResult(null); setSelectedScene(null); onSceneSelect(null) }} /><span><strong>Smart scene finder</strong><small>{smart ? 'Find a scene without entering its time.' : 'Off · enter the scene start and end time yourself.'}</small></span></label>
    {smart && <section className="smart-search-panel">
      <div className="smart-cost"><Database size={18} /><p><strong>{mode === 'LIVE' ? 'Uses Google AI and ClickHouse credits' : 'Local rehearsal · no cloud credits used'}</strong><span>The video is sampled and indexed only when you press Find scenes.</span></p></div>
      <div className="smart-search-controls"><label htmlFor="scene-query">Scene to find<input id="scene-query" value={sceneQuery} maxLength={500} disabled={disabled || loading} placeholder="e.g., a close-up of the dashboard chart" onChange={event => { setSceneQuery(event.target.value); setSceneResult(null); setSelectedScene(null); onSceneSelect(null) }} /></label><button type="button" className="secondary-button" disabled={disabled || loading || sceneQuery.trim().length < 2} onClick={() => void findScenes()}>{loading ? <span className="spinner" /> : <Search size={17} />}{loading ? 'Finding…' : 'Find scenes'}</button></div>
      {sceneResult && <div className="scene-results" aria-live="polite"><div className="scene-results-heading"><strong>Choose the scene to edit</strong><small>{sceneResult.segments_indexed} segments indexed · {sceneResult.source === 'mcp-clickhouse.run_query' ? 'ClickHouse search' : 'local rehearsal'}</small></div>{sceneResult.matches.length ? sceneResult.matches.map(hit => <button type="button" key={hit.segment_id} className={selectedScene?.segment_id === hit.segment_id ? 'selected' : ''} onClick={() => { setSelectedScene(hit); onSceneSelect({ searchId: sceneResult.search_id, hit }); setError(null) }}><span><strong>{hit.start_seconds.toFixed(1)}–{hit.end_seconds.toFixed(1)}s</strong><small>{Math.round(hit.score * 100)}% match</small></span><p>{hit.visual_summary}</p>{selectedScene?.segment_id === hit.segment_id && <Check size={18} />}</button>) : <p className="input-help">No matching scene was returned. Turn Smart scene finder off and enter the time.</p>}</div>}
    </section>}
    {!smart && <div className="manual-scene-range"><strong>Scene time <small>Required unless the request includes a range</small></strong><div><label>Start (s)<input type="number" min={0} max={duration} step={0.1} value={manualStart} placeholder="4" disabled={disabled || loading} onChange={event => setManualStart(event.target.value === '' ? '' : event.target.valueAsNumber)} /></label><label>End (s)<input type="number" min={0.1} max={duration} step={0.1} value={manualEnd} placeholder="10" disabled={disabled || loading} onChange={event => setManualEnd(event.target.value === '' ? '' : event.target.valueAsNumber)} /></label></div></div>}
    <label htmlFor="feedback">Describe your edit <small>Optional · English or Korean</small></label>
    <textarea id="feedback" value={text} maxLength={2000} disabled={disabled || loading}
      placeholder={'Zoom in from 4 to 10 seconds and show "AI, made practical." at the bottom.'}
      onChange={e => { onText(e.target.value); setError(null); setDraft(null) }} aria-describedby="request-help" />
    <p id="request-help" className={`input-help ${!smart && text.trim() && !hasManualTime ? 'input-help-error' : ''}`}>{smart ? selectedScene ? `Selected scene: ${selectedScene.start_seconds.toFixed(1)}–${selectedScene.end_seconds.toFixed(1)}s. This time will be used in the editable draft.` : 'Find and choose a scene above. Put exact display words in quotes.' : hasManualTime ? 'Scene time is ready. Put exact display words in quotes.' : 'Enter both times above, or include a range such as "4–10 seconds" in the request.'}</p>
    <button type="button" className="secondary-button" disabled={disabled || loading || text.trim().length < 2 || (!smart && !hasManualTime) || (smart && !selectedScene)} onClick={() => void interpret()}>
      {loading ? <span className="spinner" /> : <Sparkles size={18} />}{loading ? 'Preparing an editable draft…' : 'Turn request into edit plan'}
    </button>
    {error && <p className="upload-warning" role="alert">{error}</p>}
    {current && <div className="draft-result" aria-live="polite">
      <strong>Check this draft before using it</strong>
      <ul>{draft.plan.operations.map((op, i) => <li key={i}>{editSummary(op)}</li>)}</ul>
      {draft.warnings.map((warning, i) => <p key={i} className="upload-warning">{warning}</p>)}
      {!draft.plan.operations.length && <p>No supported edit was found. Choose an edit below and fill in its details.</p>}
      <button type="button" className="primary-button" disabled={disabled || !draft.plan.operations.length} onClick={() => { onApply(draft.plan); setDraft(null) }}>
        <Check size={17} />{draft.warnings.length ? 'Use only these listed edits' : 'Use draft in edit controls'}
      </button>
    </div>}
  </div>
}

export function EditComposer({ duration, operations, onChange, disabled, onSeek, sourceFile, assetId, mode, logoMaxBytes, onBusy, defaultRange }: {
  duration: number; operations: EditOperation[]; onChange: (ops: EditOperation[]) => void
  disabled: boolean; onSeek: (time: number) => void; sourceFile?: File; assetId?: string
  mode?: ExecutionMode; logoMaxBytes: number; onBusy: (busy: boolean) => void
  defaultRange?: TimeRange
}) {
  const logoInput = useRef<HTMLInputElement>(null)
  const [language, setLanguage] = useState<TranscriptionLanguage>('auto')
  const [toolBusy, setToolBusy] = useState<'logo' | 'subtitles' | null>(null)
  const [toolMessage, setToolMessage] = useState<string | null>(null)
  const [toolError, setToolError] = useState<string | null>(null)
  function add(kind: EditOperation['kind']) {
    if (kind === 'logo') { logoInput.current?.click(); return }
    let start = defaultRange?.start_seconds ?? 0, end = defaultRange?.end_seconds ?? Math.min(4, duration)
    if (kind === 'remove_silence') end = duration
    if (kind === 'subtitle') {
      const last = operations.filter(op => op.kind === 'subtitle').at(-1)
      start = last ? Math.min(last.end, duration - 0.1) : 0
      end = Math.min(start + 3, duration)
    }
    onChange([...operations, operation(kind, start, end)])
  }
  async function uploadLogo(file?: File) {
    if (!file || disabled || toolBusy) return
    setToolError(null); setToolMessage(null)
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) { setToolError('Choose a PNG, JPG, or WebP logo.'); return }
    if (!file.size || file.size > logoMaxBytes) { setToolError(`Logo must be no larger than ${logoMaxBytes / 1048576} MiB.`); return }
    setToolBusy('logo'); onBusy(true)
    try {
      const asset = await api.uploadLogo(file)
      const logo = { ...operation('logo', 0, duration), asset_id: asset.asset_id, asset_sha256: asset.sha256 }
      onChange([...operations, logo])
      setToolMessage(`${file.name} uploaded. Choose its time and corner below.`)
    } catch (reason) {
      setToolError(reason instanceof Error ? reason.message : 'The logo could not be uploaded.')
    } finally { setToolBusy(null); onBusy(false) }
  }
  async function generateSubtitles() {
    if (disabled || toolBusy) return
    setToolError(null); setToolMessage(null); setToolBusy('subtitles'); onBusy(true)
    try {
      const result = await api.transcribe(language, sourceFile, sourceFile ? undefined : assetId)
      if (!result.cues.length) { setToolMessage(result.warnings[0] ?? 'No clear speech was detected.'); return }
      const other = operations.filter(op => op.kind !== 'subtitle')
      const available = Math.max(0, 24 - other.length)
      if (!available) { setToolError('Remove at least one edit before adding automatic subtitles.'); return }
      const subtitles = result.cues.slice(0, available).map(cue => ({ ...operation('subtitle', cue.start, cue.end, cue.text), position: 'bottom' as const }))
      onChange([...other, ...subtitles])
      const detected = result.detected_languages.length ? result.detected_languages.map(value => value === 'ko' ? 'Korean' : value === 'en' ? 'English' : 'other').join(' + ') : 'no language'
      const replaced = operations.some(op => op.kind === 'subtitle') ? ' Existing timed subtitles were replaced.' : ''
      setToolMessage(`${subtitles.length} subtitle cue${subtitles.length === 1 ? '' : 's'} added (${detected}). Review every word and time below.${replaced}${result.cues.length > available ? ' Some cues exceeded the 24-edit limit.' : ''}`)
    } catch (reason) {
      setToolError(reason instanceof Error ? reason.message : 'Speech could not be transcribed.')
    } finally { setToolBusy(null); onBusy(false) }
  }
  function change(index: number, update: Partial<EditOperation>) {
    onChange(operations.map((op, i) => i === index ? { ...op, ...update } : op))
  }
  function example(which: 'intro' | 'subtitles' | 'pace') {
    if (which === 'intro') {
      const start = duration >= 10 ? 4 : Math.round(duration * 0.4 * 10) / 10
      onChange([operation('zoom', start, Math.min(10, duration)), operation('text', start, Math.min(10, duration), 'AI, made practical.')])
    } else if (which === 'subtitles') {
      const middle = Math.round(duration / 2 * 10) / 10
      onChange([operation('subtitle', 0, middle, 'Meet KANAPP.'), operation('subtitle', middle, duration, 'AI, made practical.')])
    } else {
      onChange([operation('remove_silence', 0, duration)])
    }
  }
  const subtitleRows = operations.map((op, index) => ({ op, index })).filter(({ op }) => op.kind === 'subtitle')
  const otherRows = operations.map((op, index) => ({ op, index })).filter(({ op }) => op.kind !== 'subtitle')
  return <div className="edit-composer">
    <div className="composer-heading"><div><span className="eyebrow">BUILD YOUR EDIT</span><h3>What would you like to change?</h3></div><span className="input-help">Combine up to 24 edits</span></div>
    <div className="speech-subtitles">
      <div><Languages size={22} /><div><strong>Generate subtitles from speech</strong><p>Google Gemini transcribes the audio. It does not translate it. You review and edit every cue before previewing.</p></div></div>
      <div className="speech-controls">
        <label>Spoken language<select value={language} disabled={disabled || Boolean(toolBusy)} onChange={event => setLanguage(event.target.value as TranscriptionLanguage)}><option value="auto">Auto detect Korean + English</option><option value="ko">Korean</option><option value="en">English</option><option value="mixed">Korean + English mixed</option></select></label>
        <button type="button" className="secondary-button" onClick={() => void generateSubtitles()} disabled={disabled || Boolean(toolBusy) || mode !== 'LIVE'}>{toolBusy === 'subtitles' ? <span className="spinner" /> : <Captions size={18} />}{toolBusy === 'subtitles' ? 'Listening…' : 'Generate editable subtitles'}</button>
        <button type="button" className="secondary-button" onClick={() => add('subtitle')} disabled={disabled || Boolean(toolBusy) || operations.length >= 24}><Plus size={17} />Add one manually</button>
      </div>
      {mode !== 'LIVE' && <p className="input-help">Automatic speech transcription is available in LIVE mode. Timed subtitles below still work manually.</p>}
    </div>
    <input ref={logoInput} hidden type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" aria-label="Upload logo image" onChange={event => { void uploadLogo(event.target.files?.[0]); event.target.value = '' }} />
    {toolError && <p className="upload-warning" role="alert">{toolError}</p>}
    {toolMessage && <p className="tool-success" role="status">{toolMessage}</p>}
    <div className="edit-type-grid">{EDITS.map(({ kind, icon: Icon, hint }) => <button type="button" className="edit-type" key={kind} onClick={() => add(kind)} disabled={disabled || Boolean(toolBusy) || operations.length >= 24}><Icon size={21} /><strong>{EDIT_LABELS[kind]}</strong><span>{hint}</span><Plus size={15} className="edit-type-plus" /></button>)}</div>
    <details className="edit-examples" open={!operations.length}>
      <summary>Need an idea? Start with a ready-to-edit example</summary>
      <div className="example-grid">
        <button type="button" disabled={disabled} onClick={() => example('intro')}><strong>Promo highlight</strong><span>Zoom + “AI, made practical.” at the bottom</span></button>
        <button type="button" disabled={disabled} onClick={() => example('subtitles')}><strong>Two timed subtitles</strong><span>Show one line, then replace it with the next</span></button>
        <button type="button" disabled={disabled} onClick={() => example('pace')}><strong>Tighten the pacing</strong><span>Find quiet pauses, then choose what to cut</span></button>
      </div>
      <p className="input-help">Examples replace the current edit list. Change the wording and times below.</p>
    </details>
    {operations.length > 0 && <div className="edit-list">
      <p className="edit-time-guidance">All times refer to the <strong>original video</strong>. Captions stay attached to their scenes after cuts.</p>
      {subtitleRows.length > 0 && <section className="subtitle-editor" aria-labelledby="subtitle-editor-title"><header><div><Captions size={19} /><div><strong id="subtitle-editor-title">Subtitles</strong><small>{subtitleRows.length} editable cue{subtitleRows.length === 1 ? '' : 's'} · review words and timing</small></div></div><button type="button" className="secondary-button" onClick={() => add('subtitle')} disabled={disabled || operations.length >= 24}><Plus size={16} />Add cue</button></header><div className="subtitle-table">{subtitleRows.map(({ op, index }, cueIndex) => <div className="subtitle-row" key={index}><span className="subtitle-number">{cueIndex + 1}</span><label><span>Start</span><input aria-label={`Subtitle ${cueIndex + 1} start`} type="number" min={0} max={duration} step={0.1} value={Number.isFinite(op.start) ? op.start : ''} onChange={e => change(index, { start: e.target.valueAsNumber })} /></label><label><span>End</span><input aria-label={`Subtitle ${cueIndex + 1} end`} type="number" min={0.1} max={duration} step={0.1} value={Number.isFinite(op.end) ? op.end : ''} onChange={e => change(index, { end: e.target.valueAsNumber })} /></label><label className="subtitle-text"><span>Words</span><input aria-label={`Subtitle ${cueIndex + 1} words`} maxLength={160} value={op.text} onChange={e => change(index, { text: e.target.value })} /></label><label><span>Position</span><select aria-label={`Subtitle ${cueIndex + 1} position`} value={op.position} onChange={e => change(index, { position: e.target.value as EditOperation['position'] })}><option value="bottom">Bottom</option><option value="top">Top</option><option value="center">Center</option></select></label><div className="subtitle-actions"><button type="button" className="icon-button" onClick={() => onSeek(op.start)} aria-label={`Watch subtitle ${cueIndex + 1}`}><Film size={17} /></button><button type="button" className="icon-button" onClick={() => onChange(operations.filter((_, i) => i !== index))} aria-label={`Remove subtitle ${cueIndex + 1}`}><Trash2 size={17} /></button></div></div>)}</div></section>}
      {otherRows.map(({ op, index }) => <fieldset className="edit-card" key={index} disabled={disabled}>
        <legend><span>{String(index + 1).padStart(2, '0')}</span> {EDIT_LABELS[op.kind]}</legend>
        <button className="icon-button remove-edit" type="button" onClick={() => onChange(operations.filter((_, i) => i !== index))} aria-label={`Remove edit ${index + 1}`}><Trash2 size={18} /></button>
        <div className="edit-fields">
          <label>Start (s)<input type="number" min={0} max={duration} step={0.1} value={Number.isFinite(op.start) ? op.start : ''} onChange={e => change(index, { start: e.target.valueAsNumber })} /></label>
          <label>End (s)<input type="number" min={0.1} max={duration} step={0.1} value={Number.isFinite(op.end) ? op.end : ''} onChange={e => change(index, { end: e.target.valueAsNumber })} /></label>
          <button type="button" className="secondary-button" disabled={!Number.isFinite(op.start)} onClick={() => onSeek(op.start)}>Watch from here</button>
        </div>
        {op.kind === 'text' && <div className="caption-fields">
          <label>Exact words<textarea rows={2} maxLength={160} value={op.text} placeholder="AI, made practical." onChange={e => change(index, { text: e.target.value })} /></label>
          <label>Position<select value={op.position} onChange={e => change(index, { position: e.target.value as EditOperation['position'] })}><option value="bottom">Bottom</option><option value="top">Top</option><option value="center">Center</option><option value="top_left">Top left</option><option value="top_right">Top right</option><option value="bottom_left">Bottom left</option><option value="bottom_right">Bottom right</option></select></label>
        </div>}
        {op.kind === 'speed' && <div className="edit-fields"><label>Playback speed<select value={op.rate} onChange={e => change(index, { rate: Number(e.target.value) })}><option value={0.5}>0.5× · slow</option><option value={0.75}>0.75×</option><option value={1.25}>1.25×</option><option value={1.5}>1.5×</option><option value={2}>2× · fast</option></select></label></div>}
        {op.kind === 'volume' && <div className="edit-fields"><label>Volume change<select value={op.volume_db} onChange={e => change(index, { volume_db: Number(e.target.value) })}><option value={-60}>Mute</option><option value={-12}>Much quieter · −12 dB</option><option value={-6}>Quieter · −6 dB</option><option value={3}>Louder · +3 dB</option><option value={6}>Much louder · +6 dB</option><option value={12}>Maximum boost · +12 dB</option></select></label></div>}
        {op.kind === 'logo' && <div className="logo-fields"><img src={`/media/edit-assets/${op.asset_id}.png`} alt="Uploaded logo preview" /><label>Position<select value={op.position} onChange={e => change(index, { position: e.target.value as EditOperation['position'] })}><option value="top_left">Top left</option><option value="top_right">Top right</option><option value="bottom_left">Bottom left</option><option value="bottom_right">Bottom right</option><option value="center">Center</option></select></label></div>}
        {op.kind === 'zoom' && <p className="input-help">A fixed center zoom during this interval: 1.05× or 1.12×. The crop can cut off existing text near the edges; check the previews.</p>}
        {op.kind === 'cut' && <p className="input-help">Remove both the picture and audio in this interval. Kept sections join together.</p>}
        {op.kind === 'speed' && <p className="input-help">Picture and sound change together, while subtitles and overlays remain attached to their original scene times.</p>}
        {op.kind === 'volume' && <p className="input-help">Changes the selected audio only. Louder settings may clip if the original is already loud; compare the preview.</p>}
        {op.kind === 'logo' && <p className="input-help">The uploaded image is fixed by checksum for this review. Option A uses a smaller logo; B uses a larger logo.</p>}
        {op.kind === 'remove_silence' && <>
          <div className="edit-fields silence-fields"><label>Minimum pause (s)<input type="number" min={0.3} max={3} step={0.1} value={Number.isFinite(op.min_silence) ? op.min_silence : ''} onChange={e => change(index, { min_silence: e.target.valueAsNumber })} /></label><label>Quiet level<select value={op.threshold_db} onChange={e => change(index, { threshold_db: Number(e.target.value) })}><option value={-50}>Very quiet · −50 dB</option><option value={-40}>Quiet · −40 dB</option><option value={-30}>Low sound · −30 dB</option></select></label></div>
          <p className="input-help">Continuous music may leave no quiet pauses. We keep a small margin around sound and ask you to select each proposed cut.</p>
        </>}
      </fieldset>)}
    </div>}
    <details className="capability-guide"><summary>What can I ask for?</summary><div><p><strong>Works now:</strong> “Speed up 2–6s to 1.5×”, “Lower 0–4s by −6 dB”, upload a logo, generate Korean/English mixed subtitles, add exact text, zoom, cut a range, or find quiet pauses.</p><p><strong>Combine them:</strong> “Zoom 4–8s, add ‘AI, made practical.’ at the bottom, make 0–4s 1.25×, then mute 8–10s.” Review the generated cards before applying them.</p><p><strong>Needs an editor:</strong> moving-object tracking, removing text baked into footage, background replacement, color grading, generated scenes and music selection.</p></div></details>
  </div>
}

export function PlanReview({ plan, warnings, selected, onSelect, onPreview, onEdit, onSeek, disabled, rendered }: {
  plan: EditPlan; warnings: string[]; selected: number[]; onSelect: (indexes: number[]) => void
  onPreview: () => void; onEdit: () => void; onSeek: (time: number) => void; disabled: boolean; rendered: boolean
}) {
  const chosen = { ...plan, operations: plan.operations.filter((_, i) => selected.includes(i)) }
  const problem = planProblem(chosen)
  return <section className="workspace-section plan-review">
    <div className="section-heading"><div><span className="step-number">02</span><div><h2>Review your edit plan</h2><p>{rendered ? 'These are the edits in your previews.' : 'Only checked edits will appear in the previews.'}</p></div></div></div>
    {warnings.map((warning, i) => <p key={i} className="intelligence-notice" role="status">{warning}</p>)}
    <div className="plan-review-list">{plan.operations.map((op, i) => <div className={`plan-review-row ${selected.includes(i) ? 'chosen' : ''}`} key={i}>
      <label><input type="checkbox" checked={selected.includes(i)} disabled={disabled || rendered} onChange={() => onSelect(selected.includes(i) ? selected.filter(n => n !== i) : [...selected, i])} /><span><strong>{op.detected ? 'Quiet pause · proposed cut' : EDIT_LABELS[op.kind]}</strong><span>{editDetail(op)} · original timeline</span></span></label>
      <button type="button" className="secondary-button" onClick={() => onSeek(op.start)}>Watch original</button>
    </div>)}</div>
    <div className="plan-duration"><span>Original <strong>{seconds(plan.source_duration)}</strong></span><span>After selected edits <strong>{seconds(outputDuration(chosen))}</strong></span></div>
    {rendered && <div className="section-action-bar"><p>Want different text, timing or cuts? Adjust your edits and make fresh previews.</p><button type="button" className="secondary-button" onClick={onEdit} disabled={disabled}>Adjust edits</button></div>}
    {!rendered && <div className="section-action-bar"><div><strong>{selected.length} edit{selected.length === 1 ? '' : 's'} selected</strong><p>{problem ?? 'Watch the full previews before choosing an option.'}</p></div><button type="button" className="secondary-button" onClick={onEdit} disabled={disabled}>Edit request</button><button type="button" className="primary-button" onClick={onPreview} disabled={disabled || Boolean(problem)}><Film size={18} />Create previews</button></div>}
  </section>
}
