import type { FileItem } from '../types/file'

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, options)
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status}). Check the server and try again.`
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function listFiles(): Promise<FileItem[]> {
  return request('/api/files')
}

export function uploadFile(file: File): Promise<FileItem> {
  const body = new FormData()
  body.append('file', file)
  return request('/api/files', { method: 'POST', body })
}

export function deleteFile(id: string): Promise<void> {
  return request<void>(`/api/files/${encodeURIComponent(id)}`, { method: 'DELETE' }).catch((error: unknown) => {
    // A missing row already has the requested final state.
    if (!(error instanceof ApiError && error.status === 404)) throw error
  })
}
