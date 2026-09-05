import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { operation, planIssues, planProblem } from './editing'
import { PlanIssueNotice } from './StudioApp'

const screenshotPlan = () => ({ source_duration: 30, operations: [
  { ...operation('subtitle', 0, 15, 'Meet KANAPP.'), position: 'center' as const },
  operation('subtitle', 15, 30, 'AI, made practical.'),
  operation('cut', 0, 4), operation('zoom', 0, 4),
  { ...operation('logo', 0, 30), asset_id: '01M1RFPEN1BG17X6MZQ8B0ZF6V', asset_sha256: 'a'.repeat(64) },
] })

describe('Studio actionable plan validation', () => {
  it('identifies the exact zoom and cut in the reported five-edit plan', () => {
    const issues = planIssues(screenshotPlan())
    expect(issues).toHaveLength(1)
    expect(issues[0].operationIndexes).toEqual([3, 2])
    expect(issues[0].message).toMatch(/Edit 4.*Zoom in.*0s–4s.*entirely.*Edit 3/)
    expect(issues[0].message).toContain('Move it to a section you keep')
    expect(planProblem(screenshotPlan())).toBe(issues[0].message)
  })

  it('clears the block only after the edit moves into retained footage', () => {
    const plan = screenshotPlan()
    plan.operations[3] = operation('zoom', 4, 8)
    expect(planIssues(plan)).toEqual([])
    expect(planProblem(plan)).toBeNull()
  })

  it('finds visual edits covered by multiple adjacent cuts', () => {
    expect(planIssues({ source_duration: 30, operations: [operation('cut', 0, 2), operation('cut', 2, 4), operation('zoom', 0, 4)] })[0].operationIndexes).toEqual([2, 0, 1])
  })

  it('does not reject partially retained footage or adjacent overlays', () => {
    expect(planIssues({ source_duration: 30, operations: [operation('cut', 0, 4), operation('zoom', 2, 6), operation('subtitle', 4, 8, 'One'), operation('subtitle', 8, 12, 'Two')] })).toEqual([])
  })

  it('reports multiple invalid fields without losing their edit numbers', () => {
    const issues = planIssues({ source_duration: 30, operations: [operation('text', 4, 8), operation('zoom', NaN, 8)] })
    expect(issues.map(issue => issue.operationIndexes)).toEqual([[0], [1]])
  })

  it.each(['speed', 'volume', 'zoom', 'subtitle'] as const)('identifies both overlapping %s edits', kind => {
    const issues = planIssues({ source_duration: 30, operations: [operation(kind, 0, 4, 'One'), operation(kind, 2, 6, 'Two')] })
    expect(issues[0].operationIndexes).toEqual([0, 1])
    expect(issues[0].message).toMatch(/Edit 1.*Edit 2.*conflict/)
  })

  it('keeps original edit numbers when validating a selected subset', () => {
    const issues = planIssues({ source_duration: 30, operations: [operation('cut', 0, 4), operation('zoom', 0, 4)] }, [2, 4])
    expect(issues[0].operationIndexes).toEqual([4, 2])
    expect(issues[0].message).toMatch(/Edit 5.*Edit 3/)
  })

  it('renders a visible, accessible reason and direct edit action', () => {
    const html = renderToStaticMarkup(<PlanIssueNotice issues={planIssues(screenshotPlan())} onEdit={() => {}} disabled={false} />)
    expect(html).toContain('role="status"')
    expect(html).toContain('Fix 1 issue before continuing')
    expect(html).toContain('Edit 4: Zoom in')
    expect(html).toContain('Fix edit 4')
  })

  it('explains a deselected empty plan without offering a nonexistent edit', () => {
    const issues = planIssues({ source_duration: 30, operations: [] })
    const html = renderToStaticMarkup(<PlanIssueNotice issues={issues} onEdit={() => {}} disabled={false} />)
    expect(html).toContain('Select at least one edit')
    expect(html).not.toContain('Fix edit 1')
  })
})
