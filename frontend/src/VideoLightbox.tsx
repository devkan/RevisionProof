import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'

export interface VideoLightboxContent {
  src: string
  title: string
  detail: string
}

export function VideoLightbox({
  content,
  onClose,
}: {
  content: VideoLightboxContent
  onClose: () => void
}) {
  const closeButton = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButton.current?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  return (
    <div
      className="video-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="video-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="video-modal-title"
        aria-describedby="video-modal-detail"
      >
        <header className="video-modal-header">
          <div>
            <span>ENLARGED PREVIEW</span>
            <h2 id="video-modal-title">{content.title}</h2>
            <p id="video-modal-detail">{content.detail}</p>
          </div>
          <button ref={closeButton} type="button" onClick={onClose} aria-label="Close enlarged video">
            <X size={19} />
          </button>
        </header>
        <div className="video-modal-stage">
          <video key={content.src} src={content.src} controls playsInline preload="metadata" />
        </div>
        <footer>Use the player controls to pause on the 00:08–00:14 punch-in.</footer>
      </section>
    </div>
  )
}

