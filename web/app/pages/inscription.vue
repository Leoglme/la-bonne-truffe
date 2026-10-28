<template>
  <AuthScreen v-if="recordedSignupRequestEmail === null" title="Créer ton compte">
    <template #subtitle>
      <span class="md:hidden">Deux minutes, et la truffe se met au travail.</span>
      <span class="hidden md:inline">Deux minutes, et la truffe se met à flairer pour toi.</span>
    </template>
    <template #visual>
      <AuthPhotoVisual
        photo-path="/images/auth/cocker-gold-dos.jpg"
        photo-description="Cocker gold ravi, couché sur le dos dans l’herbe"
        height-class="h-[160px] md:h-[290px]"
        photo-position-class="object-[center_30%]"
        overlay-overlap-class="-mt-[22px] md:-mt-[26px]"
        left-photo-path="/images/auth/cocker-gold-balle.jpg"
        right-photo-path="/images/auth/cocker-gold-herbe.jpg"
      >
        <template #overlay>
          <ul class="m-0 hidden list-none gap-3 p-0 md:flex">
            <li
              v-for="highlight in SIGNUP_HIGHLIGHTS"
              :key="highlight.label"
              class="inline-flex h-[52px] items-center gap-2.5 rounded-full bg-card ps-1.5 pe-[18px] text-[15px] font-extrabold whitespace-nowrap shadow-straddling-photo"
            >
              <span class="flex size-10 items-center justify-center rounded-full" :class="highlight.circleClass">
                <CockerIllustration
                  v-if="highlight.coat"
                  :coat="highlight.coat"
                  :size-in-pixels="32"
                  aria-hidden="true"
                />
                <UiCustomIcon
                  v-else-if="highlight.iconName"
                  :name="highlight.iconName"
                  :size-in-pixels="20"
                  :stroke-width="2.2"
                />
              </span>
              {{ highlight.label }}
            </li>
          </ul>
          <p
            class="m-0 inline-flex h-11 max-w-full items-center gap-2 rounded-full bg-card ps-[5px] pe-4 text-[13px] font-extrabold whitespace-nowrap shadow-straddling-photo md:hidden"
          >
            <span class="flex size-[34px] shrink-0 items-center justify-center rounded-full bg-coral-pastel text-coral">
              <UiCustomIcon name="bell" :size-in-pixels="18" :stroke-width="2.2" />
            </span>
            <span class="min-w-0 truncate">Prévenu même avant la naissance</span>
          </p>
        </template>
      </AuthPhotoVisual>
    </template>

    <form class="flex flex-col gap-3 md:gap-5 xl:gap-[18px]" @submit.prevent="submit">
      <UiErrorAlert v-if="errorMessage" :message="errorMessage" />
      <UFormField label="Prénom" name="name" hint="Pour te dire bonjour">
        <UInput v-model="name" autocomplete="given-name" required size="xl" class="w-full" />
      </UFormField>
      <UFormField label="E-mail" name="email" :error="hasRefusedEmail">
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
      <UFormField label="Mot de passe" name="password" :error="hasRefusedPassword">
        <template #hint>
          <span class="md:hidden">{{ PASSWORD_RULE_SHORT_HINT }}</span>
          <span class="hidden md:inline">{{ PASSWORD_RULE_HINT }}</span>
        </template>
        <UiPasswordInput v-model="password" autocomplete="new-password" required />
        <UiPasswordStrengthMeter :password="password" class="mt-2" />
      </UFormField>
      <div class="mt-1.5 flex flex-col gap-2.5 md:mt-2 md:gap-3">
        <UButton type="submit" block size="xl" :loading="isSubmitting" class="md:min-h-[58px] xl:min-h-14">
          Créer mon compte
        </UButton>
        <UButton
          to="/connexion"
          color="neutral"
          variant="outline"
          block
          size="xl"
          class="bg-transparent md:min-h-[58px] xl:min-h-14"
        >
          J’ai déjà un compte
        </UButton>
      </div>
    </form>
  </AuthScreen>

  <AuthScreen v-else title="C’est noté !">
    <template #subtitle>
      La Bonne Truffe n’ouvre pas encore les inscriptions. On garde
      <strong class="font-extrabold text-ink">{{ recordedSignupRequestEmail }}</strong> pour te prévenir dès qu’elles
      ouvrent.
    </template>
    <template #visual>
      <AuthIllustrationVisual coat="gold" badge-icon-name="i-lucide-bell-ring" height-class="h-[200px] md:h-[420px]" />
    </template>

    <UButton to="/connexion" block size="xl" class="md:min-h-[58px] xl:min-h-14">Retour à la connexion</UButton>
  </AuthScreen>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { SignupAvailability, SignupRequestRecorded } from '~/types/api'
import { ref } from 'vue'
import { PASSWORD_RULE_HINT, PASSWORD_RULE_MESSAGE, PASSWORD_RULE_SHORT_HINT } from '~/constants/passwordRules'
import { SIGNUP_HIGHLIGHTS } from '~/constants/signupHighlights'
import { AuthService, RefusedRequestError } from '~/services/authService'
import { PasswordRules } from '~/utils/passwordRules'

const EMAIL_ALREADY_USED_STATUS: number = 409

definePageMeta({ layout: 'signed-out', isGuestOnlyScreen: true })
useHead({ title: 'Créer un compte · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

const name: Ref<string> = ref('')
const password: Ref<string> = ref('')
const isSubmitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string | null> = ref(null)
const hasRefusedEmail: Ref<boolean> = ref(false)
const hasRefusedPassword: Ref<boolean> = ref(false)
const recordedSignupRequestEmail: Ref<string | null> = ref(null)

/**
 * Create the account, or keep the signup request while signups are closed; the password rule is checked first.
 */
async function submit(): Promise<void> {
  errorMessage.value = null
  hasRefusedEmail.value = false
  hasRefusedPassword.value = !PasswordRules.isStrongEnough(password.value)
  if (hasRefusedPassword.value) {
    errorMessage.value = PASSWORD_RULE_MESSAGE
    return
  }
  isSubmitting.value = true
  try {
    const availability: SignupAvailability = await AuthService.getSignupAvailability()
    if (availability.is_open) {
      await createAccount()
    } else {
      await keepSignupRequest()
    }
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Création du compte impossible'
    hasRefusedEmail.value = error instanceof RefusedRequestError && error.status === EMAIL_ALREADY_USED_STATUS
  } finally {
    isSubmitting.value = false
  }
}

/**
 * Create the account, sign it in, then open the criteria.
 */
async function createAccount(): Promise<void> {
  await userStore.signup({
    name: name.value.trim(),
    email: userStore.emailTypedWhileSignedOut.trim(),
    password: password.value,
  })
  await navigateTo('/criteres')
}

/**
 * Keep the name and address while signups are closed, then show « C’est noté ».
 */
async function keepSignupRequest(): Promise<void> {
  const recordedSignupRequest: SignupRequestRecorded = await AuthService.requestSignup({
    name: name.value.trim(),
    email: userStore.emailTypedWhileSignedOut.trim(),
  })
  recordedSignupRequestEmail.value = recordedSignupRequest.email
}
</script>
