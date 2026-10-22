<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { FileItem } from '../types/file'
import DriveIcon from './DriveIcon.vue'

const props = defineProps<{ file: FileItem | null; busy: boolean; error: string }>()
const emit = defineEmits<{ cancel: []; confirm: [] }>()
const dialog = ref<HTMLDialogElement>()
const cancelButton = ref<HTMLButtonElement>()

watch(() => props.file, async (file) => {
  await nextTick()
  if (file && !dialog.value?.open) {
    dialog.value?.showModal()
    cancelButton.value?.focus()
  } else if (!file && dialog.value?.open) dialog.value.close()
})

function cancel() {
  if (!props.busy) emit('cancel')
}
</script>

<template>
  <dialog ref="dialog" class="delete-dialog" aria-labelledby="delete-title" aria-describedby="delete-description" @cancel.prevent="cancel" @click="($event.target === dialog) && cancel()">
    <div class="dialog-content"><div class="delete-mark"><DriveIcon name="trash" /></div><span class="eyebrow">A little housekeeping</span><h2 id="delete-title">Delete this file?</h2>
      <p id="delete-description"><strong>{{ file?.name }}</strong> will be removed from your drive. This cannot be undone.</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions"><button ref="cancelButton" class="button secondary" :disabled="busy" @click="cancel">Keep file</button><button class="button destructive" :disabled="busy" @click="$emit('confirm')">{{ busy ? 'Deleting...' : 'Delete file' }}</button></div>
    </div>
  </dialog>
</template>
