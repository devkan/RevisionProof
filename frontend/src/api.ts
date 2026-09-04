import type { DemoAsset, EditInterpretation, EditMemorySearch, EditPlan, LogoAsset, RunSnapshot, RuntimeStatus, SearchEngine, TimeRange, TranscriptionLanguage, TranscriptionResult } from './types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: unknown }
    throw new Error(typeof payload.detail === 'string' ? payload.detail : `Request failed (${response.status}). Check the file and selected section, then retry.`)
  }
  return response.json() as Promise<T>
}

function mutationHeaders(key: string, json = false): HeadersInit {
  return {
    'Idempotency-Key': key,
    ...(json ? { 'Content-Type': 'application/json' } : {}),
  }
}

async function blobSha256(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer())
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, '0')).join('')
}

export const api = {
  interpretEdit: (text: string, duration: number) => request<EditInterpretation>('/api/edit-plans/interpret', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, duration, start: 0, end: duration }),
  }),
  runtime: () => request<RuntimeStatus>('/api/runtime'),
  assets: () => request<DemoAsset[]>('/api/demo-assets'),
  uploadLogo: async (file: File): Promise<LogoAsset> => {
    const form = new FormData()
    form.append('file', file)
    return request<LogoAsset>('/api/edit-assets/logo', {
      method: 'POST',
      headers: { 'X-Content-SHA256': await blobSha256(file) },
      body: form,
    })
  },
  transcribe: async (language: TranscriptionLanguage, file?: File, assetId?: string): Promise<TranscriptionResult> => {
    const form = new FormData()
    form.append('language', language)
    if (file) form.append('file', file)
    else if (assetId) form.append('asset_id', assetId)
    const headers: HeadersInit = file ? { 'X-Content-SHA256': await blobSha256(file) } : {}
    return request<TranscriptionResult>('/api/transcriptions', { method: 'POST', headers, body: form })
  },
  uploadSource: async (file: File, feedback: string, range: TimeRange, onProgress: (value: number) => void, editPlan?: EditPlan): Promise<RunSnapshot> => {
    const digest = await blobSha256(file)
    const form = new FormData()
    form.append('file', file)
    form.append('feedback', feedback)
    form.append('start_seconds', String(range.start_seconds))
    form.append('end_seconds', String(range.end_seconds))
    if (editPlan) form.append('edit_plan', JSON.stringify(editPlan))
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/runs/upload')
      xhr.setRequestHeader('Idempotency-Key', `source:${crypto.randomUUID()}`)
      xhr.setRequestHeader('X-Content-SHA256', digest)
      xhr.timeout = 240000
      xhr.upload.onprogress = (event) => { if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100)) }
      xhr.onerror = () => reject(new Error('Upload connection failed. Check your connection and try again.'))
      xhr.ontimeout = () => reject(new Error('Video preparation took too long. Try a shorter clip.'))
      xhr.onload = () => {
        let payload: { detail?: unknown }
        try { payload = JSON.parse(xhr.responseText) } catch { reject(new Error(`Upload failed (${xhr.status}). Please try again.`)); return }
        if (xhr.status >= 200 && xhr.status < 300) resolve(payload as RunSnapshot)
        else reject(new Error(typeof payload.detail === 'string' ? payload.detail : `Upload failed (${xhr.status}). Check the file and selected section.`))
      }
      xhr.send(form)
    })
  },
  searchMemory: (runId: string, engine: SearchEngine) =>
    request<EditMemorySearch>(`/api/runs/${runId}/edit-memory?engine=${engine}`),
  saveMemory: (runId: string, workspaceKey: string) =>
    request<{ memory_id: string; status: string }>(`/api/runs/${runId}/edit-memory`, {
      method: 'POST',
      headers: workspaceKey ? { 'X-Workspace-Key': workspaceKey } : {},
    }),
  createRun: (assetId: string, feedback: string, editPlan?: EditPlan) =>
    request<RunSnapshot>('/api/runs', {
      method: 'POST',
      headers: mutationHeaders(`create:${crypto.randomUUID()}`, true),
      body: JSON.stringify({ asset_id: assetId, feedback, edit_plan: editPlan }),
    }),
  retryRun: (runId: string) =>
    request<RunSnapshot>(`/api/runs/${runId}/retry`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:retry:${crypto.randomUUID()}`),
    }),
  previews: (runId: string, noteId: string, editPlan?: EditPlan) =>
    request<RunSnapshot>(`/api/runs/${runId}/previews`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:previews:${editPlan ? crypto.randomUUID() : noteId}`, true),
      body: JSON.stringify({ note_id: noteId, edit_plan: editPlan }),
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
  renderApprovedVersion: (runId: string) =>
    request<RunSnapshot>(`/api/runs/${runId}/automatic-version`, {
      method: 'POST',
      headers: mutationHeaders(`${runId}:automatic-version`),
    }),
  uploadVersion: async (runId: string, versionLabel: string, file: Blob) => {
    const contentSha256 = await blobSha256(file)
    const form = new FormData()
    form.append('version_label', versionLabel)
    form.append('file', file, `${versionLabel}.mp4`)
    return request<RunSnapshot>(`/api/runs/${runId}/versions`, {
      method: 'POST',
      headers: {
        ...mutationHeaders(`${runId}:version:${versionLabel}:${contentSha256}`),
        'X-Content-SHA256': contentSha256,
      },
      body: form,
    })
  },
  demoVersion: (runId: string, version: 'v2' | 'v3') =>
    request<RunSnapshot>(`/api/runs/${runId}/demo-versions/${version}`, {
      method: 'POST',
    }),
}
