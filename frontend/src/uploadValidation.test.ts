import { describe, expect, it } from 'vitest'
import { fileValidation, rangeValidation, DEFAULT_UPLOAD_LIMITS } from './uploadValidation'

describe('original video upload limits', () => {
  it('accepts the exact byte boundary and rejects one byte over it before upload', () => {
    const file = { name: '내 영상.mp4', size: DEFAULT_UPLOAD_LIMITS.max_bytes }
    expect(fileValidation(file)).toBeNull()
    expect(fileValidation({ ...file, size: file.size + 1 })).toContain('maximum is 24 MiB')
  })
  it('uses server limits and validates empty and unsupported files', () => {
    expect(fileValidation({ name: 'clip.MOV', size: 1024 })).toBeNull()
    expect(fileValidation({ name: 'clip.webm', size: 10 })).toBeNull()
    expect(fileValidation({ name: 'clip.mp4', size: 0 })).toContain('empty')
    expect(fileValidation({ name: 'clip.txt', size: 100 })).toContain('MP4, MOV, or WebM')
    expect(fileValidation({ name: 'clip.mp4', size: 200 }, { ...DEFAULT_UPLOAD_LIMITS, max_bytes: 100 })).toContain('maximum')
  })
  it('accepts clip-boundary edits but rejects invalid, short or out-of-video ranges', () => {
    expect(rangeValidation({ start_seconds: 0, end_seconds: 4 }, 4)).toBeNull()
    expect(rangeValidation({ start_seconds: 52, end_seconds: 60 }, 60)).toBeNull()
    for (const range of [{ start_seconds: NaN, end_seconds: 6 }, { start_seconds: -1, end_seconds: 6 }, { start_seconds: 3, end_seconds: 11 }]) expect(rangeValidation(range, 10)).not.toBeNull()
    expect(rangeValidation({ start_seconds: 2, end_seconds: 5 }, 10)).toContain('4 and 8')
  })
})
