import type { RunState } from './types'

const TERMINAL_RUN_STATES: ReadonlySet<RunState> = new Set(['BLOCKED', 'READY', 'FAILED'])

export function isTerminalRunState(state: RunState): boolean {
  return TERMINAL_RUN_STATES.has(state)
}
