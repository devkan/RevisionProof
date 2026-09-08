// @vitest-environment happy-dom
import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api'
import StudioApp from './StudioApp'

afterEach(() => vi.restoreAllMocks())

it('Use sample video loads the KANAPP source without uploading a file', async () => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true })
  vi.spyOn(api, 'runtime').mockResolvedValue({ mode: 'FIXTURE', mutable: true, live_ready: false, missing_settings: [], message: 'Local test' })
  const common = { duration_seconds: 30, width: 1280, height: 720, codec: 'h264/aac', source_kind: 'demo' as const }
  vi.spyOn(api, 'assets').mockResolvedValue([
    { ...common, asset_id: 'legacy', title: 'Product Reveal', source_url: '/media/demo/revisionproof_v1.mp4' },
    { ...common, asset_id: 'kanapp', title: 'KANAPP — English Promo (30s)', source_url: '/media/demo/kanapp_promo_english_editable_30s.mp4' },
  ])
  const upload = vi.spyOn(api, 'uploadSource')
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  try {
    await act(async () => { root.render(<StudioApp />) })
    const sample = Array.from(container.querySelectorAll('button')).find(button => button.textContent === 'Use sample video')!
    expect(sample).toBeDefined()
    expect(sample.disabled).toBe(false)
    await act(async () => sample.click())
    expect(container.querySelector('video')?.getAttribute('src')).toBe('/media/demo/kanapp_promo_english_editable_30s.mp4')
    expect(container.textContent).toContain('KANAPP — English Promo (30s)')
    expect(upload).not.toHaveBeenCalled()
  } finally {
    await act(async () => root.unmount())
    container.remove()
  }
})
