import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { VideoLightbox } from './VideoLightbox'

describe('VideoLightbox', () => {
  it('renders an accessible enlarged video dialog', () => {
    const markup = renderToStaticMarkup(
      <VideoLightbox
        content={{
          src: '/media/demo/revisionproof_v1.mp4',
          title: 'Original video',
          detail: 'RevisionProof — Product Reveal',
        }}
        onClose={vi.fn()}
      />,
    )

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('aria-modal="true"')
    expect(markup).toContain('Original video')
    expect(markup).toContain('/media/demo/revisionproof_v1.mp4')
    expect(markup).toContain('Close enlarged video')
  })
})

