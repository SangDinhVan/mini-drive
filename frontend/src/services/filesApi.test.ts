import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, deleteFile, listFiles, uploadFile } from './filesApi'

afterEach(() => vi.unstubAllGlobals())

describe('files API', () => {
  it('reads the list using a relative URL', async () => {
    const item = { id: 'one', name: 'notes.txt', size_bytes: 5, content_type: 'application/octet-stream', created_at: '2026-10-13T08:00:00Z', download_url: '/api/files/one/content?download=1', preview_url: null }
    const fetchMock = vi.fn().mockResolvedValue(Response.json([item]))
    vi.stubGlobal('fetch', fetchMock)
    expect(await listFiles()).toEqual([item])
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/files')
  })

  it('uploads the original file as multipart without forcing a content type', async () => {
    const file = new File(['hello'], 'notes.txt')
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ id: 'one' }, { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)
    await uploadFile(file)
    const [url, options] = fetchMock.mock.calls[0]!
    expect(url).toBe('/api/files')
    expect(options.method).toBe('POST')
    expect(options.body.get('file').name).toBe('notes.txt')
    expect(options.body.get('file').size).toBe(5)
    expect(options.headers).toBeUndefined()
  })

  it('accepts an empty 204 delete response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(deleteFile('one')).resolves.toBeUndefined()
    expect(fetchMock.mock.calls[0]).toEqual(['/api/files/one', { method: 'DELETE' }])
  })

  it('preserves actionable API error details and status', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ detail: 'Too large' }, { status: 413 })))
    await expect(uploadFile(new File(['x'], 'x.txt'))).rejects.toMatchObject({ message: 'Too large', status: 413 })
  })

  it('handles proxy errors with non-JSON responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad gateway', { status: 502 })))
    await expect(listFiles()).rejects.toBeInstanceOf(ApiError)
  })

  it('explains a disconnected server', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(listFiles()).rejects.toMatchObject({ status: 0 })
  })
})
