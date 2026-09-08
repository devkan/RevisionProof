import type { DemoAsset } from './types'

export function sampleAsset(assets: DemoAsset[], legacy = false): DemoAsset | undefined {
  const filename = legacy ? 'revisionproof_v1.mp4' : 'kanapp_promo_english_editable_30s.mp4'
  return assets.find(asset => asset.source_url === `/media/demo/${filename}`)
    ?? (legacy ? undefined : assets[0])
}
