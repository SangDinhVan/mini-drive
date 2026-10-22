<script setup lang="ts">
import type { FileItem } from '../types/file'
import FileCard from './FileCard.vue'

defineProps<{ files: FileItem[]; disabled: boolean }>()
defineEmits<{ preview: [file: FileItem]; delete: [file: FileItem] }>()
</script>

<template>
  <div class="file-grid"><FileCard v-for="file in files" :key="file.id" :file="file" :disabled="disabled" @preview="$emit('preview', $event)" @delete="$emit('delete', $event)" /></div>
</template>
