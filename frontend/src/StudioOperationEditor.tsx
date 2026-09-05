import { Copy, Film, GripVertical, Trash2 } from 'lucide-react'
import type { EditOperation } from './types'
import { EDIT_LABELS, seconds } from './editing'

const POSITIONS: Array<{ value: EditOperation['position']; label: string }> = [
  { value: 'top_left', label: 'Top left' },
  { value: 'top', label: 'Top' },
  { value: 'top_right', label: 'Top right' },
  { value: 'center', label: 'Center' },
  { value: 'bottom_left', label: 'Bottom left' },
  { value: 'bottom', label: 'Bottom' },
  { value: 'bottom_right', label: 'Bottom right' },
]

function PositionGrid({ value, disabled, onChange }: {
  value: EditOperation['position']
  disabled: boolean
  onChange: (position: EditOperation['position']) => void
}) {
  return (
    <div className="studio-position-grid" aria-label="Position on video">
      {POSITIONS.map((position) => (
        <button
          type="button"
          key={position.value}
          className={value === position.value ? 'is-selected' : ''}
          aria-label={position.label}
          aria-pressed={value === position.value}
          disabled={disabled}
          onClick={() => onChange(position.value)}
        >
          <span />
        </button>
      ))}
      <span aria-hidden="true" />
      <span aria-hidden="true" />
    </div>
  )
}

export function StudioOperationEditor({
  operation,
  index,
  duration,
  disabled,
  canMoveDown,
  canDuplicate,
  onChange,
  onDelete,
  onDuplicate,
  onMove,
  onSeek,
}: {
  operation: EditOperation | null
  index: number | null
  duration: number
  disabled: boolean
  canMoveDown: boolean
  canDuplicate: boolean
  onChange: (update: Partial<EditOperation>) => void
  onDelete: () => void
  onDuplicate: () => void
  onMove: (direction: -1 | 1) => void
  onSeek: (time: number) => void
}) {
  if (!operation || index === null) {
    return (
      <section className="studio-settings studio-empty-settings">
        <span className="studio-kicker">SETTINGS</span>
        <GripVertical size={24} />
        <h3>Select an edit</h3>
        <p>Choose a tool or select an edit below.</p>
      </section>
    )
  }

  const wholeVideo = operation.start <= 0.001 && Math.abs(operation.end - duration) <= 0.001
  const segmentDuration = Math.max(0, operation.end - operation.start)
  const supportsWholeVideo = !['cut', 'remove_silence', 'subtitle'].includes(operation.kind)
  const supportsPosition = ['text', 'subtitle', 'logo'].includes(operation.kind)
  const invalidRange = !Number.isFinite(operation.start) || !Number.isFinite(operation.end) || operation.start < 0

  return (
    <section className="studio-settings" aria-labelledby="studio-settings-title">
      <header>
        <div>
          <span className="studio-kicker">REVISION {String(index + 1).padStart(2, '0')}</span>
          <h3 id="studio-settings-title">{EDIT_LABELS[operation.kind]}</h3>
        </div>
        <button className="studio-icon-button" type="button" onClick={onDelete} disabled={disabled} aria-label={`Delete revision ${index + 1}`}>
          <Trash2 size={17} />
        </button>
      </header>

      {supportsWholeVideo && (
        <label className="studio-check-row">
          <input
            type="checkbox"
            checked={wholeVideo}
            disabled={disabled}
            onChange={(event) => onChange(event.target.checked
              ? { start: 0, end: duration }
              : { start: 0, end: Math.min(4, duration) })}
          />
          <span><strong>Apply to the full video</strong><small>Turn this off to set a time range.</small></span>
        </label>
      )}

      {!wholeVideo || !supportsWholeVideo ? (
        <div className="studio-field-grid">
          <label>
            <span>Start time <b>*</b></span>
            <input type="number" min={0} max={duration} step={0.1} value={Number.isFinite(operation.start) ? operation.start : ''} disabled={disabled} onChange={(event) => onChange({ start: event.target.valueAsNumber })} />
          </label>
          <label>
            <span>End time <b>*</b></span>
            <input type="number" min={0.1} max={duration} step={0.1} value={Number.isFinite(operation.end) ? operation.end : ''} disabled={disabled} onChange={(event) => onChange({ end: event.target.valueAsNumber })} />
          </label>
        </div>
      ) : null}
      <div className={`studio-range-note ${invalidRange || operation.end <= operation.start || operation.end > duration ? 'is-error' : ''}`}>
        {invalidRange ? 'Enter a start and end time within this video.' : operation.end <= operation.start
          ? 'End time must be later than the start time.'
          : operation.end > duration
            ? `End time is past the end of the video (${seconds(duration)}).`
            : `${seconds(segmentDuration)} selected · source time`}
        <button type="button" onClick={() => onSeek(operation.start)} disabled={disabled || !Number.isFinite(operation.start)}><Film size={14} />Watch</button>
      </div>

      {(operation.kind === 'text' || operation.kind === 'subtitle') && (
        <label className="studio-stack-field">
          <span>Text <b>*</b></span>
          <textarea rows={3} maxLength={160} value={operation.text} disabled={disabled} placeholder="AI, made practical." onChange={(event) => onChange({ text: event.target.value })} />
          <small>{operation.text.length} / 160 · review before processing</small>
        </label>
      )}

      {supportsPosition && (
        <fieldset className="studio-position-field">
          <legend>Position</legend>
          <PositionGrid value={operation.position} disabled={disabled} onChange={(position) => onChange({ position })} />
          <small>{operation.position.replaceAll('_', ' ')}</small>
        </fieldset>
      )}

      {operation.kind === 'zoom' && (
        <div className="studio-info-block">
          <strong>Compare two zoom levels</strong>
          <p>Preview 1.05× and 1.12×, then choose.</p>
        </div>
      )}

      {operation.kind === 'cut' && (
        <div className="studio-info-block studio-info-warning">
          <strong>Removes video and audio</strong>
          <p>Estimated final length: {seconds(Math.max(0, duration - segmentDuration))}. Later edits keep their source times.</p>
        </div>
      )}

      {operation.kind === 'remove_silence' && (
        <>
          <div className="studio-field-grid">
            <label><span>Minimum pause</span><input type="number" min={0.3} max={3} step={0.1} value={operation.min_silence} disabled={disabled} onChange={(event) => onChange({ min_silence: event.target.valueAsNumber })} /></label>
            <label><span>Quiet level</span><select value={operation.threshold_db} disabled={disabled} onChange={(event) => onChange({ threshold_db: Number(event.target.value) })}><option value={-50}>Very quiet · −50 dB</option><option value={-40}>Quiet · −40 dB</option><option value={-30}>Low sound · −30 dB</option></select></label>
          </div>
          <div className="studio-info-block"><strong>Review before removing</strong><p>We suggest quiet ranges. Choose each cut in Plan.</p></div>
        </>
      )}

      {operation.kind === 'speed' && (
        <label className="studio-stack-field">
          <span>Playback speed</span>
          <select value={operation.rate} disabled={disabled} onChange={(event) => onChange({ rate: Number(event.target.value) })}>
            <option value={0.5}>0.5× · slow</option><option value={0.75}>0.75×</option><option value={1.25}>1.25×</option><option value={1.5}>1.5×</option><option value={2}>2× · fast</option>
          </select>
          <small>{seconds(segmentDuration)} becomes {seconds(segmentDuration / operation.rate)}.</small>
        </label>
      )}

      {operation.kind === 'volume' && (
        <label className="studio-stack-field">
          <span>Volume change</span>
          <select value={operation.volume_db} disabled={disabled} onChange={(event) => onChange({ volume_db: Number(event.target.value) })}>
            {![-60, -12, -6, 3, 6, 12].includes(operation.volume_db) && <option value={operation.volume_db}>Custom · {operation.volume_db > 0 ? '+' : ''}{operation.volume_db} dB</option>}
            <option value={-60}>Mute</option><option value={-12}>Much quieter · −12 dB</option><option value={-6}>Quieter · −6 dB</option><option value={3}>Louder · +3 dB</option><option value={6}>Much louder · +6 dB</option><option value={12}>Maximum boost · +12 dB</option>
          </select>
          <input aria-label="Volume decibels" type="range" min={-60} max={12} step={1} value={operation.volume_db} disabled={disabled} onChange={(event) => onChange({ volume_db: Number(event.target.value) })} />
          <small>{operation.volume_db <= -60 ? 'Muted' : `${operation.volume_db > 0 ? '+' : ''}${operation.volume_db} dB`} in this range.</small>
        </label>
      )}

      {operation.kind === 'logo' && (
        <div className="studio-logo-preview">
          <img src={`/media/edit-assets/${operation.asset_id}.png`} alt="Uploaded logo preview" />
          <p>This image and its file hash stay with the review. A/B compares two safe sizes.</p>
        </div>
      )}

      <footer className="studio-settings-actions">
        <button type="button" onClick={() => onMove(-1)} disabled={disabled || index === 0}>↑ Move up</button>
        <button type="button" onClick={() => onMove(1)} disabled={disabled || !canMoveDown}>↓ Move down</button>
        <button type="button" onClick={onDuplicate} disabled={disabled || !canDuplicate}><Copy size={15} />Duplicate</button>
      </footer>
    </section>
  )
}
