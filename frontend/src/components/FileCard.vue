<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FileItem } from '../types/file'
import DriveIcon from './DriveIcon.vue'

const props = defineProps<{ file: FileItem; disabled: boolean }>()
defineEmits<{ preview: [file: FileItem]; delete: [file: FileItem] }>()
const brokenImage = ref(false)
const extension = computed(() => props.file.name.includes('.') ? props.file.name.split('.').pop()!.slice(0, 8).toUpperCase() : 'FILE')
const date = computed(() => new Date(props.file.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }))
const size = computed(() => {
  const bytes = props.file.size_bytes
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
})
</script>

<template>
  <article class="file-card" :class="{ 'image-card': file.preview_url, 'document-card': ['PDF', 'DOC', 'DOCX', 'TXT'].includes(extension), 'sheet-card': ['XLS', 'XLSX', 'CSV'].includes(extension), 'pdf-card': extension === 'PDF' }">
    <div class="file-visual" :class="{ 'has-image': file.preview_url && !brokenImage }">
      <button v-if="file.preview_url && !brokenImage" class="thumbnail-button" :aria-label="`Preview ${file.name}`" @click="$emit('preview', file)">
        <img :src="file.preview_url" :alt="file.name" loading="lazy" @error="brokenImage = true" /><span class="preview-hint"><DriveIcon name="eye" /> Preview</span>
      </button>
      <template v-else><div class="file-sheet"><DriveIcon :name="file.preview_url ? 'image' : 'file'" /><span>{{ extension }}</span></div><span v-if="brokenImage" class="file-extension">UNAVAILABLE</span></template>
    </div>
    <div class="file-info"><h3 :title="file.name"><DriveIcon :name="file.preview_url ? 'image' : 'file'" /><span>{{ file.name }}</span></h3><p><span>{{ size }}</span><span>{{ date }}</span></p></div>
    <div class="file-actions">
      <button v-if="file.preview_url" class="text-button" @click="$emit('preview', file)"><DriveIcon name="eye" />Preview</button>
      <a class="text-button" :href="file.download_url" download><DriveIcon name="download" />Download</a>
      <button class="icon-button danger" :disabled="disabled" :aria-label="`Delete ${file.name}`" @click="$emit('delete', file)"><DriveIcon name="trash" /></button>
    </div>
  </article>
</template>
