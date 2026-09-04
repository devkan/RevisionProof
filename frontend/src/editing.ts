import type { EditOperation, EditPlan, PatchCandidate } from './types'

export const EDIT_LABELS = { zoom: 'Zoom in', text: 'Add text', subtitle: 'Timed subtitle', cut: 'Cut a section', remove_silence: 'Find quiet pauses', speed: 'Change speed', volume: 'Adjust volume', logo: 'Add logo' }
export const seconds = (value: number) => Number.isFinite(value) ? `${Number(value.toFixed(2))}s` : '—'
export function operation(kind: EditOperation['kind'], start: number, end: number, text = ''): EditOperation {
  return { kind, start, end, text, position: kind === 'logo' ? 'bottom_right' : 'bottom', threshold_db: -40, min_silence: 0.7, detected: false, rate: kind === 'speed' ? 1.5 : 1, volume_db: kind === 'volume' ? -6 : 0, asset_id: '', asset_sha256: '' }
}
export function keptSpans(plan: EditPlan) {
  const cuts = plan.operations.filter(op => op.kind === 'cut').sort((a, b) => a.start - b.start)
  const merged: Array<{ start: number; end: number }> = []
  for (const cut of cuts) {
    const last = merged[merged.length - 1]
    if (last && cut.start <= last.end + 0.001) last.end = Math.max(last.end, cut.end)
    else merged.push({ start: cut.start, end: cut.end })
  }
  const boundaries = new Set([0, plan.source_duration])
  merged.forEach(cut => { boundaries.add(cut.start); boundaries.add(cut.end) })
  plan.operations.filter(op => op.kind === 'speed').forEach(op => { boundaries.add(op.start); boundaries.add(op.end) })
  let output = 0
  const spans: Array<{ start: number; end: number; output: number; rate: number; duration: number }> = []
  const points = [...boundaries].sort((a, b) => a - b)
  for (let i = 0; i < points.length - 1; i++) {
    const start = points[i], end = points[i + 1], midpoint = (start + end) / 2
    if (end - start <= 0.001 || merged.some(cut => cut.start <= midpoint && midpoint < cut.end)) continue
    const rate = plan.operations.find(op => op.kind === 'speed' && op.start <= midpoint && midpoint < op.end)?.rate ?? 1
    const duration = (end - start) / rate
    spans.push({ start, end, output, rate, duration })
    output += duration
  }
  return spans
}
export const outputDuration = (plan: EditPlan) => keptSpans(plan).reduce((sum, span) => sum + span.duration, 0)
export function sourceTimeForOutput(plan: EditPlan | undefined, time: number): number {
  if (!plan) return time
  const spans = keptSpans(plan)
  const t = Math.max(0, Math.min(outputDuration(plan) - 0.001, time))
  const span = spans.find(s => t >= s.output && t < s.output + s.duration)
  return span ? span.start + (t - span.output) * span.rate : 0
}
export function planProblem(plan: EditPlan): string | null {
  if (!plan.operations.length) return 'Choose an edit below or turn your request into a plan.'
  if (plan.operations.length > 24) return 'Use up to 24 edits in one video.'
  for (const [i, op] of plan.operations.entries()) {
    if (![op.start, op.end].every(Number.isFinite) || op.start < 0 || op.end > plan.source_duration + 0.001 || op.end - op.start < 0.09) return `Edit ${i + 1}: choose a valid start and end within this video (at least 0.1s).`
    if (['text', 'subtitle'].includes(op.kind) && (!op.text.trim() || op.text.length > 160 || op.text.split('\n').length > 3)) return `Edit ${i + 1}: enter text, up to 160 characters and 3 lines.`
    if (op.kind === 'remove_silence' && (!Number.isFinite(op.min_silence) || op.min_silence < 0.3 || op.min_silence > 3)) return `Edit ${i + 1}: choose a minimum pause between 0.3 and 3 seconds.`
    if (op.kind === 'speed' && (!Number.isFinite(op.rate) || op.rate < 0.5 || op.rate > 2 || Math.abs(op.rate - 1) < 0.001)) return `Edit ${i + 1}: choose a speed from 0.5× to 2×, excluding 1×.`
    if (op.kind === 'volume' && (!Number.isFinite(op.volume_db) || op.volume_db < -60 || op.volume_db > 12 || Math.abs(op.volume_db) < 0.001)) return `Edit ${i + 1}: choose a volume from −60 dB to +12 dB, excluding 0 dB.`
    if (op.kind === 'logo' && (!/^[0-9A-HJKMNP-TV-Z]{26}$/.test(op.asset_id) || !/^[a-f0-9]{64}$/.test(op.asset_sha256))) return `Edit ${i + 1}: upload a valid logo image.`
  }
  if (outputDuration(plan) < 0.999) return 'Keep at least one second of the original video.'
  if (outputDuration(plan) > 60.05) return 'The edited video must stay within 60 seconds. Shorten the slow section or choose a faster rate.'
  for (const kind of ['speed', 'volume'] as const) {
    const timed = plan.operations.filter(op => op.kind === kind)
    for (const [i, a] of timed.entries()) if (timed.slice(i + 1).some(b => Math.max(a.start, b.start) < Math.min(a.end, b.end))) return `Overlapping ${kind} edits conflict. Adjust their times.`
  }
  const visual = plan.operations.filter(op => ['zoom', 'text', 'subtitle', 'logo'].includes(op.kind))
  for (const [i, a] of visual.entries()) {
    if (!keptSpans(plan).some(s => Math.max(a.start, s.start) < Math.min(a.end, s.end))) return 'A visual edit falls entirely inside a section you are cutting. Adjust its times.'
    for (const b of visual.slice(i + 1)) {
      if (Math.max(a.start, b.start) < Math.min(a.end, b.end) && ((a.kind === 'zoom' && b.kind === 'zoom') || (a.kind !== 'zoom' && b.kind !== 'zoom' && a.position === b.position))) return 'Overlapping zooms or overlays at the same position conflict. Adjust the times or position.'
    }
  }
  return null
}
export function editDetail(op: EditOperation) {
  const detail = op.text ? ` · “${op.text}” · ${op.position.replace('_', ' ')}` : op.kind === 'speed' ? ` · ${op.rate}×` : op.kind === 'volume' ? ` · ${op.volume_db <= -60 ? 'mute' : `${op.volume_db > 0 ? '+' : ''}${op.volume_db} dB`}` : op.kind === 'logo' ? ` · ${op.position.replace('_', ' ')}` : ''
  return `${seconds(op.start)}–${seconds(op.end)}${detail}`
}
export function editSummary(op: EditOperation) {
  return `${EDIT_LABELS[op.kind]} · ${editDetail(op)}`
}
export function candidateTitle(candidate: PatchCandidate) {
  if (candidate.patch_type === 'PUNCH_IN') return `${candidate.candidate_id === 'A' ? 'Subtle' : 'Stronger'} center punch-in`
  if (!candidate.plan.operations.some(op => ['zoom', 'text', 'subtitle', 'logo'].includes(op.kind))) return 'Your edited video'
  const zoom = candidate.plan.operations.some(op => op.kind === 'zoom')
  const text = candidate.plan.operations.some(op => ['text', 'subtitle'].includes(op.kind))
  const logo = candidate.plan.operations.some(op => op.kind === 'logo')
  return [zoom ? candidate.candidate_id === 'A' ? 'Subtle zoom' : 'Stronger zoom' : '', text ? candidate.candidate_id === 'A' ? 'Smaller text' : 'Larger text' : '', logo ? candidate.candidate_id === 'A' ? 'Smaller logo' : 'Larger logo' : ''].filter(Boolean).join(' · ')
}
