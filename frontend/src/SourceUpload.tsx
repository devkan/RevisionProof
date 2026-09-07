import { useRef, useState } from 'react'
import { Film, Upload } from 'lucide-react'
import type { DemoAsset, RuntimeStatus } from './types'
import { fileValidation, formatUploadSize, limitsFor } from './uploadValidation'

export interface UploadedSource { file: File; asset: DemoAsset }

export function SourceUpload({ runtime, selected, disabled, onSelect }: {
  runtime: RuntimeStatus | null; selected: UploadedSource | null; disabled: boolean
  onSelect: (source: UploadedSource | null) => void
}) {
  const input = useRef<HTMLInputElement>(null)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const limits = limitsFor(runtime)
  async function choose(file?: File) {
    if (!file || disabled || checking) return
    const problem = fileValidation(file, limits)
    setError(problem)
    if (problem) return
    setChecking(true)
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    try {
      await new Promise<void>((resolve, reject) => {
        const timer = window.setTimeout(() => { video.onloadedmetadata = null; video.onerror = null; reject(new Error('Video preview timed out. Try an H.264 MP4.')) }, 10000)
        video.onloadedmetadata = () => { clearTimeout(timer); resolve() }
        video.onerror = () => { clearTimeout(timer); reject(new Error('Your browser cannot preview this video. Export as H.264 MP4 and try again.')) }
        video.src = url
      })
      if (!Number.isFinite(video.duration) || video.duration < limits.min_duration_seconds || video.duration > limits.max_duration_seconds) throw new Error(`This video is ${Number.isFinite(video.duration) ? video.duration.toFixed(1) : 'an unknown number of'} seconds long. Choose a ${limits.min_duration_seconds}–${limits.max_duration_seconds} second clip.`)
      if (video.videoWidth > 4096 || video.videoHeight > 4096) throw new Error('Choose a video no larger than 4096 pixels per side.')
      onSelect({ file, asset: { asset_id: 'local-upload', title: file.name, source_url: url,
        duration_seconds: video.duration, width: video.videoWidth, height: video.videoHeight, codec: 'Your original video', source_kind: 'upload' } })
    } catch (reason) {
      URL.revokeObjectURL(url)
      setError(reason instanceof Error ? reason.message : 'This video could not be opened.')
    } finally {
      video.removeAttribute('src'); video.load()
      setChecking(false)
    }
  }
  return <div className="source-picker" aria-busy={checking}>
    <div className="source-picker-actions">
      <button type="button" className="primary-button" disabled={disabled || checking} onClick={() => input.current?.click()}><Upload size={18} />{checking ? 'Checking video…' : selected ? 'Choose another video' : 'Upload your video'}</button>
      {selected ? <button type="button" className="secondary-button" disabled={disabled || checking} onClick={() => { setError(null); onSelect(null) }}><Film size={18} />Use sample instead</button> : <span className="input-help">Or explore with the sample below.</span>}
    </div>
    <input ref={input} hidden type="file" accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm" aria-label="Upload original video" disabled={disabled || checking} onChange={(event) => { void choose(event.target.files?.[0]); event.target.value = '' }} />
    <p className="input-help">MP4, MOV or WebM · up to {formatUploadSize(limits.max_bytes)} · {limits.min_duration_seconds}–{limits.max_duration_seconds}s. Videos are prepared at 1280×720 with their aspect ratio preserved.</p>
    {error && <p className="upload-warning" role="alert">{error}</p>}
  </div>
}
