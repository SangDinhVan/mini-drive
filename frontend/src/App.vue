<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import UploadDropzone from './components/UploadDropzone.vue'
import FileGrid from './components/FileGrid.vue'
import ConfirmDeleteDialog from './components/ConfirmDeleteDialog.vue'
import DriveIcon from './components/DriveIcon.vue'
import { deleteFile, listFiles, uploadFile } from './services/filesApi'
import type { FileItem, UploadEntry } from './types/file'

const files = ref<FileItem[]>([])
const search = ref('')
const category = ref<'all' | 'photos' | 'other'>('all')
const pageTitle = computed(() => ({ all: 'My Drive', photos: 'Photos', other: 'Other files' })[category.value])
const photoCount = computed(() => files.value.filter((file) => file.preview_url).length)
const filteredFiles = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()
  return files.value.filter((file) => {
    const matchesType = category.value === 'all' || (category.value === 'photos' ? Boolean(file.preview_url) : !file.preview_url)
    return matchesType && file.name.toLocaleLowerCase().includes(query)
  })
})

function clearFilters() {
  search.value = ''
  category.value = 'all'
}

const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const uploads = ref<UploadEntry[]>([])
const deleting = ref(false)
const deleteTarget = ref<FileItem | null>(null)
const deleteError = ref('')
const preview = ref<FileItem | null>(null)
const previewFailed = ref(false)
const previewDialog = ref<HTMLDialogElement>()
const totalSize = computed(() => {
  const bytes = files.value.reduce((sum, file) => sum + file.size_bytes, 0)
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`
})
const completed = computed(() => uploads.value.filter((entry) => entry.status === 'success').length)
const message = (cause: unknown) => cause instanceof Error ? cause.message : 'Something went wrong. Please try again.'

async function loadFiles() {
  loading.value = true
  error.value = ''
  try { files.value = await listFiles() }
  catch (cause) { error.value = message(cause) }
  finally { loading.value = false }
}

async function handleFiles(selected: File[]) {
  if (uploading.value || selected.length === 0) return
  uploading.value = true
  uploads.value = selected.map((file) => ({ name: file.name, status: 'waiting' }))
  for (const [index, file] of selected.entries()) {
    const entry = uploads.value[index]!
    entry.status = 'uploading'
    try {
      const item = await uploadFile(file)
      files.value = [item, ...files.value].slice(0, 100)
      entry.status = 'success'
    } catch (cause) {
      entry.status = 'error'
      entry.error = message(cause)
    }
  }
  if (error.value && completed.value > 0) await loadFiles()
  uploading.value = false
}

function askDelete(file: FileItem) {
  deleteError.value = ''
  deleteTarget.value = file
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    const id = deleteTarget.value.id
    await deleteFile(id)
    files.value = files.value.filter((file) => file.id !== id)
    deleteTarget.value = null
  } catch (cause) { deleteError.value = message(cause) }
  finally { deleting.value = false }
}

watch(preview, async (file) => {
  await nextTick()
  previewFailed.value = false
  if (file && !previewDialog.value?.open) previewDialog.value?.showModal()
  else if (!file && previewDialog.value?.open) previewDialog.value.close()
})

onMounted(loadFiles)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Drive navigation">
      <a class="brand" href="/" aria-label="Mini Drive home"><span class="brand-mark"><DriveIcon name="folder" /></span><span>Mini Drive<small>Personal workspace</small></span></a>
      <span class="nav-heading">LIBRARY</span>
      <nav>
        <button class="nav-item" :class="{ active: category === 'all' }" :aria-current="category === 'all' ? 'page' : undefined" aria-label="Show all files" @click="category = 'all'"><DriveIcon name="folder" /><span>My Drive</span><span class="nav-count">{{ files.length }}</span></button>
        <button class="nav-item" :class="{ active: category === 'photos' }" :aria-current="category === 'photos' ? 'page' : undefined" aria-label="Show photos" @click="category = 'photos'"><DriveIcon name="image" /><span>Photos</span><span class="nav-count">{{ photoCount }}</span></button>
        <button class="nav-item" :class="{ active: category === 'other' }" :aria-current="category === 'other' ? 'page' : undefined" aria-label="Show other files" @click="category = 'other'"><DriveIcon name="file" /><span>Other files</span><span class="nav-count">{{ files.length - photoCount }}</span></button>
      </nav>
      <div class="sidebar-bottom"><div class="storage-label"><DriveIcon name="storage" /><span>Your collection</span></div><strong>{{ totalSize }}</strong><p>{{ files.length }} files saved</p><div class="workspace-label"><span class="workspace-avatar">M</span><div>Personal drive<small>Mini Drive v1.0</small></div></div></div>
    </aside>
    <div class="workspace">
      <header class="site-header">
        <div class="breadcrumb"><DriveIcon name="folder" /><span>My Drive</span><DriveIcon name="chevron" /><strong>{{ category === 'all' ? 'All files' : pageTitle }}</strong></div>
        <div class="search-field"><DriveIcon name="search" /><input v-model="search" type="search" aria-label="Search files" placeholder="Search your files..." /><button v-if="search" class="icon-button" aria-label="Clear search" @click="search = ''"><DriveIcon name="close" /></button></div>
        <span class="header-avatar" aria-label="Personal workspace">M</span>
      </header>
    <main>
      <div class="page-heading"><div><h1>{{ pageTitle }}</h1><p>Your files, right where you need them.</p></div><button class="button secondary refresh-button" :disabled="loading || uploading || deleting" @click="loadFiles"><DriveIcon name="refresh" :class="{ spinning: loading }" />Refresh</button></div>
      <UploadDropzone :disabled="uploading || loading" @files="handleFiles" />
      <section v-if="uploads.length" class="upload-status" aria-label="Upload status" aria-live="polite">
        <div class="queue-heading"><strong>{{ uploading ? 'Adding to your drive...' : `${completed} of ${uploads.length} files uploaded` }}</strong><button v-if="!uploading" class="text-button" @click="uploads = []">Dismiss <DriveIcon name="close" /></button></div>
        <ul><li v-for="(entry, index) in uploads" :key="index" :class="entry.status"><span class="queue-name">{{ entry.name }}</span><span class="queue-state"><DriveIcon v-if="entry.status === 'success'" name="check" />{{ entry.status === 'error' ? entry.error : entry.status === 'success' ? 'Uploaded' : entry.status === 'uploading' ? 'Uploading...' : 'Waiting' }}</span></li></ul>
      </section>
      <section class="collection" aria-labelledby="collection-title"><div class="collection-heading"><h2 id="collection-title">Files <span class="count-badge">{{ filteredFiles.length }}</span></h2><span class="sort-label">Newest first <DriveIcon name="chevron" /></span></div>
        <div v-if="loading" class="empty-state" role="status"><span class="loading-ring"></span><h3>Opening your drive...</h3><p>Getting everything in place.</p></div>
        <div v-else-if="error" class="empty-state connection-error" role="alert"><div class="empty-icon"><DriveIcon name="folder" /></div><h3>We couldn't open your drive.</h3><p>{{ error }}</p><button class="button primary" :disabled="uploading || deleting" @click="loadFiles">Try again <DriveIcon name="arrow" /></button></div>
        <div v-else-if="!files.length" class="empty-state"><div class="empty-icon"><DriveIcon name="folder" /></div><span class="eyebrow">A fresh start</span><h3>Your space is waiting.</h3><p>Add your first file using the upload area above.<br />Photos, documents, or something worth keeping.</p></div>
        <div v-else-if="!filteredFiles.length" class="empty-state" role="status"><div class="empty-icon"><DriveIcon name="search" /></div><h3>No matching files</h3><p>Try a different name or browse all your files.</p><button class="button secondary" aria-label="Clear filters" @click="clearFilters">Clear filters</button></div>
        <FileGrid v-else :files="filteredFiles" :disabled="uploading || deleting" @preview="preview = $event" @delete="askDelete" />
        <p v-if="files.length === 100" class="collection-limit">Showing the 100 most recent files.</p>
      </section>
    </main>
    <footer class="site-footer"><span>{{ filteredFiles.length }} files<span v-if="search.trim() || category !== 'all'"> matching your filters</span></span><span>{{ totalSize }} in collection</span></footer>
    </div>
  </div>
  <ConfirmDeleteDialog :file="deleteTarget" :busy="deleting" :error="deleteError" @cancel="deleteTarget = null" @confirm="confirmDelete" />
  <dialog ref="previewDialog" class="preview-dialog" aria-labelledby="preview-title" @cancel.prevent="preview = null" @click="($event.target === previewDialog) && (preview = null)">
    <div class="preview-header"><h2 id="preview-title">{{ preview?.name }}</h2><button class="icon-button" aria-label="Close preview" @click="preview = null"><DriveIcon name="close" /></button></div>
    <div class="preview-image"><p v-if="previewFailed" role="alert">This image is unavailable. It may have been removed from local storage.</p><img v-else-if="preview?.preview_url" :src="preview.preview_url" :alt="preview.name" @error="previewFailed = true" /></div>
    <div class="preview-footer"><a v-if="preview" class="button primary" :href="preview.download_url" download><DriveIcon name="download" />Download original</a></div>
  </dialog>
</template>
