import type { EditPlan, RunSnapshot } from './types'

type WorkflowRun = Pick<RunSnapshot, 'edit_plan' | 'candidates' | 'proof' | 'generated_version_url' | 'run_id'>

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
