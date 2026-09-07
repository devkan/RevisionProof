// @vitest-environment happy-dom
import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { ChangeMap } from './RevisionIntelligence'
import type { ChangeWindow, RunSnapshot } from './types'

function makeMockRun(options: {
  analysisId: string
  generatedUrl?: string | null
  windows: ChangeWindow[]
}): RunSnapshot {
  return {
    run_id: 'run-test-123',
    asset: {
      asset_id: 'asset-123',
      title: 'Test Asset',
      source_url: '/source.mp4',
      duration_seconds: 4,
      width: 1920,
      height: 1080,
      fps: 30,
    },
    delivery_approved: false,
    generated_version_url: options.generatedUrl ?? undefined,
    change_map: {
      analysis_id: options.analysisId,
      status: 'ready',
      source: 'fixture.frame_analysis',
      duration_seconds: 4,
      message: 'Sampling analysis',
      windows: options.windows,
    },
    proof: {
      verdict: options.windows.some((w) => w.status === 'review') ? 'BLOCKED' : 'PASS',
      publish_allowed: !options.windows.some((w) => w.status === 'review'),
      checks: [],
    },
  } as unknown as RunSnapshot
}

describe('ChangeMap regression: Issue B & Issue C', () => {
  describe('Issue B: Compare this moment with external revised videos', () => {
    it('enables Compare this moment button when revisedVideoUrl is passed, even if run.generated_version_url is undefined', () => {
      const run = makeMockRun({
        analysisId: 'analysis-external-blocked',
        generatedUrl: undefined,
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'review', visual_delta: 0.32, residual_delta: 0.28, audio_delta_db: 0.1, cta_delta: 0 },
        ],
      })

      const html = renderToStaticMarkup(
        <ChangeMap run={run} revisedVideoUrl="blob:http://localhost:5173/checked-external-video-uuid" />
      )

      expect(html).toContain('Compare this moment')
      expect(html).not.toMatch(/<button[^>]*disabled=""[^>]*>.*?Compare this moment<\/button>/)
    })

    it('disables Compare this moment button when both run.generated_version_url and revisedVideoUrl are missing', () => {
      const run = makeMockRun({
        analysisId: 'analysis-no-video',
        generatedUrl: undefined,
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'review', visual_delta: 0.32, residual_delta: 0.28, audio_delta_db: 0.1, cta_delta: 0 },
        ],
      })

      const html = renderToStaticMarkup(<ChangeMap run={run} />)
      expect(html).toContain('Compare this moment')
      expect(html).toMatch(/<button[^>]*disabled=""[^>]*>.*?Compare this moment<\/button>/)
    })

    it('enables Compare this moment button when run.generated_version_url is present without revisedVideoUrl', () => {
      const run = makeMockRun({
        analysisId: 'analysis-generated',
        generatedUrl: '/media/generated-version.mp4',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
        ],
      })

      const html = renderToStaticMarkup(<ChangeMap run={run} />)
      expect(html).toContain('Compare this moment')
      expect(html).not.toMatch(/<button[^>]*disabled=""[^>]*>.*?Compare this moment<\/button>/)
    })
  })

  describe('Issue C: Change Map state transition from BLOCKED to PASS (Mounted DOM)', () => {
    let container: HTMLDivElement
    let root: Root

    beforeEach(() => {
      // @ts-expect-error react act environment flag
      globalThis.IS_REACT_ACT_ENVIRONMENT = true
      container = document.createElement('div')
      document.body.appendChild(container)
      root = createRoot(container)
    })

    afterEach(async () => {
      await act(async () => {
        root.unmount()
      })
      container.remove()
    })

    it('clears stale failure explanation and metrics when transitioning from BLOCKED to PASS on the same mount', async () => {
      const blockedRun = makeMockRun({
        analysisId: 'analysis-blocked-001',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'review', visual_delta: 0.32, residual_delta: 0.28, audio_delta_db: 0.1, cta_delta: 0 },
        ],
      })

      // 1. Mount ChangeMap in DOM
      await act(async () => {
        root.render(<ChangeMap run={blockedRun} />)
      })

      // 2. User clicks the failed window (0:01)
      const reviewButton = container.querySelector<HTMLButtonElement>('.map-window.map-review')!
      expect(reviewButton).not.toBeNull()

      await act(async () => {
        reviewButton.click()
      })

      // Verify active failure details in BLOCKED state
      expect(container.querySelector('.map-detail-review')).not.toBeNull()
      const blockedDetail = container.querySelector('.map-detail')!
      expect(blockedDetail.textContent).toContain('0:01–0:02 · Review needed')
      expect(blockedDetail.textContent).toContain('The observed result differs from the approved edit')
      expect(container.textContent).toContain('28.00%')

      // 3. Same mount receives new PASS props with new analysis_id (no unmount, no key change)
      const passedRun = makeMockRun({
        analysisId: 'analysis-passed-002',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.02, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
        ],
      })

      await act(async () => {
        root.render(<ChangeMap run={passedRun} revisedVideoUrl="blob:checked-pass" />)
      })

      // 4. Verify no stale failure text, class, or metrics remain
      expect(container.querySelector('.map-detail-review')).toBeNull()
      expect(container.querySelector('.map-detail-unchanged')).not.toBeNull()
      const passedDetail = container.querySelector('.map-detail')!
      expect(passedDetail.textContent).not.toContain('Review needed')
      expect(passedDetail.textContent).toContain('Unchanged')
      expect(container.textContent).not.toContain('The observed result differs from the approved edit')
      expect(container.textContent).not.toContain('28.00%')
      expect(container.textContent).toContain('These samples match the expected kept scenes')
      expect(container.textContent).toContain('0.00%')
    })

    it('updates detail metrics even when analysis_id is unchanged but window data is re-evaluated on the same mount', async () => {
      const blockedRun = makeMockRun({
        analysisId: 'analysis-same-001',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'review', visual_delta: 0.32, residual_delta: 0.28, audio_delta_db: 0.1, cta_delta: 0 },
        ],
      })

      await act(async () => {
        root.render(<ChangeMap run={blockedRun} />)
      })

      const reviewButton = container.querySelector<HTMLButtonElement>('.map-window.map-review')!
      await act(async () => {
        reviewButton.click()
      })
      expect(container.textContent).toContain('28.00%')

      // Re-evaluated run with SAME analysis_id, but second 1 is now unchanged with 0.00% residual
      const updatedRun = makeMockRun({
        analysisId: 'analysis-same-001',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.02, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
        ],
      })

      await act(async () => {
        root.render(<ChangeMap run={updatedRun} />)
      })

      // Must display updated metrics for second 1, not stale review object
      expect(container.querySelector('.map-detail-review')).toBeNull()
      expect(container.textContent).not.toContain('28.00%')
      expect(container.textContent).not.toContain('The observed result differs from the approved edit')
      expect(container.textContent).toContain('0.00%')
    })

    it('falls back safely when previously selected window disappears in the new map on the same mount', async () => {
      const blockedRun = makeMockRun({
        analysisId: 'analysis-001',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
          { second: 1, sample_count: 2, requested: false, status: 'review', visual_delta: 0.32, residual_delta: 0.28, audio_delta_db: 0.1, cta_delta: 0 },
        ],
      })

      await act(async () => {
        root.render(<ChangeMap run={blockedRun} />)
      })

      const reviewButton = container.querySelector<HTMLButtonElement>('.map-window.map-review')!
      await act(async () => {
        reviewButton.click()
      })
      expect(container.textContent).toContain('0:01–0:02')

      // New map only contains second 0; second 1 has disappeared
      const trimmedRun = makeMockRun({
        analysisId: 'analysis-002',
        windows: [
          { second: 0, sample_count: 2, requested: false, status: 'unchanged', visual_delta: 0.01, residual_delta: 0.0, audio_delta_db: 0.0, cta_delta: 0 },
        ],
      })

      await act(async () => {
        root.render(<ChangeMap run={trimmedRun} />)
      })

      // Must fallback to available window without crashing or showing stale second 1
      expect(container.querySelector('.map-detail-review')).toBeNull()
      expect(container.textContent).toContain('0:00–0:01 · Unchanged')
      expect(container.textContent).not.toContain('0:01–0:02')
      expect(container.textContent).not.toContain('28.00%')
    })
  })
})
