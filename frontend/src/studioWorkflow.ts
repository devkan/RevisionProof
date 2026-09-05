import type { EditPlan, RunSnapshot, TimeRange } from './types'

type WorkflowRun = Pick<RunSnapshot, 'edit_plan' | 'candidates' | 'proof' | 'generated_version_url' | 'run_id'>

export function uploadPreparationRange(plan: EditPlan, scene?: TimeRange): TimeRange {
  // The upload preparer still accepts a legacy 4–8s anchor, not the edit range.
  // The complete plan and selected scene IDs are sent separately and stay intact.
  if (scene) {
    const span = scene.end_seconds - scene.start_seconds
    if (scene.start_seconds >= 0 && scene.end_seconds <= plan.source_duration && span >= 4 && span <= 8) {
      return { start_seconds: scene.start_seconds, end_seconds: scene.end_seconds }
    }
  }
  return { start_seconds: 0, end_seconds: Math.min(6, plan.source_duration) }
}

export function reviewedPlan(run: WorkflowRun | null, draft: EditPlan, selected: number[]): EditPlan {
  if (!run?.edit_plan) return draft
  // The server replaces the draft with the selected subset when it creates previews.
  if (run.candidates.length) return run.edit_plan
  return { ...run.edit_plan, operations: run.edit_plan.operations.filter((_, index) => selected.includes(index)) }
}

export function planAction(step: number, run: WorkflowRun | null) {
  if (step === 2 && run?.edit_plan) return { label: 'Continue to plan', nextStep: 3 } as const
  if (step === 3 && run?.candidates.length) return { label: 'Continue to previews', nextStep: 4 } as const
  return null
}

export interface ExternalVideo { runId: string; versionLabel: string; url: string }

export function checkedVideoUrl(run: WorkflowRun | null, external: ExternalVideo | null) {
  if (!run?.proof) return undefined
  if (run.generated_version_url) return run.generated_version_url
  return external?.runId === run.run_id && external.versionLabel === run.proof.version_label ? external.url : undefined
}
