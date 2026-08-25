import type { DemoAsset, RunSnapshot, RuntimeStatus } from './types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(payload.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

function mutationHeaders(key: string, json = false): HeadersInit {
  return {
    'Idempotency-Key': key,
    ...(json ? { 'Content-Type': 'application/json' } : {}),
  }
}

export const api = {
  runtime: () => request<RuntimeStatus>('/api/runtime'),
  assets: () => request<DemoAsset[]>('/api/demo-assets'),
  createRun: (assetId: string, feedback: string) =>
    request<RunSnapshot>('/api/runs', {
      method: 'POST',
      headers: mutationHeaders(`create:${crypto.randomUUID()}`, true),
      body: JSON.stringify({ asset_id: assetId, feedback }),
    }),
  previews: (runId: string) =>
    request<RunSnapshot>(`/api/runs/${runId}/previews`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:previews`),
    }),
  approve: (runId: string, candidateId: 'A' | 'B') =>
    request<RunSnapshot>(`/api/runs/${runId}/approvals`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:approval:${candidateId}`, true),
      body: JSON.stringify({ candidate_id: candidateId }),
    }),
  approveForDelivery: (runId: string) =>
    request<RunSnapshot>(`/api/runs/${runId}/delivery-approval`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:delivery-approval`),
    }),
  uploadVersion: (runId: string, versionLabel: string, file: Blob) => {
    const form = new FormData()
    form.append('version_label', versionLabel)
    form.append('file', file, `${versionLabel}.mp4`)
    return request<RunSnapshot>(`/api/runs/${runId}/versions`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:version:${versionLabel}:${file.size}`),
      body: form,
    })
  },
  demoVersion: async (runId: string, version: 'v2' | 'v3') => {
    const filename = version === 'v2' ? 'revisionproof_v2_blocked.mp4' : 'revisionproof_v3_ready.mp4'
    const response = await fetch(`/media/demo/${filename}`)
    if (!response.ok) throw new Error(`Demo ${version} fixture is unavailable`)
    return api.uploadVersion(runId, version, await response.blob())
  },
}
