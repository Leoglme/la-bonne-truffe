<template>
  <section class="flex w-full max-w-[420px] flex-col gap-6 rounded-card bg-card px-6 py-8 shadow-card md:px-8">
    <UiAppLogo />
    <div class="flex flex-col gap-1">
      <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold">Bon retour</h1>
      <p class="m-0 text-[15px] text-ink-muted">La truffe est à l’affût. Connecte-toi pour voir les portées.</p>
    </div>

    <form class="flex flex-col gap-4" @submit.prevent="submit">
      <UFormField label="Email" name="email">
        <UInput v-model="email" type="email" autocomplete="username" required size="xl" class="w-full" />
      </UFormField>
      <UFormField label="Mot de passe" name="password">
        <UInput v-model="password" type="password" autocomplete="current-password" required size="xl" class="w-full" />
      </UFormField>
      <p v-if="errorMessage" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ errorMessage }}</p>
      <UButton type="submit" size="xl" block :loading="isSubmitting">Se connecter</UButton>
    </form>
  </section>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref } from 'vue'

definePageMeta({ layout: 'signed-out' })
useHead({ title: 'Connexion · La Bonne Truffe' })

const userStore: ReturnType<typeof useUserStore> = useUserStore()

const email: Ref<string> = ref('')
const password: Ref<string> = ref('')
const isSubmitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string | null> = ref(null)

/**
 * Sign in with the typed credentials, then open the litters.
 */
async function submit(): Promise<void> {
  isSubmitting.value = true
  errorMessage.value = null
  try {
    await userStore.login({ email: email.value, password: password.value })
    await navigateTo('/')
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Connexion impossible'
  } finally {
    isSubmitting.value = false
  }
}
</script>
