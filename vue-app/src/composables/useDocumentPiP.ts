import { ref, computed } from 'vue'

/**
 * Composable for Document Picture-in-Picture API with Video Fallback
 * @see https://developer.chrome.com/docs/web-platform/document-picture-in-picture/
 */
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
      fallbackData?: {
        timer: string;
        status: string;
        stepText: string;
      }
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

  async function requestVideoPiP(data?: { timer: string, status: string, stepText: string }) {
    const canvas = document.createElement('canvas')
    canvas.width = 400
    canvas.height = 160
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const video = document.createElement('video')
    video.muted = true
    // @ts-ignore
    video.srcObject = canvas.captureStream()
    video.play()

    document.body.appendChild(video)
    video.style.position = 'fixed'
    video.style.top = '-1000px'

    const draw = () => {
      if (!video.srcObject) return
      
      ctx.fillStyle = '#0d1117'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      // Timer
      ctx.fillStyle = '#3fb950'
      ctx.font = 'bold 50px monospace'
      ctx.fillText(data?.timer || '00:00', 20, 60)

      // Step Text
      ctx.fillStyle = '#ffffff'
      ctx.font = '22px sans-serif'
      const text = data?.stepText || '等待开始'
      ctx.fillText(text.slice(0, 30), 20, 100)

      // Status
      ctx.fillStyle = '#8b949e'
      ctx.font = '18px sans-serif'
      ctx.fillText(data?.status || '', 20, 135)

      if (video.readyState >= 2) {
        requestAnimationFrame(draw)
      }
    }
    draw()

    try {
      await video.requestPictureInPicture()
      video.addEventListener('leavepictureinpicture', () => {
        video.remove()
      }, { once: true })
    } catch (err) {
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
