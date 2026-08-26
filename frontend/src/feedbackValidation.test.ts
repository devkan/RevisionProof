import { describe, expect, it } from 'vitest'

import { feedbackValidationMessage } from './feedbackValidation'

describe('client feedback validation', () => {
  it('explains how many characters are still required', () => {
    expect(feedbackValidationMessage('short')).toBe(
      'Client feedback must be at least 8 characters (3 more needed).',
    )
  })

  it('returns no message once the minimum length is met', () => {
    expect(feedbackValidationMessage('12345678')).toBeNull()
  })
})
