// Regression: design-review FINDING-001, 2026-09-05.
// Report: ~/.gstack/projects/RevisionProof/designs/design-audit-20260905/design-audit-localhost.md
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { StudioRevisionCard } from './StudioRevisionCard'
import { StudioOperationEditor } from './StudioOperationEditor'
import { operation } from './editing'

const card = { index: 2, title: 'Cut a section', detail: '0s–4s', status: 'ready' as const, expanded: true, disabled: false, editable: true, issues: [], onToggle: () => {} }
const editor = <StudioOperationEditor operation={operation('cut', 0, 4)} index={2} duration={30} disabled={false} canMoveDown={false} canDuplicate onChange={() => {}} onDelete={() => {}} onDuplicate={() => {}} onMove={() => {}} onSeek={() => {}} />

describe('inline Studio revision settings', () => {
  it('places the expanded editor after its trigger, inside the same list item', () => {
    const html = renderToStaticMarkup(<StudioRevisionCard {...card}>{editor}</StudioRevisionCard>)
    expect(html).toMatch(/^<li.*is-selected/)
    expect(html).toContain('aria-expanded="true" aria-controls="studio-revision-2-settings"')
    expect(html).toContain('role="region" aria-labelledby="studio-revision-2-trigger"')
    expect(html.indexOf('id="studio-revision-2-settings"')).toBeGreaterThan(html.indexOf('</button>'))
    expect(html.indexOf('class="studio-settings"')).toBeLessThan(html.indexOf('</li>'))
    expect(html).toContain('value="4"')
  })

  it('keeps a valid disclosure target but removes hidden inputs when collapsed', () => {
    const html = renderToStaticMarkup(<StudioRevisionCard {...card} expanded={false}>{editor}</StudioRevisionCard>)
    expect(html).toContain('aria-expanded="false"')
    expect(html).toContain('id="studio-revision-2-settings"')
    expect(html).toContain('hidden=""')
    expect(html).not.toContain('<input')
    expect(html).toContain('Edit settings')
  })

  it('renders one editor when another row is selected and preserves the supplied values', () => {
    const html = renderToStaticMarkup(<ol><StudioRevisionCard {...card} index={0} expanded={false}>{editor}</StudioRevisionCard><StudioRevisionCard {...card}>{editor}</StudioRevisionCard></ol>)
    expect(html.match(/class="studio-settings"/g)).toHaveLength(1)
    expect(html.match(/aria-expanded="true"/g)).toHaveLength(1)
    expect(html).toContain('value="4"')
  })

  it('associates the visible issue with its own trigger and settings', () => {
    const html = renderToStaticMarkup(<StudioRevisionCard {...card} issues={['Move this edit to footage you keep.']}>{editor}</StudioRevisionCard>)
    expect(html).toContain('aria-describedby="studio-revision-2-issues"')
    expect(html).toContain('id="studio-revision-2-issues"')
    expect(html).toContain('needs fix')
    expect(html.indexOf('Move this edit')).toBeLessThan(html.indexOf('class="studio-settings"'))
  })

  it('does not expose editable controls in a frozen reviewed plan', () => {
    const html = renderToStaticMarkup(<StudioRevisionCard {...card} editable={false}>{editor}</StudioRevisionCard>)
    expect(html).toContain('disabled=""')
    expect(html).not.toContain('aria-expanded')
    expect(html).not.toContain('class="studio-settings"')
    expect(html).not.toContain('Edit settings')
  })

  it('disables the disclosure while processing', () => {
    const html = renderToStaticMarkup(<StudioRevisionCard {...card} disabled>{editor}</StudioRevisionCard>)
    expect(html).toMatch(/id="studio-revision-2-trigger" disabled=""/)
  })
})
