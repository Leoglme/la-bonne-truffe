import type { ApiErrorBody } from '~/types/ApiClient'
import type {
  CurrentSession,
  LoginCredentials,
  PasswordResetConfirm,
  PasswordResetRequest,
  PasswordResetRequested,
  PasswordResetTarget,
  PasswordResetToken,
  SignupAvailability,
  SignupPayload,
  SignupRequestPayload,
  SignupRequestRecorded,
  TokenResponse,
} from '~/types/api'

const TOKEN_REJECTION_STATUSES: number[] = [400, 401, 403]

/**
 * The API answered and refused the token, as opposed to an API out of reach (no network yet, a restart).
 */
export class TokenRejectedError extends Error {}

/**
 * The API answered and refused a signed-out request (wrong password, address already used, expired link),
 * as opposed to an API out of reach. Its status tells the screen which field to point at.
 */
export class RefusedRequestError extends Error {
  /**
   * @param message - Message to show, the API one when it gave one a person can read.
   * @param status - HTTP status of the refusal.
   */
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

/** HTTP client for the /auth API resource: what a signed-out visitor sends, and the check of a stored token. */
export class AuthService {
  /**
   * Exchange the email and password for a bearer token.
   *
   * @param credentials - Email and password typed on the login screen.
   * @returns The token.
   * @throws RefusedRequestError when the credentials are refused, Error when the API cannot be reached.
   */
  static login(credentials: LoginCredentials): Promise<TokenResponse> {
    return this.postAsVisitor<TokenResponse>('/login', credentials, 'Connexion impossible')
  }

  /**
   * Create an account and receive its bearer token.
   *
   * @param account - Name, email and password typed on the signup screen.
   * @returns The token of the new account.
   * @throws RefusedRequestError when the account is refused (address already used, signups closed).
   */
  static signup(account: SignupPayload): Promise<TokenResponse> {
    return this.postAsVisitor<TokenResponse>('/signup', account, 'Création du compte impossible')
  }

  /**
   * Tell whether the signup screen creates an account, or keeps a signup request while signups are closed.
   *
   * @returns Whether signups are open.
   * @throws Error when the API cannot be reached.
   */
  static async getSignupAvailability(): Promise<SignupAvailability> {
    const response: Response = await fetch(`${this.apiBase()}/api/v1/auth/signup-availability`).catch((): never => {
      throw new Error('L’API ne répond pas')
    })
    if (!response.ok) {
      throw new Error('L’API ne répond pas')
    }
    return response.json()
  }

  /**
   * Keep the name and address typed on the signup screen while signups are closed; the password is not sent.
   *
   * @param request - Name and address typed on the signup screen.
   * @returns The address told when signups open.
   * @throws RefusedRequestError when the address is refused, Error when the API cannot be reached.
   */
  static requestSignup(request: SignupRequestPayload): Promise<SignupRequestRecorded> {
    return this.postAsVisitor<SignupRequestRecorded>('/signup-requests', request, 'Envoi de la demande impossible')
  }

  /**
   * Ask for a reset link. The API answers the same whether or not the address has an account.
   *
   * @param request - Address typed on the « Mot de passe oublié » screen.
   * @returns The lifetime of the link and the delay before another one may be asked.
   */
  static requestPasswordReset(request: PasswordResetRequest): Promise<PasswordResetRequested> {
    return this.postAsVisitor<PasswordResetRequested>('/forgot-password', request, 'Envoi du lien impossible')
  }

  /**
   * Check the link of a reset email before asking for the new password.
   *
   * @param resetToken - Token read from the link.
   * @returns The address of the account the link resets.
   * @throws RefusedRequestError when the link is expired or already used.
   */
  static verifyPasswordResetLink(resetToken: PasswordResetToken): Promise<PasswordResetTarget> {
    return this.postAsVisitor<PasswordResetTarget>(
      '/reset-password/verify',
      resetToken,
      'Ce lien a expiré ou a déjà servi.',
    )
  }

  /**
   * Set the password chosen from a reset link and receive the bearer token of the account.
   *
   * @param confirmation - Token read from the link, and the new password.
   * @returns The token.
   * @throws RefusedRequestError when the link is expired or already used.
   */
  static resetPassword(confirmation: PasswordResetConfirm): Promise<TokenResponse> {
    return this.postAsVisitor<TokenResponse>('/reset-password', confirmation, 'Changement du mot de passe impossible')
  }

  /**
   * Read the session a token opens: its user and, once the token is past half its life, a fresh token to keep.
   *
   * @param token - Bearer token.
   * @returns The signed-in user, and the renewed token to send from now on, null while the token is young.
   * @throws TokenRejectedError when the API refuses the token, Error when it cannot be reached.
   */
  static async readSession(token: string): Promise<CurrentSession> {
    const response: Response = await fetch(`${this.apiBase()}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    }).catch((): never => {
      throw new Error('L’API ne répond pas')
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
   * POST to an /auth route without a token, and unwrap the message of a refusal.
   *
   * @param path - Route under `/api/v1/auth`.
   * @param body - Request body, JSON-encoded.
   * @param fallbackMessage - Message shown when the API gives none a person can read (a validation error).
   * @returns The parsed response body.
   * @throws RefusedRequestError when the API refuses, Error when it cannot be reached.
   */
  private static async postAsVisitor<T>(path: string, body: unknown, fallbackMessage: string): Promise<T> {
    const response: Response = await fetch(`${this.apiBase()}/api/v1/auth${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch((): never => {
      throw new Error('L’API ne répond pas')
    })
    if (!response.ok) {
      const error: ApiErrorBody = await response.json().catch((): ApiErrorBody => ({}))
      throw new RefusedRequestError(typeof error.detail === 'string' ? error.detail : fallbackMessage, response.status)
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
