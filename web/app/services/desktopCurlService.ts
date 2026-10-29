import type { RelayedPageResponse, RelayPageRequest } from '~/types/api'

/** The curl of Windows, reached through the command of the desktop app. */
export class DesktopCurlService {
  /**
   * Read a Centrale Canine page with the curl of Windows, without opening any window.
   *
   * @param pageRequest - Address of the page and headers to send.
   * @returns The page as curl received it.
   */
  static async readCentraleCaninePage(pageRequest: RelayPageRequest): Promise<RelayedPageResponse> {
    const { invoke }: typeof import('@tauri-apps/api/core') = await import('@tauri-apps/api/core')
    return invoke<RelayedPageResponse>('read_centrale_canine_page', {
      url: pageRequest.url,
      headers: Object.entries(pageRequest.headers),
    })
  }
}
