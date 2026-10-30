import type { ApiErrorBody, ApiQueryParams } from '~/types/ApiClient'
import { TokenRejectedError } from '~/services/authService'

const TOKEN_REJECTED_STATUS: number = 401

/** HTTP client every service goes through: bearer token, JSON encoding, and error unwrapping. */
export class ApiClient {
  /**
   * Send a GET request.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param options - Optional query parameters; null and undefined values are dropped.
   * @returns The parsed response body.
   */
  static get<T>(endpoint: string, options?: { params?: ApiQueryParams }): Promise<T> {
    return this.request<T>(this.withQuery(endpoint, options?.params), { method: 'GET' })
  }

  /**
   * Send a POST request.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param data - Request body, JSON-encoded.
   * @returns The parsed response body.
   */
  static post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) })
  }

  /**
   * Send a PUT request.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param data - Request body, JSON-encoded.
   * @returns The parsed response body.
   */
  static put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) })
  }

  /**
   * Send a PATCH request.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param data - Request body, JSON-encoded.
   * @returns The parsed response body.
   */
  static patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) })
  }

  /**
   * Send a DELETE request, with a JSON body when the route expects one.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param data - Optional request body, JSON-encoded.
   * @returns The parsed response body, or undefined when the route answers empty.
   */
  static delete<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    })
  }

  /**
   * Append a query string, skipping the parameters that carry no value.
   *
   * @param endpoint - Path to decorate.
   * @param params - Query parameters.
   * @returns The path, with its query string when at least one parameter survived.
   */
  private static withQuery(endpoint: string, params?: ApiQueryParams): string {
    if (!params) {
      return endpoint
    }
    const search: URLSearchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]: [string, unknown]): void => {
      if (value !== null && value !== undefined) {
        search.append(key, String(value))
      }
    })
    const queryString: string = search.toString()
    return queryString ? `${endpoint}?${queryString}` : endpoint
  }

  /**
   * Perform the authenticated request and unwrap the response.
   *
   * @param endpoint - Path starting with `/api/`.
   * @param options - Fetch options; the auth and content-type headers are added here.
   * @returns The parsed body, or undefined when the response has none.
   * @throws TokenRejectedError when the API refuses the session, Error carrying the API `detail` message for any
   *   other refusal, or when the API cannot be reached.
   */
  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const userStore: ReturnType<typeof useUserStore> = useUserStore()
    const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()

    const response: Response = await fetch(`${config.public.apiBase}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(userStore.token && { Authorization: `Bearer ${userStore.token}` }),
        ...options.headers,
      },
    }).catch((): never => {
      throw new Error('L’API ne répond pas')
    })

    if (response.status === TOKEN_REJECTED_STATUS) {
      throw new TokenRejectedError(await this.readErrorMessage(response))
    }
    if (!response.ok) {
      throw new Error(await this.readErrorMessage(response))
    }

    // Several routes answer 204: response.json() would throw on their empty body.
    const text: string = await response.text()
    if (!text.trim()) {
      return undefined as T
    }
    return JSON.parse(text) as T
  }

  /**
   * Extract the most precise message a failed response offers.
   *
   * @param response - The failed response.
   * @returns The API `detail` field, falling back to the status text.
   */
  private static async readErrorMessage(response: Response): Promise<string> {
    const fallback: string = `Erreur de l'API : ${response.status} ${response.statusText}`
    const body: string = await response.text().catch((): string => '')
    try {
      const parsed: ApiErrorBody = JSON.parse(body)
      return typeof parsed.detail === 'string' ? parsed.detail : fallback
    } catch {
      return fallback
    }
  }
}
