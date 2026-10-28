<template>
  <AuthScreen
    v-if="linkState === 'invalid'"
    title="Ce lien ne marche plus"
    subtitle="Un lien pour changer de mot de passe ne sert qu’une fois et finit par expirer. Demande-en un nouveau, il arrive tout de suite."
  >
    <template #visual>
      <AuthIllustrationVisual coat="inconnue" badge-icon-name="i-lucide-clock" height-class="h-[200px] md:h-[420px]" />
    </template>

    <div class="flex flex-col gap-2.5 md:gap-3">
      <UButton to="/mot-de-passe-oublie" block size="xl" class="md:min-h-[58px] lg:min-h-14">
        Recevoir un nouveau lien
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
  </AuthScreen>

  <AuthScreen v-else title="Nouveau mot de passe">
    <template #subtitle>
      <template v-if="linkState === 'valid'">
        Pour le compte <strong class="font-extrabold text-ink">{{ accountEmail }}</strong
        >. Choisis-en un que personne ne devinera, pas même la truffe.
      </template>
      <template v-else>La truffe vérifie ton lien…</template>
    </template>
    <template #visual>
      <AuthIllustrationVisual
        coat="noir_et_feu"
        badge-icon-name="i-lucide-lock"
        height-class="h-[200px] md:h-[420px]"
      />
    </template>

    <form class="flex flex-col gap-3 md:gap-5 lg:gap-[18px]" @submit.prevent="savePassword">
      <UiErrorAlert v-if="errorMessage" :message="errorMessage" />
      <input :value="accountEmail" type="text" autocomplete="username" readonly hidden />
      <UFormField label="Nouveau mot de passe" name="password" :error="hasRefusedPassword">
        <template #hint>
          <span class="md:hidden">{{ PASSWORD_RULE_SHORT_HINT }}</span>
          <span class="hidden md:inline">{{ PASSWORD_RULE_HINT }}</span>
        </template>
        <UiPasswordInput v-model="password" autocomplete="new-password" required :disabled="linkState !== 'valid'" />
        <UiPasswordStrengthMeter :password="password" class="mt-2" />
      </UFormField>
      <div class="mt-1.5 flex flex-col gap-2.5 md:mt-2 md:gap-3">
        <UButton
          type="submit"
          block
          size="xl"
          :loading="isSaving"
          :disabled="linkState !== 'valid'"
          class="md:min-h-[58px] lg:min-h-14"
        >
          Enregistrer et me connecter
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
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { PasswordResetTarget } from '~/types/api'
import type { PasswordResetLinkState } from '~/types/PasswordResetLinkState'
import { computed, onMounted, ref } from 'vue'
import { PASSWORD_RULE_HINT, PASSWORD_RULE_MESSAGE, PASSWORD_RULE_SHORT_HINT } from '~/constants/passwordRules'
import { AuthService, RefusedRequestError } from '~/services/authService'
import { PasswordRules } from '~/utils/passwordRules'

definePageMeta({ layout: 'signed-out', isPublicScreen: true })
useHead({ title: 'Nouveau mot de passe · La Bonne Truffe' })

const route: RouteLocationNormalizedLoaded = useRoute()
const userStore: ReturnType<typeof useUserStore> = useUserStore()

const linkState: Ref<PasswordResetLinkState> = ref('checking')
const accountEmail: Ref<string> = ref('')
const password: Ref<string> = ref('')
const isSaving: Ref<boolean> = ref(false)
const errorMessage: Ref<string | null> = ref(null)
const hasRefusedPassword: Ref<boolean> = ref(false)

const token: ComputedRef<string> = computed((): string => {
  const tokenParameter: unknown = route.query['token']
  return typeof tokenParameter === 'string' ? tokenParameter : ''
})

/**
 * Check the link of the email before asking for the password; a refused link shows « Ce lien ne marche plus ».
 */
async function checkLink(): Promise<void> {
  if (!token.value) {
    linkState.value = 'invalid'
    return
  }
  try {
    const target: PasswordResetTarget = await AuthService.verifyPasswordResetLink({ token: token.value })
    accountEmail.value = target.email
    linkState.value = 'valid'
  } catch (error: unknown) {
    if (error instanceof RefusedRequestError) {
      linkState.value = 'invalid'
      return
    }
    errorMessage.value = error instanceof Error ? error.message : 'Vérification du lien impossible'
  }
}

/**
 * Save the new password, sign the account in, then open the litters; the rule is checked before the API.
 */
async function savePassword(): Promise<void> {
  errorMessage.value = null
  hasRefusedPassword.value = !PasswordRules.isStrongEnough(password.value)
  if (hasRefusedPassword.value) {
    errorMessage.value = PASSWORD_RULE_MESSAGE
    return
  }
  isSaving.value = true
  try {
    await userStore.resetPassword({ token: token.value, password: password.value })
    await navigateTo('/')
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Changement du mot de passe impossible'
  } finally {
    isSaving.value = false
  }
}

onMounted(async (): Promise<void> => {
  await checkLink()
})
</script>
