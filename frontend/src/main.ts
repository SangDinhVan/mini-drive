import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// Intentional type error to demonstrate CI blocking a merge.
createApp(App).mount(123)
