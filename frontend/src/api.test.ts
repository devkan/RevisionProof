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
})
