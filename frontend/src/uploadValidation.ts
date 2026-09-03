import type { RuntimeStatus, TimeRange } from './types'

export const DEFAULT_UPLOAD_LIMITS = { max_bytes: 24 * 1024 * 1024, max_duration_seconds: 60, min_duration_seconds: 4 }
export const limitsFor = (runtime: RuntimeStatus | null) => runtime?.upload_limits ?? DEFAULT_UPLOAD_LIMITS

export function fileValidation(file: Pick<File, 'size' | 'name'>, limits = DEFAULT_UPLOAD_LIMITS): string | null {
  if (!file.size) return 'This file is empty. Choose a video with content.'
  if (file.size > limits.max_bytes) return `This video is ${(file.size / 1048576).toFixed(1)} MiB. The maximum is ${limits.max_bytes / 1048576} MiB. Choose a smaller file.`
  if (!/\.(mp4|mov|webm)$/i.test(file.name)) return 'Choose an MP4, MOV, or WebM video.'
  return null
}

export function rangeValidation(range: TimeRange, duration: number): string | null {
  const { start_seconds: start, end_seconds: end } = range
  if (![start, end, duration].every(Number.isFinite) || start < 0 || end > duration) return 'Keep the selected section inside the video.'
  if (end - start < 4 || end - start > 8) return 'Select a section between 4 and 8 seconds long.'
  return null
}
