import { describe, expect, it } from 'vitest'
import { sampleAsset } from './sampleAssets'
import type { DemoAsset } from './types'

const legacy: DemoAsset = { asset_id: 'legacy', title: 'Product Reveal', source_url: '/media/demo/revisionproof_v1.mp4', duration_seconds: 30, width: 1280, height: 720, codec: 'h264/aac', source_kind: 'demo' }
const kanapp: DemoAsset = { ...legacy, asset_id: 'kanapp', title: 'KANAPP', source_url: '/media/demo/kanapp_promo_english_editable_30s.mp4' }

describe('sample source selection', () => {
  it('uses KANAPP regardless of API ordering', () => {
    expect(sampleAsset([legacy, kanapp])).toBe(kanapp)
    expect(sampleAsset([kanapp, legacy])).toBe(kanapp)
  })
  it('keeps the original proof demo on its own indexed source', () => {
    expect(sampleAsset([kanapp, legacy], true)).toBe(legacy)
    expect(sampleAsset([kanapp], true)).toBeUndefined()
  })
  it('handles empty and older asset catalogs', () => {
    expect(sampleAsset([])).toBeUndefined()
    expect(sampleAsset([legacy])).toBe(legacy)
  })
})
