<template>
  <AuthScreen title="Bon retour">
    <template #subtitle>
      <span class="md:hidden">La truffe est restée à l’affût pour toi.</span>
      <span class="hidden md:inline">La truffe est restée à l’affût. Connecte-toi pour voir ce qu’elle a flairé.</span>
    </template>
    <template #visual>
      <AuthPhotoVisual
        photo-path="/images/auth/chiot-gold-plaid.jpg"
        photo-description="Chiot cocker gold couché sur un plaid"
        height-class="h-[200px] md:h-[420px]"
        photo-position-class="object-[center_34%] md:object-[center_36%] lg:object-[center_30%]"
      >
        <template #overlay>
          <PushNotificationPreview
            title="Née cette nuit à Redon"
            body="Une portée gold, 2 mâles et 3 femelles."
            class="w-[318px] max-w-full md:w-[640px] lg:w-[460px]"
          />
        </template>
      </AuthPhotoVisual>
    </template>

    <form class="flex flex-col gap-3 md:gap-5 lg:gap-[18px]" @submit.prevent="submit">
      <UiErrorAlert v-if="errorMessage" :message="errorMessage" />
      <UFormField label="E-mail" name="email">
        <UInput
          v-model="userStore.emailTypedWhileSignedOut"
          type="email"
          autocomplete="username"
          autocapitalize="off"
          spellcheck="false"
          required
          size="xl"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Mot de passe" name="password" :error="hasRefusedCredentials">
        <template #hint>
          <NuxtLink
            to="/mot-de-passe-oublie"
            class="-my-3 inline-flex min-h-11 items-center text-sm font-extrabold text-coral-text no-underline md:text-[15px]"
          >
            Mot de passe oublié ?
          </NuxtLink>
        </template>
        <UiPasswordInput v-model="password" autocomplete="current-password" required />
      </UFormField>
      <div class="mt-1.5 flex flex-col gap-2.5 md:mt-2 md:gap-3">
        <UButton type="submit" block size="xl" :loading="isSubmitting" class="md:min-h-[58px] lg:min-h-14">
          Se connecter
        </UButton>
        <UButton
          to="/inscription"
          color="neutral"
          variant="outline"
          block
          size="xl"
          class="bg-transparent md:min-h-[58px] lg:min-h-14"
        >
          Créer un compte
        </UButton>
      </div>
    </form>
  </AuthScreen>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref } from 'vue'
import { RefusedRequestError } from '~/services/authService'

const CREDENTIALS_REFUSED_STATUS: number = 401

definePageMeta({ layout: 'signed-out', isGuestOnlyScreen: true })
useHead({ title: 'Connexion · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

const password: Ref<string> = ref('')
const isSubmitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string | null> = ref(null)
const hasRefusedCredentials: Ref<boolean> = ref(false)

/**
 * Sign in with the typed credentials, then open the litters; a refusal turns the password field coral.
 */
async function submit(): Promise<void> {
  isSubmitting.value = true
  errorMessage.value = null
  hasRefusedCredentials.value = false
  try {
    await userStore.login({ email: userStore.emailTypedWhileSignedOut.trim(), password: password.value })
    await navigateTo('/')
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Connexion impossible'
    hasRefusedCredentials.value = error instanceof RefusedRequestError && error.status === CREDENTIALS_REFUSED_STATUS
  } finally {
    isSubmitting.value = false
  }
}
</script>
