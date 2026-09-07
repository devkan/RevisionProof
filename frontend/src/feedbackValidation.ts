export const MIN_FEEDBACK_LENGTH = 8

export function feedbackValidationMessage(feedback: string): string | null {
  const remaining = MIN_FEEDBACK_LENGTH - feedback.length
  if (remaining <= 0) return null
  return `Client feedback must be at least ${MIN_FEEDBACK_LENGTH} characters (${remaining} more needed).`
}
