import { ref, computed } from 'vue'

/**
 * Composable for Document Picture-in-Picture API with Video Fallback
 * @see https://developer.chrome.com/docs/web-platform/document-picture-in-picture/
 */
interface VoiceStepInfo {
  time: string
  text: string
}

export interface FallbackData {
  timer: string
  currentStep: VoiceStepInfo | null
  prevSteps: VoiceStepInfo[]
  nextSteps: VoiceStepInfo[]
  stepProgress: number
  timelineProgress: number
  layout: 'horizontal' | 'vertical'
}

export function useDocumentPiP() {
  const pipWindow = ref<Window | null>(null)
  
  // Use a more robust check that works at runtime
  const isSupported = computed(() => {
    return !!((window as any).documentPictureInPicture) || 'documentPictureInPicture' in window
  })

  async function requestPiP(
    element: HTMLElement,
    options: { 
      width?: number; 
      height?: number;
      fallbackData?: FallbackData
    } = {}
  ) {
    const dPip = (window as any).documentPictureInPicture

    if (dPip) {
      try {
        if (pipWindow.value) pipWindow.value.close()

        const pip = await dPip.requestWindow({
          width: options.width || 400,
          height: options.height || 120,
          copyStyleSheets: true,
        })
        pipWindow.value = pip

        pip.document.body.style.margin = '0'
        pip.document.body.style.padding = '0'
        pip.document.body.style.overflow = 'hidden'
        pip.document.body.style.height = '100vh'
        pip.document.body.style.backgroundColor = getComputedStyle(document.body).backgroundColor

        // Style copying helpers
        const copyStyles = (destDoc: Document) => {
          Array.from(document.styleSheets).forEach((sheet) => {
            try {
              const rules = Array.from(sheet.cssRules).map(r => r.cssText).join('')
              const style = document.createElement('style')
              style.textContent = rules
              destDoc.head.appendChild(style)
            } catch (e) {
              const link = document.createElement('link')
              if (sheet.href) {
                link.rel = 'stylesheet'
                link.href = sheet.href
                destDoc.head.appendChild(link)
              }
            }
          })
        }
        copyStyles(pip.document)

        // Element restoration logic
        const originalParent = element.parentElement
        const originalSibling = element.nextElementSibling
        pip.document.body.appendChild(element)

        const closeHandler = () => {
          if (originalParent) {
            if (originalSibling) originalParent.insertBefore(element, originalSibling)
            else originalParent.appendChild(element)
          }
          pipWindow.value = null
        }
        pip.addEventListener('pagehide', closeHandler, { once: true })
        
        return pip
      } catch (err) {
        console.error('Document PiP failed, trying fallback...', err)
        return requestVideoPiP(options.fallbackData)
      }
    } else {
      return requestVideoPiP(options.fallbackData)
    }
  }

  async function requestVideoPiP(data?: FallbackData) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const video = document.createElement('video')
    video.muted = true
    // @ts-ignore
    video.srcObject = canvas.captureStream()

    let isDrawing = true
    const draw = () => {
      if (!isDrawing || !video.srcObject) return
      
      const isH = data?.layout === 'horizontal'
      canvas.width = isH ? 540 : 320
      canvas.height = isH ? 120 : 600

      ctx.fillStyle = '#0d1117'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      const ph = 8
      const py = canvas.height - ph
      const segW = canvas.width / 4
      
      // segments
      ctx.fillStyle = 'rgba(210, 153, 34, 0.4)'
      ctx.fillRect(0, py, segW, ph)
      ctx.fillStyle = 'rgba(63, 185, 80, 0.4)'
      ctx.fillRect(segW, py, segW, ph)
      ctx.fillStyle = 'rgba(248, 81, 73, 0.4)'
      ctx.fillRect(segW * 2, py, segW, ph)
      ctx.fillStyle = 'rgba(163, 113, 247, 0.4)'
      ctx.fillRect(segW * 3, py, segW, ph)
      
      // Step progress (gradient)
      const sp = (data?.stepProgress || 0) * canvas.width
      const grad = ctx.createLinearGradient(0, 0, canvas.width, 0)
      grad.addColorStop(0, '#d29922'); grad.addColorStop(0.25, '#d29922')
      grad.addColorStop(0.25, '#3fb950'); grad.addColorStop(0.5, '#3fb950')
      grad.addColorStop(0.5, '#f85149'); grad.addColorStop(0.75, '#f85149')
      grad.addColorStop(0.75, '#a371f7'); grad.addColorStop(1, '#a371f7')
      ctx.fillStyle = grad
      ctx.globalAlpha = 0.8
      ctx.fillRect(0, py, sp, ph)
      ctx.globalAlpha = 1.0

      // Timeline progress 
      const tp = (data?.timelineProgress || 0) * canvas.width
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
      ctx.fillRect(0, py, tp, ph)

      const px = 20
      if (!isH) {
         let y = 60
         ctx.font = '14px sans-serif'
         data?.prevSteps?.forEach(s => {
            ctx.globalAlpha = 0.6
            ctx.fillStyle = '#8b949e'
            ctx.fillText(`${s.time}  ${s.text}`.slice(0, 35), px + 10, y)
            y += 30
         })
         ctx.globalAlpha = 1.0
         
         y += 10
         if (data?.currentStep) {
            ctx.fillStyle = '#3fb950' 
            ctx.fillRect(px, y - 20, 4, 26)
            ctx.font = 'bold 20px monospace'
            ctx.fillStyle = '#d29922'
            ctx.fillText(data.currentStep.time, px + 15, y)
            ctx.font = 'bold 20px sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText(data.currentStep.text.slice(0, 20), px + 95, y)
         } else {
            ctx.font = 'bold 20px sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText('等待开始...', px, y)
         }
         y += 50

         ctx.font = '14px sans-serif'
         data?.nextSteps?.forEach(s => {
            ctx.globalAlpha = 0.8
            ctx.fillStyle = '#8b949e'
            ctx.fillText(`${s.time}  ${s.text}`.slice(0, 35), px + 10, y)
            y += 30
         })
         ctx.globalAlpha = 1.0

         const timerY = canvas.height - 40
         ctx.fillStyle = '#22c55e'
         ctx.font = 'bold 42px monospace'
         ctx.fillText(data?.timer || '00:00', px, timerY)
      } else {
         ctx.fillStyle = '#22c55e'
         ctx.font = 'bold 42px monospace'
         ctx.fillText(data?.timer || '00:00', 20, 70)
         
         const cx = 170
         const cy = 40
         if (data?.currentStep) {
            ctx.fillStyle = '#3fb950' 
            ctx.fillRect(cx, cy - 20, 4, 26)
            ctx.font = 'bold 20px monospace'
            ctx.fillStyle = '#d29922'
            ctx.fillText(data.currentStep.time, cx + 15, cy)
            ctx.font = 'bold 20px sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText(data.currentStep.text.slice(0, 25), cx + 90, cy)
         } else {
            ctx.font = 'bold 20px sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText('等待开始...', cx + 15, cy)
         }
         
         const rowY = 85
         ctx.font = '15px sans-serif'
         const pCount = data?.prevSteps?.length || 0
         if (pCount > 0) {
             ctx.globalAlpha = 0.6
             ctx.fillStyle = '#8b949e'
             ctx.fillText(`${data!.prevSteps[pCount-1].time} ${data!.prevSteps[pCount-1].text}`.slice(0, 20), cx + 15, rowY)
             ctx.globalAlpha = 1.0
         }
         if (data?.nextSteps?.length) {
             ctx.globalAlpha = 0.8
             ctx.fillStyle = '#8b949e'
             ctx.fillText(`${data!.nextSteps[0].time} ${data!.nextSteps[0].text}`.slice(0, 20), cx + 190, rowY)
             ctx.globalAlpha = 1.0
         }
      }

      requestAnimationFrame(draw)
    }
    
    // Draw initial frame so captureStream has content, otherwise metadata can't load
    draw()
    
    let closeBtn: HTMLButtonElement | null = null
    const cleanup = () => {
      isDrawing = false
      video.remove()
      if (closeBtn) closeBtn.remove()
    }

    try {
      // Must await play for metadata to load and preserve user activation gesture
      await video.play()

      // Some browsers (Edge via HTTP) support this API
      // Firefox does NOT support requestPictureInPicture on HTMLVideoElement
      if (typeof (video as any).requestPictureInPicture === 'function') {
        video.style.position = 'fixed'
        video.style.top = '-1000px'
        document.body.appendChild(video)
        
        await (video as any).requestPictureInPicture()
        video.addEventListener('leavepictureinpicture', cleanup, { once: true })
      } else {
        // Firefox fallback: display the video on screen with controls
        // Firefox users can then click the browser's built-in PiP overlay button on the video
        document.body.appendChild(video)
        video.controls = true // Important: Firefox shows PiP button when controls are true or when hovered
        video.style.position = 'fixed'
        video.style.bottom = '100px'
        video.style.right = '20px'
        video.style.width = '320px'
        video.style.zIndex = '9999'
        video.style.borderRadius = '8px'
        video.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.6)'
        
        // Add a close button for Firefox users
        closeBtn = document.createElement('button')
        closeBtn.innerHTML = '&times;'
        closeBtn.style.position = 'fixed'
        closeBtn.style.bottom = '240px'
        closeBtn.style.right = '25px'
        closeBtn.style.zIndex = '10000'
        closeBtn.style.background = 'rgba(0,0,0,0.5)'
        closeBtn.style.color = 'white'
        closeBtn.style.border = 'none'
        closeBtn.style.borderRadius = '50%'
        closeBtn.style.width = '24px'
        closeBtn.style.height = '24px'
        closeBtn.style.cursor = 'pointer'
        closeBtn.onclick = cleanup
        document.body.appendChild(closeBtn)

        video.addEventListener('leavepictureinpicture', cleanup, { once: true })
      }
    } catch (err) {
      cleanup()
      console.error('Video PiP failed', err)
      alert('您的浏览器不支持画中画功能。')
    }
  }

  return {
    isSupported,
    pipWindow,
    requestPiP,
  }
}
