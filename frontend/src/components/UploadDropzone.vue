<script setup lang="ts">
import { ref } from 'vue'
import DriveIcon from './DriveIcon.vue'

defineProps<{ disabled: boolean }>()
const emit = defineEmits<{ files: [files: File[]] }>()
const input = ref<HTMLInputElement>()
const dragDepth = ref(0)

function select(event: Event) {
  const target = event.target as HTMLInputElement
  emit('files', Array.from(target.files ?? []))
  target.value = ''
}

function drop(event: DragEvent, disabled: boolean) {
  dragDepth.value = 0
  if (!disabled) emit('files', Array.from(event.dataTransfer?.files ?? []))
}
</script>

<template>
  <section class="dropzone" :class="{ 'is-dragging': dragDepth > 0 && !disabled, 'is-disabled': disabled }"
    aria-label="Upload files" :aria-busy="disabled" @dragenter.prevent="dragDepth++"
    @dragleave.prevent="dragDepth = Math.max(0, dragDepth - 1)" @dragover.prevent @drop.prevent="drop($event, disabled)">
    <div class="upload-art"><DriveIcon name="upload" /></div>
    <div class="dropzone-copy"><h2>Drag &amp; drop files to upload</h2><p>Or choose files from your computer. You can add multiple files at once.</p></div>
    <button class="button primary" :disabled="disabled" @click="input?.click()"><DriveIcon name="upload" />{{ disabled ? 'Uploading...' : 'Upload files' }}</button>
    <input ref="input" class="visually-hidden" type="file" multiple tabindex="-1" aria-label="Choose files to upload" :disabled="disabled" @change="select" />
  </section>
</template>
