import { describe, expect, it } from 'vitest'

import { isTerminalRunState } from './runStream'

describe('run event stream lifecycle', () => {
  it('closes only for terminal run states', () => {
    expect(isTerminalRunState('BLOCKED')).toBe(true)
    expect(isTerminalRunState('READY')).toBe(true)
    expect(isTerminalRunState('FAILED')).toBe(true)
    expect(isTerminalRunState('VERIFYING')).toBe(false)
    expect(isTerminalRunState('EVIDENCE_ANCHORED')).toBe(false)
  })
})
