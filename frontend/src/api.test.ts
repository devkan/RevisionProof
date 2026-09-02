import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from './api'

describe('demo version API', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('uses the server-owned candidate-aware fixture endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ run_id: 'run-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.demoVersion('run-1', 'v3')

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledWith('/api/runs/run-1/demo-versions/v3', {
      method: 'POST',
    })
  })

  it('sends the user-selected request when creating previews', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ run_id: 'run-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.previews('run-1', 'note_01')

    expect(fetchMock).toHaveBeenCalledWith('/api/runs/run-1/previews', {
      method: 'POST',
      headers: {
        'Idempotency-Key': 'run-1:previews:note_01',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ note_id: 'note_01' }),
    })
  })

  it('uses the server-owned full video render endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ run_id: 'run-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.renderApprovedVersion('run-1')

    expect(fetchMock).toHaveBeenCalledWith('/api/runs/run-1/automatic-version', {
      method: 'POST',
      headers: { 'Idempotency-Key': 'run-1:automatic-version' },
    })
  })
})
