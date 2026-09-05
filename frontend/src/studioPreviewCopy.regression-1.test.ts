import { describe, expect, it } from 'vitest'
import { countedLabel, previewGuidance } from './studioWorkflow'

// Regression: ISSUE-LIVE-002 — cut-only plans claimed two versions existed.
// Found by /qa on 2026-09-05; docs/deployment-2026-09-05-studio.md.
describe('Studio preview guidance matches the generated candidates', () => {
  it('offers one preview without promising a missing version B', () => {
    expect(previewGuidance(1)).toEqual({
      title: 'Review your preview.',
      detail: 'This edit has one version. Watch the cuts and timing before choosing it.',
      hint: 'Watch the preview before choosing',
      action: 'Choose the preview above',
    })
    expect(JSON.stringify(previewGuidance(1))).not.toMatch(/both|Version B|A or B/)
  })

  it('preserves the guidance for an actual A/B pair', () => {
    expect(previewGuidance(2).title).toBe('Compare both versions.')
    expect(previewGuidance(2).detail).toContain('Version B')
    expect(previewGuidance(2).action).toBe('Choose A or B above')
  })

  it.each(['item', 'version', 'revision', 'edit'])('uses a singular %s for one', (noun) => {
    expect(countedLabel(1, noun)).toBe(`1 ${noun}`)
    expect(countedLabel(0, noun)).toBe(`0 ${noun}s`)
    expect(countedLabel(2, noun)).toBe(`2 ${noun}s`)
  })
})
