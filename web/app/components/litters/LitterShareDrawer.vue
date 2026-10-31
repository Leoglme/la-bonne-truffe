<template>
  <UDrawer
    :open="props.open"
    title="Partager cette portée"
    description="Une page qui s’ouvre sans compte, avec le téléphone de l’éleveur. Valable 30 jours."
    :ui="{
      content: 'rounded-t-3xl bg-cream md:mx-auto md:w-full md:max-w-md',
      container: 'gap-4 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-center gap-3 rounded-[20px] bg-card p-2.5 shadow-card">
          <LitterTileFrame :litter="props.litter" class="size-14 overflow-hidden rounded-[14px]">
            <LitterVisual :litter="props.litter" :illustration-size-in-pixels="44" photo-position="center 30%" />
          </LitterTileFrame>
          <span class="flex min-w-0 flex-col gap-0.5">
            <span class="truncate font-display text-[17px] leading-[1.2] font-semibold">{{ props.litter.name }}</span>
            <span class="text-[13px] text-ink-muted">{{ LitterSharePresentation.buildSummaryLine(props.litter) }}</span>
          </span>
        </div>

        <template v-if="sharedUrl === null">
          <div class="flex flex-col gap-2">
            <label :for="messageFieldId" class="text-[13px] font-extrabold text-ink-secondary">Un mot pour eux</label>
            <textarea
              :id="messageFieldId"
              v-model="message"
              rows="2"
              :aria-invalid="isMessageTooLong"
              :aria-describedby="isMessageTooLong ? messageLimitId : undefined"
              placeholder="Celle-là me plaît bien, on appelle demain ?"
              class="resize-none rounded-[18px] border-0 bg-card px-4 py-3 text-[15px] text-ink shadow-card"
              :class="isMessageTooLong ? 'outline-2 outline-coral' : 'focus:outline-2 focus:outline-line-strong'"
            />
            <p v-if="isMessageTooLong" :id="messageLimitId" class="m-0 text-sm font-bold text-coral-text">
              {{ message.length }}/{{ MAX_SHARE_MESSAGE_LENGTH }} caractères maximum
            </p>
          </div>
          <UiErrorAlert v-if="shareError" :message="shareError" />
          <UButton
            icon="i-lucide-share"
            size="xl"
            loading-auto
            :disabled="isMessageTooLong"
            class="w-full justify-center"
            @click="shareLink"
          >
            Envoyer le lien
          </UButton>
        </template>
        <template v-else>
          <div class="flex flex-col gap-2 rounded-2xl bg-lof-pastel px-4 py-3.5">
            <span class="inline-flex items-center gap-2 text-[15px] font-extrabold text-lof-ink">
              <UIcon name="i-lucide-check" class="size-5" />
              {{ isLinkCopied ? 'Lien copié, colle-le dans ton message' : 'Ton lien est prêt' }}
            </span>
            <span class="text-sm break-all text-ink-secondary select-all">{{ sharedUrl }}</span>
          </div>
          <UButton
            v-if="canUseShareSheet || !isLinkCopied"
            :icon="canUseShareSheet ? 'i-lucide-share' : 'i-lucide-copy'"
            size="xl"
            class="w-full justify-center"
            @click="handOverLink"
          >
            {{ canUseShareSheet ? 'Envoyer le lien' : 'Copier le lien' }}
          </UButton>
        </template>

        <button
          type="button"
          class="min-h-11 self-center border-0 bg-transparent px-2 text-[15px] font-extrabold text-ink-secondary"
          @click="emit('update:open', false)"
        >
          {{ sharedUrl === null ? 'Annuler' : 'Fermer' }}
        </button>
      </div>
    </template>
  </UDrawer>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterDetail, LitterShareLink } from '~/types/api'
import type { LitterShareDrawerEmits, LitterShareDrawerProps } from '~/types/LitterShareDrawer'
import { computed, ref, useId, watch } from 'vue'
import { MAX_SHARE_MESSAGE_LENGTH } from '~/constants/litterLimits'
import { SharesService } from '~/services/sharesService'
import { LitterSharePresentation } from '~/utils/litterSharePresentation'

const props: LitterShareDrawerProps = defineProps({
  open: { type: Boolean, required: true },
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const emit: LitterShareDrawerEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const messageFieldId: string = useId()
const messageLimitId: string = useId()
const canUseShareSheet: boolean = import.meta.client && typeof navigator.share === 'function'

const message: Ref<string> = ref('')
const shareError: Ref<string | null> = ref(null)
const sharedUrl: Ref<string | null> = ref(null)
const isLinkCopied: Ref<boolean> = ref(false)

const isMessageTooLong: ComputedRef<boolean> = computed((): boolean => message.value.length > MAX_SHARE_MESSAGE_LENGTH)

/**
 * Create the link, then hand it over at once: the share sheet of the phone, or the clipboard.
 */
async function shareLink(): Promise<void> {
  shareError.value = null
  const trimmedMessage: string = message.value.trim()
  try {
    const link: LitterShareLink = await SharesService.create(
      props.litter.id,
      trimmedMessage === '' ? null : trimmedMessage,
    )
    sharedUrl.value = link.url
  } catch (error: unknown) {
    shareError.value = error instanceof Error ? error.message : 'Le lien n’a pas pu être créé, réessaie.'
    return
  }
  await handOverLink()
}

/**
 * Open the share sheet, or copy the link; when the device refuses, the link and its button stay in the drawer.
 */
async function handOverLink(): Promise<void> {
  if (sharedUrl.value === null) {
    return
  }
  if (canUseShareSheet) {
    try {
      await navigator.share({ title: props.litter.name, text: buildShareText(), url: sharedUrl.value })
    } catch {
      return
    }
    emit('update:open', false)
    return
  }
  try {
    await navigator.clipboard.writeText(sharedUrl.value)
  } catch {
    return
  }
  isLinkCopied.value = true
}

/**
 * The text that goes with the link in the message.
 *
 * @returns The word typed in the drawer, or the name of the litter.
 */
function buildShareText(): string {
  const trimmedMessage: string = message.value.trim()
  return trimmedMessage === '' ? `${props.litter.name}, sur La Bonne Truffe` : trimmedMessage
}

watch(
  (): boolean => props.open,
  (isOpen: boolean): void => {
    if (isOpen) {
      message.value = ''
      shareError.value = null
      sharedUrl.value = null
      isLinkCopied.value = false
    }
  },
)
</script>
