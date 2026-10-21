import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import OverlayView from './components/analysis/OverlayView.vue'

const isOverlay = new URLSearchParams(window.location.search).has('overlay')
if (isOverlay) {
  document.documentElement.classList.add('overlay-mode')
  document.body.classList.add('overlay-mode')
}
createApp(isOverlay ? OverlayView : App).mount('#app')
