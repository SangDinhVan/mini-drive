<script setup lang="ts">
withDefaults(defineProps<{ name: 'folder' | 'upload' | 'download' | 'trash' | 'image' | 'file' | 'eye' | 'refresh' | 'close' | 'check' | 'arrow' | 'search' | 'chevron' | 'storage' }>(), { name: 'file' })

const paths = {
  folder: 'M3 7h6l2 3h10v10H3z M3 7V4h6l2 3h7',
  upload: 'M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6',
  download: 'M12 3v13m-5-5 5 5 5-5M4 16v5h16v-5',
  trash: 'M4 7h16M9 7V3h6v4M6 7l1 14h10l1-14M10 11v6m4-6v6',
  image: 'M3 3h18v18H3z M3 17l6-6 5 5 3-3 4 4 M8 7h.01',
  file: 'M5 3h9l5 5v13H5z M14 3v6h5M9 13h6m-6 4h4',
  eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
  refresh: 'M20 7V3m0 4h-4M4 17v4m0-4h4M20 7a9 9 0 0 0-15 0m-1 10a9 9 0 0 0 15 0',
  close: 'm6 6 12 12M6 18 18 6',
  check: 'm5 12 4 4L19 6',
  arrow: 'M5 12h14m-5-5 5 5-5 5',
  search: 'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
  chevron: 'm9 6 6 6-6 6',
  storage: 'M4 4h16v16H4zM4 14h16M8 17h.01m4 0h.01',
}
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[name]" /></svg>
</template>
