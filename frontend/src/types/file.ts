export interface FileItem {
  id: string
  name: string
  content_type: string | null
  size_bytes: number
  created_at: string
  download_url: string
  preview_url: string | null
}

export interface UploadEntry {
  name: string
  status: 'waiting' | 'uploading' | 'success' | 'error'
  error?: string
}
