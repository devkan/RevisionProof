import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { operation } from './editing'
import { StudioOperationEditor } from './StudioOperationEditor'

const props = {
  index: 0, duration: 30, disabled: false, canMoveDown: false, canDuplicate: true,
  onChange: () => {}, onDelete: () => {}, onDuplicate: () => {}, onMove: () => {}, onSeek: () => {},
}

describe('Studio edit settings', () => {
  it('shows the actual custom slider value in the preset selector', () => {
    const edit = { ...operation('volume', 0, 4), volume_db: -5 }
    const html = renderToStaticMarkup(<StudioOperationEditor {...props} operation={edit} />)
    expect(html).toContain('<option value="-5" selected="">Custom · -5 dB</option>')
  })

  it('explains invalid or missing times', () => {
    for (const start of [NaN, -1]) {
      const html = renderToStaticMarkup(<StudioOperationEditor {...props} operation={operation('zoom', start, 4)} />)
      expect(html).toContain('Enter a start and end time within this video.')
      expect(html).toContain('studio-range-note is-error')
    }
  })
})
