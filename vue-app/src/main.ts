import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import OverlayView from './components/analysis/OverlayView.vue'

const isOverlay = new URLSearchParams(window.location.search).has('overlay')
createApp(isOverlay ? OverlayView : App).mount('#app')
