import type { ApiErrorBody, ApiValidationError } from '~/types/ApiClient'
import { TokenRejectedError } from '~/services/authService'

const REQUEST_BODY_LOCATION: string = 'body'
const TOKEN_REJECTED_STATUS: number = 401

/** HTTP client every service goes through: bearer token, JSON encoding, and error unwrapping. */
export class ApiClient {
  /**
   * Send a GET request.
   *
   * @param endpoint - Path starting with `/api/`.
   * @returns The parsed response body.
   */
  static get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
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
   * @returns The API `detail` field, the first validation error of a refused payload, or the status text.
   */
  private static async readErrorMessage(response: Response): Promise<string> {
    const fallback: string = `Erreur de l'API : ${response.status} ${response.statusText}`
    const body: string = await response.text().catch((): string => '')
    try {
      const parsed: ApiErrorBody = JSON.parse(body)
      if (typeof parsed.detail === 'string') {
        return parsed.detail
      }
      return this.readFirstValidationError(parsed.detail) ?? fallback
    } catch {
      return fallback
    }
  }

  /**
   * Word the first validation error of a refused payload, as FastAPI lists them.
   *
   * @param detail - The `detail` field of the response.
   * @returns « department_codes : List should have at least 1 item… », or null when the field is not that list.
   */
  private static readFirstValidationError(detail: unknown): string | null {
    const firstError: unknown = Array.isArray(detail) ? detail[0] : null
    if (typeof firstError !== 'object' || firstError === null) {
      return null
    }
    const validationError: ApiValidationError = firstError
    if (typeof validationError.msg !== 'string') {
      return null
    }
    const fieldPath: string = Array.isArray(validationError.loc)
      ? validationError.loc
          .filter((part: unknown): part is string => typeof part === 'string')
          .filter((part: string): boolean => part !== REQUEST_BODY_LOCATION)
          .join('.')
      : ''
    return fieldPath ? `${fieldPath} : ${validationError.msg}` : validationError.msg
  }
}
