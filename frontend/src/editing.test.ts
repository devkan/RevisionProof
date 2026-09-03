import { describe, expect, it } from 'vitest'
import { operation, outputDuration, planProblem, sourceTimeForOutput } from './editing'

describe('editing timeline', () => {
  it('maps playback and seek across overlapping and trailing cuts', () => {
    const plan = { source_duration: 10, operations: [operation('cut', 2, 4), operation('cut', 3, 5), operation('cut', 8, 10)] }
    expect(outputDuration(plan)).toBe(5)
    expect(sourceTimeForOutput(plan, 1.99)).toBeCloseTo(1.99)
    expect(sourceTimeForOutput(plan, 2)).toBe(5)
    expect(sourceTimeForOutput(plan, 4.5)).toBe(7.5)
    expect(sourceTimeForOutput(plan, 5)).toBeLessThan(8)
  })
  it('blocks captions lost in cuts and ambiguous overlapping captions', () => {
    expect(planProblem({ source_duration: 10, operations: [operation('text', 2, 3, 'Title'), operation('cut', 1, 4)] })).toMatch(/entirely/)
    expect(planProblem({ source_duration: 10, operations: [operation('subtitle', 2, 4, 'One'), operation('subtitle', 3, 5, 'Two')] })).toMatch(/conflict/)
    expect(planProblem({ source_duration: 10, operations: [operation('subtitle', 2, 4, 'One'), operation('subtitle', 4, 5, 'Two')] })).toBeNull()
  })
  it('rejects missing text and invalid times without blocking valid compound edits', () => {
    expect(planProblem({ source_duration: 10, operations: [operation('text', 4, 10)] })).toMatch(/enter text/)
    expect(planProblem({ source_duration: 10, operations: [operation('zoom', NaN, 10)] })).toMatch(/valid start/)
    expect(planProblem({ source_duration: 10, operations: [operation('zoom', 4, 10), operation('text', 4, 10, 'AI, made practical.')] })).toBeNull()
  })
})
