import { describe, expect, it } from 'vitest'
import { operation } from './editing'
import { checkedVideoUrl, planAction, reviewedPlan } from './studioWorkflow'
import type { RunSnapshot } from './types'

const draft = { source_duration: 30, operations: [operation('zoom', 4, 10), operation('text', 4, 10, 'Title')] }
const run: Pick<RunSnapshot, 'run_id' | 'edit_plan' | 'candidates' | 'proof' | 'generated_version_url'> = {
  run_id: 'review-1', edit_plan: draft, candidates: [],
}

describe('Studio workflow state', () => {
  it('preserves zero selected edits instead of falling back to the full draft', () => {
    expect(reviewedPlan(run, draft, []).operations).toEqual([])
    expect(reviewedPlan(null, draft, []).operations).toHaveLength(2)
  })

  it('uses the frozen server plan after a non-prefix subset is previewed', () => {
    const selected = { ...draft, operations: [draft.operations[1]] }
    const previewed = { ...run, edit_plan: selected, candidates: [{ candidate_id: 'A', patch_type: 'EDIT_PLAN', plan: selected }] } as typeof run
    expect(reviewedPlan(previewed, draft, [1])).toEqual(selected)
    expect(planAction(3, previewed)).toEqual({ label: 'Continue to previews', nextStep: 4 })
    expect(planAction(2, previewed)).toEqual({ label: 'Continue to plan', nextStep: 3 })
    expect(planAction(3, run)).toBeNull()
    expect(planAction(2, null)).toBeNull()
  })

  it('uses only the external file that belongs to the current verification', () => {
    const verified = { ...run, proof: { version_label: 'external-1' } } as typeof run
    const external = { runId: 'review-1', versionLabel: 'external-1', url: 'blob:checked-file' }
    expect(checkedVideoUrl(verified, external)).toBe('blob:checked-file')
    expect(checkedVideoUrl(verified, { ...external, runId: 'old-review' })).toBeUndefined()
    expect(checkedVideoUrl(verified, { ...external, versionLabel: 'old-upload' })).toBeUndefined()
    expect(checkedVideoUrl(run, external)).toBeUndefined()
    expect(checkedVideoUrl({ ...verified, generated_version_url: '/generated' }, external)).toBe('/generated')
  })
})
