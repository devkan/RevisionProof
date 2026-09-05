import type { ReactNode } from 'react'
import { AlertTriangle, ChevronDown } from 'lucide-react'

export function StudioRevisionCard({ index, title, detail, status, expanded, disabled, editable, issues, onToggle, children }: {
  index: number
  title: string
  detail: string
  status: 'ready' | 'check' | 'skipped'
  expanded: boolean
  disabled: boolean
  editable: boolean
  issues: string[]
  onToggle: () => void
  children: ReactNode
}) {
  const triggerId = `studio-revision-${index}-trigger`
  const panelId = `studio-revision-${index}-settings`
  const issueId = `studio-revision-${index}-issues`
  const open = editable && expanded
  return (
    <li className={`studio-revision-card ${open ? 'is-selected' : ''} ${issues.length ? 'has-issue' : ''}`}>
      <button type="button" className="studio-revision-trigger" id={triggerId} disabled={disabled || !editable}
        aria-expanded={editable ? open : undefined} aria-controls={editable ? panelId : undefined}
        aria-describedby={open && issues.length ? issueId : undefined} onClick={onToggle}>
        <span className="studio-revision-number">{String(index + 1).padStart(2, '0')}</span>
        <span className="studio-revision-summary"><strong>{title}</strong><small>{detail}</small>
          {editable && <span className="studio-revision-hint">{open ? 'Hide settings' : 'Edit settings'}</span>}
        </span>
        <span className="studio-revision-state"><em className={`studio-tag ${issues.length ? 'is-warning' : status === 'skipped' ? 'is-muted' : 'is-ready'}`}>{issues.length ? 'needs fix' : status}</em>
          {editable && <ChevronDown size={17} aria-hidden="true" />}
        </span>
      </button>
      {editable && <div id={panelId} className="studio-revision-panel" role="region" aria-labelledby={triggerId} hidden={!open}>
        {open && <>
          {issues.length > 0 && <div id={issueId} className="studio-revision-issues" role="status"><strong><AlertTriangle size={16} />Needs attention</strong>{issues.map((message) => <p key={message}>{message}</p>)}</div>}
          {children}
        </>}
      </div>}
    </li>
  )
}
