import { useState } from 'react'
import { Captions, Check, Film, Plus, Scissors, Sparkles, Trash2, Type, VolumeX, ZoomIn } from 'lucide-react'
import { api } from './api'
import { EDIT_LABELS, editSummary, operation, outputDuration, planProblem, seconds } from './editing'
import type { EditInterpretation, EditOperation, EditPlan } from './types'

const EDITS = [
  { kind: 'zoom', icon: ZoomIn, hint: 'Bring a moment closer' },
  { kind: 'text', icon: Type, hint: 'A title, message or website' },
  { kind: 'subtitle', icon: Captions, hint: 'Different words at each time' },
  { kind: 'cut', icon: Scissors, hint: 'Delete a time range' },
  { kind: 'remove_silence', icon: VolumeX, hint: 'Review pauses before cutting' },
] as const

export function RequestDraft({ text, onText, duration, disabled, onApply, onBusy }: {
  text: string; onText: (text: string) => void; duration: number; disabled: boolean
  onApply: (plan: EditPlan) => void; onBusy: (busy: boolean) => void
}) {
  const [draft, setDraft] = useState<EditInterpretation | null>(null)
  const [draftText, setDraftText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function interpret() {
    setLoading(true); onBusy(true); setError(null); setDraft(null)
    try { setDraft(await api.interpretEdit(text, duration)); setDraftText(text) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not prepare a draft. Use the edit buttons below.') }
    finally { setLoading(false); onBusy(false) }
  }
  const current = draft && draftText === text
  return <div className="feedback-field request-draft">
    <label htmlFor="feedback">Describe your edit <small>Optional · English or Korean</small></label>
    <textarea id="feedback" value={text} maxLength={2000} disabled={disabled || loading}
      placeholder={'4–10초를 확대하면서 ‘AI, made practical.’ 문구를 하단에 표시'}
      onChange={e => onText(e.target.value)} aria-describedby="request-help" />
    <p id="request-help" className="input-help">Use original-video times and put exact words in quotes. No time specified? The draft uses the whole video.</p>
    <button type="button" className="secondary-button" disabled={disabled || loading || text.trim().length < 2} onClick={() => void interpret()}>
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

export function EditComposer({ duration, operations, onChange, disabled, onSeek }: {
  duration: number; operations: EditOperation[]; onChange: (ops: EditOperation[]) => void
  disabled: boolean; onSeek: (time: number) => void
}) {
  function add(kind: EditOperation['kind']) {
    let start = 0, end = Math.min(4, duration)
    if (kind === 'remove_silence') end = duration
    if (kind === 'subtitle') {
      const last = operations.filter(op => op.kind === 'subtitle').at(-1)
      start = last ? Math.min(last.end, duration - 0.1) : 0
      end = Math.min(start + 3, duration)
    }
    onChange([...operations, operation(kind, start, end)])
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
  return <div className="edit-composer">
    <div className="composer-heading"><div><span className="eyebrow">BUILD YOUR EDIT</span><h3>What would you like to change?</h3></div><span className="input-help">Combine up to 24 edits</span></div>
    <div className="edit-type-grid">{EDITS.map(({ kind, icon: Icon, hint }) => <button type="button" className="edit-type" key={kind} onClick={() => add(kind)} disabled={disabled || operations.length >= 24}><Icon size={21} /><strong>{EDIT_LABELS[kind]}</strong><span>{hint}</span><Plus size={15} className="edit-type-plus" /></button>)}</div>
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
      {operations.map((op, index) => <fieldset className="edit-card" key={index} disabled={disabled}>
        <legend><span>{String(index + 1).padStart(2, '0')}</span> {EDIT_LABELS[op.kind]}</legend>
        <button className="icon-button remove-edit" type="button" onClick={() => onChange(operations.filter((_, i) => i !== index))} aria-label={`Remove edit ${index + 1}`}><Trash2 size={18} /></button>
        <div className="edit-fields">
          <label>Start (s)<input type="number" min={0} max={duration} step={0.1} value={Number.isFinite(op.start) ? op.start : ''} onChange={e => change(index, { start: e.target.valueAsNumber })} /></label>
          <label>End (s)<input type="number" min={0.1} max={duration} step={0.1} value={Number.isFinite(op.end) ? op.end : ''} onChange={e => change(index, { end: e.target.valueAsNumber })} /></label>
          <button type="button" className="secondary-button" disabled={!Number.isFinite(op.start)} onClick={() => onSeek(op.start)}>Watch from here</button>
        </div>
        {['text', 'subtitle'].includes(op.kind) && <div className="caption-fields">
          <label>Exact words<textarea rows={2} maxLength={160} value={op.text} placeholder={op.kind === 'text' ? 'AI, made practical.' : 'Enter this subtitle line…'} onChange={e => change(index, { text: e.target.value })} /></label>
          <label>Position<select value={op.position} onChange={e => change(index, { position: e.target.value as EditOperation['position'] })}><option value="bottom">Bottom</option><option value="top">Top</option><option value="center">Center</option><option value="bottom_right">Bottom right</option></select></label>
        </div>}
        {op.kind === 'zoom' && <p className="input-help">A fixed center zoom during this interval: 1.05× or 1.12×. The crop can cut off existing text near the edges; check the previews.</p>}
        {op.kind === 'cut' && <p className="input-help">Remove both the picture and audio in this interval. Kept sections join together.</p>}
        {op.kind === 'subtitle' && <p className="input-help">One cue per edit. Add another timed subtitle for the next line. Speech is not transcribed automatically.</p>}
        {op.kind === 'remove_silence' && <>
          <div className="edit-fields silence-fields"><label>Minimum pause (s)<input type="number" min={0.3} max={3} step={0.1} value={Number.isFinite(op.min_silence) ? op.min_silence : ''} onChange={e => change(index, { min_silence: e.target.valueAsNumber })} /></label><label>Quiet level<select value={op.threshold_db} onChange={e => change(index, { threshold_db: Number(e.target.value) })}><option value={-50}>Very quiet · −50 dB</option><option value={-40}>Quiet · −40 dB</option><option value={-30}>Low sound · −30 dB</option></select></label></div>
          <p className="input-help">Continuous music may leave no quiet pauses. We keep a small margin around sound and ask you to select each proposed cut.</p>
        </>}
      </fieldset>)}
    </div>}
    <p className="capability-note">Available: center zoom, text, timed subtitles, timed cuts and quiet-pause detection. Existing text in the original is not erased. Object tracking, background replacement, generated scenes and automatic speech transcription are not included.</p>
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
      <label><input type="checkbox" checked={selected.includes(i)} disabled={disabled || rendered} onChange={() => onSelect(selected.includes(i) ? selected.filter(n => n !== i) : [...selected, i])} /><span><strong>{op.detected ? 'Quiet pause · proposed cut' : EDIT_LABELS[op.kind]}</strong><span>{seconds(op.start)}–{seconds(op.end)} of original{op.text ? ` · “${op.text}” · ${op.position.replace('_', ' ')}` : ''}</span></span></label>
      <button type="button" className="secondary-button" onClick={() => onSeek(op.start)}>Watch original</button>
    </div>)}</div>
    <div className="plan-duration"><span>Original <strong>{seconds(plan.source_duration)}</strong></span><span>After selected edits <strong>{seconds(outputDuration(chosen))}</strong></span></div>
    {rendered && <div className="section-action-bar"><p>Want different text, timing or cuts? Adjust your edits and make fresh previews.</p><button type="button" className="secondary-button" onClick={onEdit} disabled={disabled}>Adjust edits</button></div>}
    {!rendered && <div className="section-action-bar"><div><strong>{selected.length} edit{selected.length === 1 ? '' : 's'} selected</strong><p>{problem ?? 'Watch the full previews before choosing an option.'}</p></div><button type="button" className="secondary-button" onClick={onEdit} disabled={disabled}>Edit request</button><button type="button" className="primary-button" onClick={onPreview} disabled={disabled || Boolean(problem)}><Film size={18} />Create previews</button></div>}
  </section>
}
