<template>
  <AuthScreen
    v-if="sentLink === null"
    title="Mot de passe oublié ?"
    subtitle="Pas de panique. Donne ton e-mail : la truffe t’envoie un lien pour en choisir un nouveau."
  >
    <template #visual>
      <AuthIllustrationVisual coat="gold" badge-icon-name="i-lucide-key-round" height-class="h-[200px] md:h-[420px]" />
    </template>

    <form class="flex flex-col gap-3 md:gap-5 lg:gap-[18px]" @submit.prevent="sendLink">
      <UiErrorAlert v-if="errorMessage" :message="errorMessage" />
      <UFormField label="E-mail" name="email">
        <UInput
          v-model="userStore.emailTypedWhileSignedOut"
          type="email"
          autocomplete="email"
          autocapitalize="off"
          spellcheck="false"
          required
          size="xl"
          class="w-full"
        />
      </UFormField>
      <div class="mt-1.5 flex flex-col gap-2.5 md:mt-2 md:gap-3">
        <UButton type="submit" block size="xl" :loading="isSending" class="md:min-h-[58px] lg:min-h-14">
          Envoyer le lien
        </UButton>
        <UButton
          to="/connexion"
          color="neutral"
          variant="outline"
          block
          size="xl"
          class="bg-transparent md:min-h-[58px] lg:min-h-14"
        >
          Retour à la connexion
        </UButton>
      </div>
    </form>
  </AuthScreen>

  <AuthScreen v-else title="Regarde tes e-mails">
    <template #subtitle>
      Si un compte existe pour <strong class="font-extrabold text-ink">{{ sentLink.email }}</strong
      >, un lien t’y attend pour choisir un nouveau mot de passe. Il reste valable
      {{ sentLink.expiresInMinutes }} minutes.
    </template>
    <template #visual>
      <AuthPhotoVisual
        photo-path="/images/auth/cocker-gold-balle.jpg"
        photo-description="Cocker gold couché dans l’herbe, qui attend"
        height-class="h-[200px] md:h-[400px]"
        photo-position-class="object-[center_36%]"
        badge-icon-name="i-lucide-mail-check"
      />
    </template>

    <div class="flex flex-col gap-4 md:gap-5">
      <UiErrorAlert v-if="errorMessage" :message="errorMessage" />
      <p
        class="m-0 flex items-center gap-3.5 rounded-[20px] bg-card px-[18px] py-3.5 text-[15px] text-ink-secondary shadow-card md:text-base"
      >
        <span aria-hidden="true" class="flex size-11 shrink-0 items-center justify-center rounded-full bg-chip">
          <UIcon name="i-lucide-inbox" class="size-5" />
        </span>
        Rien reçu d’ici deux minutes ? Jette un œil aux indésirables.
      </p>
      <div class="mt-1 flex flex-col gap-2.5 md:mt-2 md:gap-3">
        <UButton to="/connexion" block size="xl" class="md:min-h-[58px] lg:min-h-14">Retour à la connexion</UButton>
        <UButton
          color="neutral"
          variant="outline"
          block
          size="xl"
          :disabled="resendCountdownSeconds > 0"
          :loading="isSending"
          class="bg-transparent disabled:bg-transparent disabled:text-ink-muted disabled:opacity-100 disabled:ring-avatar md:min-h-[58px] lg:min-h-14"
          @click="sendLink"
        >
          {{ resendLabel }}
        </UButton>
      </div>
      <p class="m-0 text-center text-[15px] text-ink-secondary md:text-base">
        Mauvaise adresse ?
        <button
          type="button"
          class="inline-flex min-h-11 items-center border-0 bg-transparent p-0 font-extrabold text-coral-text"
          @click="editEmail"
        >
          Modifier l’e-mail
        </button>
      </p>
    </div>
  </AuthScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { PasswordResetRequested } from '~/types/api'
import type { SentPasswordResetLink } from '~/types/SentPasswordResetLink'
import { computed, onBeforeUnmount, ref } from 'vue'
import { AuthService } from '~/services/authService'

const SECONDS_PER_MINUTE: number = 60
const COUNTDOWN_TICK_MS: number = 1000

definePageMeta({ layout: 'signed-out', isPublicScreen: true })
useHead({ title: 'Mot de passe oublié · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

const sentLink: Ref<SentPasswordResetLink | null> = ref(null)
const isSending: Ref<boolean> = ref(false)
const errorMessage: Ref<string | null> = ref(null)
const resendCountdownSeconds: Ref<number> = ref(0)
let resendCountdownTimer: ReturnType<typeof setInterval> | null = null

const resendLabel: ComputedRef<string> = computed((): string => {
  if (resendCountdownSeconds.value <= 0) {
    return 'Renvoyer le lien'
  }
  const minutes: number = Math.floor(resendCountdownSeconds.value / SECONDS_PER_MINUTE)
  const seconds: string = String(resendCountdownSeconds.value % SECONDS_PER_MINUTE).padStart(2, '0')
  return `Renvoyer le lien dans ${minutes}:${seconds}`
})

/**
 * Ask for a reset link, then show « Regarde tes e-mails » with the countdown before another one.
 */
async function sendLink(): Promise<void> {
  isSending.value = true
  errorMessage.value = null
  const email: string = userStore.emailTypedWhileSignedOut.trim()
  try {
    const requested: PasswordResetRequested = await AuthService.requestPasswordReset({ email })
    sentLink.value = { email, expiresInMinutes: requested.expires_in_minutes }
    startResendCountdown(requested.resend_delay_seconds)
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Envoi du lien impossible'
  } finally {
    isSending.value = false
  }
}

/**
 * Count down to the moment another link may be asked.
 *
 * @param seconds - Delay the API asks for.
 */
function startResendCountdown(seconds: number): void {
  stopResendCountdown()
  resendCountdownSeconds.value = seconds
  resendCountdownTimer = setInterval((): void => {
    resendCountdownSeconds.value -= 1
    if (resendCountdownSeconds.value <= 0) {
      stopResendCountdown()
    }
  }, COUNTDOWN_TICK_MS)
}

/**
 * Stop the countdown, if one is running.
 */
function stopResendCountdown(): void {
  if (resendCountdownTimer !== null) {
    clearInterval(resendCountdownTimer)
    resendCountdownTimer = null
  }
}

/**
 * Go back to the form to fix the address.
 */
function editEmail(): void {
  stopResendCountdown()
  resendCountdownSeconds.value = 0
  errorMessage.value = null
  sentLink.value = null
}

onBeforeUnmount((): void => {
  stopResendCountdown()
})
</script>
