import axios from 'axios'

export type ProblemDetail = {
  type?: string
  title?: string
  status?: number
  detail?: string
  instance?: string
  requestId?: string
  errors?: Array<{ field?: string; message?: string }>
}

export function getProblemDetail(error: unknown): ProblemDetail | null {
  if (!axios.isAxiosError(error)) {
    return null
  }
  const data = error.response?.data
  if (!data || typeof data !== 'object') {
    return null
  }
  return data as ProblemDetail
}

export function problemMessage(error: unknown, fallback: string): string {
  const problem = getProblemDetail(error)
  return problem?.detail || problem?.title || fallback
}

export function isProblemType(error: unknown, suffix: string): boolean {
  const type = getProblemDetail(error)?.type
  return typeof type === 'string' && type.endsWith(suffix)
}
