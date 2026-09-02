import { describe, expect, it } from 'vitest'
import { DEFAULT_FEEDBACK } from './demoFeedback'

describe('default demo feedback', () => {
  it('keeps the supported punch-in note inside the 4-8 second safety window', () => {
    const notes = DEFAULT_FEEDBACK.split('\n')

    expect(notes).toHaveLength(3)
    expect(notes[0]).toContain('6-second center PUNCH_IN')
    expect(notes[0]).toContain('presenter says "RevisionProof."')
    expect(notes[1]).toContain('middle feel more dynamic')
    expect(notes[2]).toContain('Add B-roll')
  })
})

