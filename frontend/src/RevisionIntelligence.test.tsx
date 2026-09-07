import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { ChangeMap, ComparisonDialog, EditMemory, SaveApprovedMemory } from './RevisionIntelligence'
import { RequestDraft } from './EditComposer'
import type { RunSnapshot, RuntimeStatus } from './types'

const base = {
  run_id: 'test-run',
  asset: { source_url: '/source.mp4' },
  delivery_approved: false,
  generated_version_url: '/revised.mp4',
  change_map: {
    status: 'ready', source: 'fixture.frame_analysis', duration_seconds: 30,
    message: 'Two samples per second. Diagnostics, not additional checks.',
    windows: [{ second: 8, sample_count: 2, requested: true, status: 'requested',
      visual_delta: 0.1, residual_delta: 0.01, audio_delta_db: 0.1, cta_delta: 0 }],
  },
} as RunSnapshot

describe('revision intelligence presentation', () => {
  it('keeps smart scene finder opt-in and requires explicit time by default', () => {
    const html = renderToStaticMarkup(<RequestDraft text="Zoom the dashboard" onText={vi.fn()} duration={30} disabled={false} onApply={vi.fn()} onBusy={vi.fn()} assetId="01M00000000000000000000000" mode="LIVE" onSceneSelect={vi.fn()} />)
    expect(html).toContain('type="checkbox"')
    expect(html).toContain('Smart scene finder')
    expect(html).toContain('Scene time')
    expect(html).toContain('Enter both times')
    expect(html).toContain('disabled=""')
  })
  it('labels sampled evidence and exposes a named time-window button', () => {
    const html = renderToStaticMarkup(<ChangeMap run={base} />)
    expect(html).toContain('0:08 to 0:09: Requested edit')
    expect(html).toContain('aria-pressed="true"')
    expect(html).toContain('Compare this moment')
    expect(html).toContain('No sampled review flags')
    expect(html).not.toContain('Every frame')
  })
  it('shows an unavailable map rather than a successful timeline', () => {
    const run = { ...base, change_map: { ...base.change_map!, status: 'unavailable' as const } }
    const html = renderToStaticMarkup(<ChangeMap run={run} />)
    expect(html).toContain('role="status"')
    expect(html).not.toContain('No sampled review flags')
    expect(html).not.toContain('Compare this moment')
  })
  it('provides a native modal and one shared seek control for two videos', () => {
    const html = renderToStaticMarkup(<ComparisonDialog original="/source.mp4" revised="/revised.mp4" second={8} duration={30} onClose={vi.fn()} />)
    expect(html).toContain('<dialog')
    expect(html).toContain('aria-labelledby="comparison-title"')
    expect(html.match(/<video/g)).toHaveLength(2)
    expect(html).toContain('Close video comparison')
    expect(html).toContain('type="range"')
    expect(html).toContain('Play both')
  })
  it('keeps an empty read-only library optional and hides unusable search controls', () => {
    const run = { ...base, edit_memory: { status: 'empty' as const, requested_engine: 'hnsw' as const,
      actual_engine: 'none' as const, source: 'mcp-clickhouse.run_query' as const,
      collection_size: 0, elapsed_ms: 5, index_verified: false, precision_bits: null, matches: [], message: 'Small library' } }
    const html = renderToStaticMarkup(<EditMemory run={run} runtime={{ memory_save_policy: 'read_only' } as RuntimeStatus} disabled={false} />)
    expect(html).toContain('Optional reference')
    expect(html).not.toContain('<select')
    expect(html).not.toContain('index verified')
    expect(html).toContain('No saved edits yet.')
    expect(html).toContain('Saving past edits is turned off')
  })
  it('does not expose public save actions for a read-only deployment', () => {
    const runtime = { memory_save_policy: 'read_only' } as RuntimeStatus
    const html = renderToStaticMarkup(<SaveApprovedMemory run={base} runtime={runtime} disabled={false} onSaved={vi.fn()} />)
    expect(html).toContain('read-only library')
    expect(html).not.toContain('<button')
  })
  it('disables fixture memory save until final approval', () => {
    const runtime = { memory_save_policy: 'local_rehearsal' } as RuntimeStatus
    const html = renderToStaticMarkup(<SaveApprovedMemory run={base} runtime={runtime} disabled={false} onSaved={vi.fn()} />)
    expect(html).toContain('disabled=""')
    expect(html).toContain('Local rehearsal only')
    expect(html).toContain('Available after final delivery approval')
  })
})
