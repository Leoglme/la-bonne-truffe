import type { LoginCredentials, TokenResponse, User } from '~/types/api'

/** Answers by which the API turns a token down: invalid or expired (401), account deactivated (400). */
const TOKEN_REJECTION_STATUSES: number[] = [400, 401, 403]

/**
 * The API answered and refused the token, as opposed to an API out of reach (no network yet, a restart).
 */
export class TokenRejectedError extends Error {}

/** HTTP client for the /auth API resource, called before any token is stored. */
export class AuthService {
  /**
   * Exchange the email and password for a bearer token.
   *
   * @param credentials - Email and password typed on the login screen.
   * @returns The token.
   * @throws Error with the API message when the credentials are refused.
   */
  static async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response: Response = await fetch(`${this.apiBase()}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    })
    if (!response.ok) {
      const error: { detail?: unknown } = await response.json().catch((): { detail?: unknown } => ({}))
      throw new Error(typeof error.detail === 'string' ? error.detail : 'Connexion impossible')
    }
    return response.json()
  }

  /**
   * Read the user a token belongs to.
   *
   * @param token - Bearer token.
   * @returns The signed-in user.
   * @throws TokenRejectedError when the API refuses the token, Error when it cannot be reached.
   */
  static async getCurrentUser(token: string): Promise<User> {
    const response: Response = await fetch(`${this.apiBase()}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (TOKEN_REJECTION_STATUSES.includes(response.status)) {
      throw new TokenRejectedError('Jeton refusé')
    }
    if (!response.ok) {
      throw new Error("L'API ne répond pas")
    }
    return response.json()
  }

  /**
   * Resolve the API base URL from the runtime config.
   *
   * @returns The base URL, without trailing slash.
   */
  private static apiBase(): string {
    return useRuntimeConfig().public.apiBase
  }
}
