import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { RequestDraft } from './EditComposer'

function renderDraft(text = '') {
  return renderToStaticMarkup(<RequestDraft
    text={text} duration={30} disabled={false} mode="FIXTURE"
    onText={() => {}} onApply={() => {}} onBusy={() => {}} onSceneSelect={() => {}}
  />)
}

describe('English request form copy', () => {
  it('renders an English example and time hint for an empty request', () => {
    const html = renderDraft()
    expect(html).toContain('placeholder="Zoom in from 4 to 10 seconds')
    expect(html).toContain('4–10 seconds')
    expect(html).not.toMatch(/[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]/)
  })

  it.each([
    'Zoom in from 4 to 10 seconds and show "AI, made practical." at the bottom.',
    '4–10초를 확대해 주세요.',
  ])('keeps requests with explicit times enabled: %s', (text) => {
    const html = renderDraft(text)
    expect(html).toContain('Scene time is ready.')
    expect(html).toMatch(/<button type="button" class="secondary-button">/)
    expect(html).toContain('Optional · English or Korean')
  })
})
