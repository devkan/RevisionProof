import type { EditOperation, EditPlan, PatchCandidate } from './types'

export const EDIT_LABELS = { zoom: 'Zoom in', text: 'Add text', subtitle: 'Timed subtitle', cut: 'Cut a section', remove_silence: 'Find quiet pauses' }
export const seconds = (value: number) => Number.isFinite(value) ? `${Number(value.toFixed(2))}s` : '—'
export function operation(kind: EditOperation['kind'], start: number, end: number, text = ''): EditOperation {
  return { kind, start, end, text, position: 'bottom', threshold_db: -40, min_silence: 0.7, detected: false }
}
export function keptSpans(plan: EditPlan) {
  const cuts = plan.operations.filter(op => op.kind === 'cut').sort((a, b) => a.start - b.start)
  const merged: Array<{ start: number; end: number }> = []
  for (const cut of cuts) {
    const last = merged[merged.length - 1]
    if (last && cut.start <= last.end + 0.001) last.end = Math.max(last.end, cut.end)
    else merged.push({ start: cut.start, end: cut.end })
  }
  let cursor = 0, output = 0
  const spans: Array<{ start: number; end: number; output: number }> = []
  for (const cut of [...merged, { start: plan.source_duration, end: plan.source_duration }]) {
    if (cut.start > cursor + 0.001) { spans.push({ start: cursor, end: cut.start, output }); output += cut.start - cursor }
    cursor = Math.max(cursor, cut.end)
  }
  return spans
}
export const outputDuration = (plan: EditPlan) => keptSpans(plan).reduce((sum, span) => sum + span.end - span.start, 0)
export function sourceTimeForOutput(plan: EditPlan | undefined, time: number): number {
  if (!plan) return time
  const spans = keptSpans(plan)
  const t = Math.max(0, Math.min(outputDuration(plan) - 0.001, time))
  const span = spans.find(s => t >= s.output && t < s.output + s.end - s.start)
  return span ? span.start + t - span.output : 0
}
export function planProblem(plan: EditPlan): string | null {
  if (!plan.operations.length) return 'Choose an edit below or turn your request into a plan.'
  if (plan.operations.length > 24) return 'Use up to 24 edits in one video.'
  for (const [i, op] of plan.operations.entries()) {
    if (![op.start, op.end].every(Number.isFinite) || op.start < 0 || op.end > plan.source_duration + 0.001 || op.end - op.start < 0.09) return `Edit ${i + 1}: choose a valid start and end within this video (at least 0.1s).`
    if (['text', 'subtitle'].includes(op.kind) && (!op.text.trim() || op.text.length > 160 || op.text.split('\n').length > 3)) return `Edit ${i + 1}: enter text, up to 160 characters and 3 lines.`
    if (op.kind === 'remove_silence' && (!Number.isFinite(op.min_silence) || op.min_silence < 0.3 || op.min_silence > 3)) return `Edit ${i + 1}: choose a minimum pause between 0.3 and 3 seconds.`
  }
  if (outputDuration(plan) < 0.999) return 'Keep at least one second of the original video.'
  const visual = plan.operations.filter(op => ['zoom', 'text', 'subtitle'].includes(op.kind))
  for (const [i, a] of visual.entries()) {
    if (!keptSpans(plan).some(s => Math.max(a.start, s.start) < Math.min(a.end, s.end))) return 'A visual edit falls entirely inside a section you are cutting. Adjust its times.'
    for (const b of visual.slice(i + 1)) {
      if (Math.max(a.start, b.start) < Math.min(a.end, b.end) && ((a.kind === 'zoom' && b.kind === 'zoom') || (a.kind !== 'zoom' && b.kind !== 'zoom' && a.position === b.position))) return 'Overlapping zooms or captions at the same position conflict. Adjust the times or position.'
    }
  }
  return null
}
export function editSummary(op: EditOperation) {
  return `${EDIT_LABELS[op.kind]} · ${seconds(op.start)}–${seconds(op.end)}${op.text ? ` · “${op.text}” · ${op.position.replace('_', ' ')}` : ''}`
}
export function candidateTitle(candidate: PatchCandidate) {
  if (candidate.patch_type === 'PUNCH_IN') return `${candidate.candidate_id === 'A' ? 'Subtle' : 'Stronger'} center punch-in`
  if (!candidate.plan.operations.some(op => ['zoom', 'text', 'subtitle'].includes(op.kind))) return 'Your shorter video'
  const zoom = candidate.plan.operations.some(op => op.kind === 'zoom')
  const text = candidate.plan.operations.some(op => ['text', 'subtitle'].includes(op.kind))
  return [zoom ? candidate.candidate_id === 'A' ? 'Subtle zoom' : 'Stronger zoom' : '', text ? candidate.candidate_id === 'A' ? 'Smaller text' : 'Larger text' : ''].filter(Boolean).join(' · ')
}
