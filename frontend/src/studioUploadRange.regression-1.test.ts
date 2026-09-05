import { describe, expect, it } from 'vitest'
import { operation } from './editing'
import { uploadPreparationRange } from './studioWorkflow'
import type { EditPlan } from './types'

// Regression: ISSUE-LIVE-001 — valid edits failed the legacy 4–8s upload gate.
// Found by /qa on 2026-09-05.
// Report: docs/deployment-2026-09-05-studio.md
describe('Studio source preparation is separate from the edit timeline', () => {
  it.each([
    operation('remove_silence', 0, 9.962),
    operation('subtitle', 0, 2, 'Short caption'),
    operation('cut', 1, 1.5),
    operation('text', 0, 9.962, 'Full-video title'),
    operation('zoom', 8, 9.962),
  ])('prepares an upload without narrowing a $kind edit', (edit) => {
    const plan: EditPlan = { source_duration: 9.962, operations: [edit] }
    const before = structuredClone(plan)
    expect(uploadPreparationRange(plan)).toEqual({ start_seconds: 0, end_seconds: 6 })
    expect(plan).toEqual(before)
  })

  it.each([4, 4.01, 5.9, 6, 30, 60])('bounds preparation to a %s-second source', (duration) => {
    expect(uploadPreparationRange({ source_duration: duration, operations: [] }))
      .toEqual({ start_seconds: 0, end_seconds: Math.min(6, duration) })
  })

  it('retains a valid explicit scene without forwarding extra metadata', () => {
    const scene = { start_seconds: 16, end_seconds: 20, segment_id: 'chosen-scene' }
    expect(uploadPreparationRange({ source_duration: 30, operations: [] }, scene))
      .toEqual({ start_seconds: 16, end_seconds: 20 })
  })

  it.each([
    { start_seconds: 28, end_seconds: 30 },
    { start_seconds: 0, end_seconds: 30 },
    { start_seconds: -1, end_seconds: 4 },
    { start_seconds: 28, end_seconds: 34 },
  ])('does not reuse an incompatible scene as a preparation window', (scene) => {
    expect(uploadPreparationRange({ source_duration: 30, operations: [] }, scene))
      .toEqual({ start_seconds: 0, end_seconds: 6 })
  })
})
