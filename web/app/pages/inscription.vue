<template>
  <AuthScreen title="Créer ton compte">
    <template #subtitle>
      <span class="md:hidden">Deux minutes, et la truffe se met au travail.</span>
      <span class="hidden md:inline">Deux minutes, et la truffe se met à flairer pour toi.</span>
    </template>
    <template #visual>
      <AuthPhotoVisual
        photo-path="/images/auth/cocker-gold-dos.jpg"
        photo-description="Cocker gold ravi, couché sur le dos dans l’herbe"
        height-class="h-[160px] md:h-[290px]"
        photo-position-class="object-[center_30%] lg:object-[center_35%]"
        overlay-overlap-class="-mt-[22px] md:-mt-[26px]"
      >
        <template #overlay>
          <ul class="m-0 hidden list-none gap-3 p-0 md:flex lg:flex-col lg:items-start">
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
            class="m-0 inline-flex h-11 items-center gap-2 rounded-full bg-card ps-[5px] pe-4 text-[13px] font-extrabold whitespace-nowrap shadow-straddling-photo md:hidden"
          >
            <span class="flex size-[34px] items-center justify-center rounded-full bg-coral-pastel text-coral">
              <UiCustomIcon name="bell" :size-in-pixels="18" :stroke-width="2.2" />
            </span>
            Prévenu le premier, même avant la naissance
          </p>
        </template>
      </AuthPhotoVisual>
    </template>

    <form class="flex flex-col gap-3 md:gap-5 lg:gap-[18px]" @submit.prevent="submit">
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
        <UButton type="submit" block size="xl" :loading="isSubmitting" class="md:min-h-[58px] lg:min-h-14">
          Créer mon compte
        </UButton>
        <UButton
          to="/connexion"
          color="neutral"
          variant="outline"
          block
          size="xl"
          class="bg-transparent md:min-h-[58px] lg:min-h-14"
        >
          J’ai déjà un compte
        </UButton>
      </div>
    </form>
  </AuthScreen>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref } from 'vue'
import { PASSWORD_RULE_HINT, PASSWORD_RULE_MESSAGE, PASSWORD_RULE_SHORT_HINT } from '~/constants/passwordRules'
import { SIGNUP_HIGHLIGHTS } from '~/constants/signupHighlights'
import { RefusedRequestError } from '~/services/authService'
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

/**
 * Create the account, sign it in, then open the criteria; the password rule is checked before the API.
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
    await userStore.signup({
      name: name.value.trim(),
      email: userStore.emailTypedWhileSignedOut.trim(),
      password: password.value,
    })
    await navigateTo('/criteres')
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Création du compte impossible'
    hasRefusedEmail.value = error instanceof RefusedRequestError && error.status === EMAIL_ALREADY_USED_STATUS
  } finally {
    isSubmitting.value = false
  }
}
</script>
