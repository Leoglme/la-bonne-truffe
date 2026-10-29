import type { RelayedPageResponse, RelayPageRequest } from '~/types/api'

/** The two ways the desktop app reads a Centrale Canine page: the curl of Windows, or its own browser. */
export class DesktopPageReaderService {
  /**
   * Read a Centrale Canine page with the curl of Windows, without opening any window.
   *
   * @param pageRequest - Address of the page and headers to send.
   * @returns The page as curl received it.
   */
  static async readCentraleCaninePageWithCurl(pageRequest: RelayPageRequest): Promise<RelayedPageResponse> {
    const { invoke }: typeof import('@tauri-apps/api/core') = await import('@tauri-apps/api/core')
    return invoke<RelayedPageResponse>('read_centrale_canine_page_with_curl', {
      url: pageRequest.url,
      headers: Object.entries(pageRequest.headers),
    })
  }

  /**
   * Read a Centrale Canine page in a hidden window of the app's browser, where Cloudflare runs its check.
   *
   * @param pageRequest - Address of the page; the browser sends its own headers.
   * @returns The page as the browser read it.
   */
  static async readCentraleCaninePageInBrowser(pageRequest: RelayPageRequest): Promise<RelayedPageResponse> {
    const { invoke }: typeof import('@tauri-apps/api/core') = await import('@tauri-apps/api/core')
    return invoke<RelayedPageResponse>('read_centrale_canine_page_in_browser', { url: pageRequest.url })
  }
}
