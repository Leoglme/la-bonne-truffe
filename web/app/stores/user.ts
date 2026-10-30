import type { ComputedRef, Ref } from 'vue'
import type {
  CurrentSession,
  LoginCredentials,
  PasswordResetConfirm,
  SignupPayload,
  TokenResponse,
  User,
} from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { AuthService, TokenRejectedError } from '~/services/authService'

const TOKEN_STORAGE_KEY: string = 'lbt-token'
const USER_STORAGE_KEY: string = 'lbt-user'
const SESSION_VALIDATION_INTERVAL_MS: number = 60_000

/** Pinia store of the session: bearer token and signed-in user, kept in localStorage; the API renews the token. */
export const useUserStore = defineStore('user', () => {
  const user: Ref<User | null> = ref(null)
  const token: Ref<string | null> = ref(null)
  const emailTypedWhileSignedOut: Ref<string> = ref('')
  let lastValidatedAt: number = 0

  const isAuthenticated: ComputedRef<boolean> = computed((): boolean => user.value !== null && token.value !== null)
  const firstName: ComputedRef<string> = computed((): string => user.value?.name ?? '')

  /**
   * Restore the session saved on this device. Client only.
   */
  function restoreSession(): void {
    if (!import.meta.client) {
      return
    }
    token.value = localStorage.getItem(TOKEN_STORAGE_KEY)
    const savedUser: string | null = localStorage.getItem(USER_STORAGE_KEY)
    user.value = savedUser ? (JSON.parse(savedUser) as User) : null
  }

  /**
   * Sign in and save the session on this device.
   *
   * @param credentials - Email and password.
   * @throws RefusedRequestError with the API message when the credentials are refused.
   */
  async function login(credentials: LoginCredentials): Promise<void> {
    await startSession(await AuthService.login(credentials))
  }

  /**
   * Create the account, then sign it in on this device.
   *
   * @param account - Name, email and password typed on the signup screen.
   * @throws RefusedRequestError with the API message when the account is refused.
   */
  async function signup(account: SignupPayload): Promise<void> {
    await startSession(await AuthService.signup(account))
  }

  /**
   * Set the password chosen from a reset link, then sign the account in on this device.
   *
   * @param confirmation - Token read from the link, and the new password.
   * @throws RefusedRequestError with the API message when the link is expired or already used.
   */
  async function resetPassword(confirmation: PasswordResetConfirm): Promise<void> {
    await startSession(await AuthService.resetPassword(confirmation))
  }

  /**
   * Save the session a token opens: read its user, keep both on this device.
   *
   * @param tokenResponse - Token returned by the login, the signup or the password reset.
   */
  async function startSession(tokenResponse: TokenResponse): Promise<void> {
    const session: CurrentSession = await AuthService.readSession(tokenResponse.access_token)
    keepSession(session.renewed_token ?? tokenResponse.access_token, session.user)
  }

  /**
   * Keep the session on this device: the token to send from now on, and the user it belongs to.
   *
   * @param sessionToken - Bearer token, the one the API just renewed when the previous was past half its life.
   * @param signedInUser - The user the token belongs to.
   */
  function keepSession(sessionToken: string, signedInUser: User): void {
    token.value = sessionToken
    user.value = signedInUser
    localStorage.setItem(TOKEN_STORAGE_KEY, sessionToken)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(signedInUser))
    lastValidatedAt = Date.now()
  }

  /**
   * Check the saved token against the API, which renews it once it is past half its life.
   *
   * @returns False only when the API refused the token; an unreachable API keeps the saved session.
   */
  async function validateSession(): Promise<boolean> {
    if (!token.value) {
      return false
    }
    if (user.value !== null && Date.now() - lastValidatedAt < SESSION_VALIDATION_INTERVAL_MS) {
      return true
    }
    try {
      const session: CurrentSession = await AuthService.readSession(token.value)
      keepSession(session.renewed_token ?? token.value, session.user)
      return true
    } catch (error: unknown) {
      if (error instanceof TokenRejectedError) {
        logout()
        return false
      }
      return user.value !== null
    }
  }

  /**
   * Forget the session on this device.
   */
  function logout(): void {
    user.value = null
    token.value = null
    lastValidatedAt = 0
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
  }

  return {
    user,
    token,
    emailTypedWhileSignedOut,
    isAuthenticated,
    firstName,
    restoreSession,
    login,
    signup,
    resetPassword,
    validateSession,
    logout,
  }
})
