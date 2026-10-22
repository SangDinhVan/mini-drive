// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import App from './App.vue'
import UploadDropzone from './components/UploadDropzone.vue'
import FileGrid from './components/FileGrid.vue'
import ConfirmDeleteDialog from './components/ConfirmDeleteDialog.vue'

HTMLDialogElement.prototype.showModal = function () { this.open = true }
HTMLDialogElement.prototype.close = function () { this.open = false }

afterEach(() => vi.unstubAllGlobals())

const item = { id: 'one', name: 'notes.txt', size_bytes: 5, content_type: 'application/octet-stream', created_at: '2026-10-13T08:00:00Z', download_url: '/api/files/one/content?download=1', preview_url: null }

describe('drive workflow', () => {
  it('filters the grid by filename and file type, including no matching results', async () => {
    const photo = { ...item, id: 'photo', name: 'Summer.PNG', content_type: 'image/png', preview_url: '/api/files/photo/content' }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json([item, photo])))
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('input[type="search"]').setValue(' SUMMER ')
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    expect(wrapper.find('.file-card').text()).toContain('Summer.PNG')
    await wrapper.get('input[type="search"]').setValue('')
    await wrapper.get('button[aria-label="Show photos"]').trigger('click')
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    await wrapper.get('input[type="search"]').setValue('notes')
    expect(wrapper.findAll('.file-card')).toHaveLength(0)
    expect(wrapper.text()).toContain('No matching files')
    await wrapper.get('button[aria-label="Clear filters"]').trigger('click')
    expect(wrapper.findAll('.file-card')).toHaveLength(2)
    await wrapper.get('button[aria-label="Show other files"]').trigger('click')
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    expect(wrapper.find('.file-card').text()).toContain('notes.txt')
    wrapper.unmount()
  })

  it('continues sequential uploads after a failed file', async () => {
    let finishFirst!: (value: Response) => void
    const firstResponse = new Promise<Response>((resolve) => { finishFirst = resolve })
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json([])).mockReturnValueOnce(firstResponse).mockResolvedValueOnce(Response.json(item, { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(App)
    await flushPromises()
    wrapper.findComponent(UploadDropzone).vm.$emit('files', [new File(['bad'], 'bad.txt'), new File(['hello'], 'notes.txt')])
    await flushPromises()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    finishFirst(Response.json({ detail: 'Upload failed' }, { status: 500 }))
    await flushPromises()
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(wrapper.text()).toContain('Upload failed')
    expect(wrapper.text()).toContain('1 of 2 files uploaded')
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    wrapper.unmount()
  })

  it('keeps a failed deletion retryable until it succeeds', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json([item])).mockResolvedValueOnce(Response.json({ detail: 'Database unavailable' }, { status: 503 })).mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(App)
    await flushPromises()
    wrapper.findComponent(FileGrid).vm.$emit('delete', item)
    await flushPromises()
    wrapper.findComponent(ConfirmDeleteDialog).vm.$emit('confirm')
    await flushPromises()
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    expect(wrapper.findComponent(ConfirmDeleteDialog).text()).toContain('Database unavailable')
    wrapper.findComponent(ConfirmDeleteDialog).vm.$emit('confirm')
    await flushPromises()
    expect(wrapper.findAll('.file-card')).toHaveLength(0)
    expect(wrapper.text()).toContain('Your space is waiting.')
    wrapper.unmount()
  })

  it('refreshes the collection after uploads recover from an initial connection error', async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(Response.json(item, { status: 201 })).mockResolvedValueOnce(Response.json([item]))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.text()).toContain("We couldn't open your drive.")
    wrapper.findComponent(UploadDropzone).vm.$emit('files', [new File(['hello'], 'notes.txt')])
    await flushPromises()
    expect(wrapper.findAll('.file-card')).toHaveLength(1)
    expect(wrapper.text()).not.toContain("We couldn't open your drive.")
    wrapper.unmount()
  })

  it('removes a stale card when deletion reports the file is already gone', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(Response.json([item])).mockResolvedValueOnce(Response.json({ detail: 'File not found' }, { status: 404 })))
    const wrapper = mount(App)
    await flushPromises()
    wrapper.findComponent(FileGrid).vm.$emit('delete', item)
    await flushPromises()
    wrapper.findComponent(ConfirmDeleteDialog).vm.$emit('confirm')
    await flushPromises()
    expect(wrapper.findAll('.file-card')).toHaveLength(0)
    expect(wrapper.findComponent(ConfirmDeleteDialog).props('file')).toBeNull()
    wrapper.unmount()
  })
})
