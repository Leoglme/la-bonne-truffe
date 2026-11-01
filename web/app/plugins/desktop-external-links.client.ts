import type { UseDesktopRuntimeReturn } from '~/types/Composables'
import { ExternalLinks } from '~/utils/externalLinks'

const MAIN_MOUSE_BUTTON: number = 0
const MIDDLE_MOUSE_BUTTON: number = 1

/** Desktop app only: a link to another site opens in the default browser, never in the window of the app. */
export default defineNuxtPlugin((): void => {
  const { isDesktopApp }: UseDesktopRuntimeReturn = useDesktopRuntime()
  if (!isDesktopApp.value) {
    return
  }
  const toast: ReturnType<typeof useToast> = useToast()

  /**
   * Open an address in the default browser, through the opener plugin of Tauri.
   *
   * @param url - The address on another site.
   */
  async function openInDefaultBrowser(url: string): Promise<void> {
    try {
      const { openUrl }: typeof import('@tauri-apps/plugin-opener') = await import('@tauri-apps/plugin-opener')
      await openUrl(url)
    } catch {
      toast.add({
        title: 'Le lien ne s’est pas ouvert dans le navigateur',
        color: 'error',
        icon: 'i-lucide-circle-alert',
      })
    }
  }

  /**
   * Send a click on a link to another site to the default browser instead of the window of the app.
   *
   * @param event - The click, or the middle click, on the page.
   */
  function openClickedExternalLink(event: MouseEvent): void {
    const isLinkOpeningButton: boolean = event.button === MAIN_MOUSE_BUTTON || event.button === MIDDLE_MOUSE_BUTTON
    if (event.defaultPrevented || !isLinkOpeningButton) {
      return
    }
    const clickedLink: Element | null = event.target instanceof Element ? event.target.closest('a[href]') : null
    if (!(clickedLink instanceof HTMLAnchorElement)) {
      return
    }
    const externalUrl: string | null = ExternalLinks.findUrlToOpenInBrowser(clickedLink.href, window.location.origin)
    if (externalUrl === null) {
      return
    }
    event.preventDefault()
    openInDefaultBrowser(externalUrl)
  }

  document.addEventListener('click', openClickedExternalLink)
  document.addEventListener('auxclick', openClickedExternalLink)
})
