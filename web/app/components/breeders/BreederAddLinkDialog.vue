<template>
  <UiDialog
    :open="props.open"
    title="Ajouter un lien"
    description="Son site, sa page Facebook ou Instagram : colle l’adresse, l’app s’occupe du reste."
    has-cream-background
    :drawer-ui="{
      content: 'rounded-t-3xl bg-cream md:mx-auto md:w-full md:max-w-2xl',
      container: 'gap-5 px-5 pt-2 pb-8 md:px-8',
      title: 'font-display text-2xl font-semibold text-ink',
      description: 'text-[15px] text-ink-muted',
    }"
    @update:open="(isOpen: boolean): void => emit('update:open', isOpen)"
  >
    <template #body>
      <form class="flex flex-col gap-6" novalidate @submit.prevent="addLink">
        <div class="flex flex-col gap-2.5">
          <label
            class="flex flex-col gap-0.5 rounded-[20px] border-2 border-card bg-card px-5 py-3 shadow-card focus-within:border-coral focus-within:ring-4 focus-within:ring-coral-pastel"
          >
            <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Adresse</span>
            <input
              v-model="address"
              type="url"
              placeholder="https://…"
              autocomplete="url"
              inputmode="url"
              class="border-0 bg-transparent p-0 text-[17px] font-bold text-ink outline-none placeholder:font-semibold placeholder:text-ink-label md:text-lg"
            />
          </label>
          <div v-if="recognition" aria-live="polite" class="flex items-start gap-3 pt-1">
            <span
              aria-hidden="true"
              class="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-lof-pastel text-lof-ink"
            >
              <UIcon name="i-lucide-check" class="size-4" />
            </span>
            <span class="flex min-w-0 flex-col gap-2">
              <span class="flex flex-col gap-0.5">
                <span class="text-[17px] font-extrabold">{{ recognition.title }}</span>
                <span class="text-base text-ink-secondary">{{ recognition.helper }}</span>
              </span>
              <span v-if="recognition.accountLabels.length > 0" class="flex flex-wrap gap-2">
                <span
                  v-for="accountLabel in recognition.accountLabels"
                  :key="accountLabel"
                  class="inline-flex items-center rounded-full bg-chip px-3.5 py-1.5 text-[15px] font-extrabold text-ink-secondary"
                >
                  {{ accountLabel }}
                </span>
              </span>
            </span>
          </div>
          <p v-else-if="isPreviewing" aria-live="polite" class="m-0 pt-1 text-[15px] text-ink-muted">
            Lecture du lien…
          </p>
          <p v-if="errorMessage" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ errorMessage }}</p>
        </div>

        <div class="flex flex-col gap-2.5">
          <UButton
            type="submit"
            size="xl"
            class="min-h-[56px] w-full justify-center text-[17px] md:min-h-[60px] md:text-[19px]"
            :loading="isAdding"
            :disabled="address.trim() === ''"
          >
            Ajouter le lien
          </UButton>
          <UButton
            type="button"
            color="neutral"
            variant="outline"
            size="xl"
            class="min-h-[52px] w-full justify-center text-[17px]"
            :disabled="isAdding"
            @click="emit('update:open', false)"
          >
            Annuler
          </UButton>
        </div>
      </form>
    </template>
  </UiDialog>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederDetail, BreederLinkPreview } from '~/types/api'
import type { BreederLinkRecognition } from '~/types/Breeder'
import type { BreederAddLinkDialogEmits, BreederAddLinkDialogProps } from '~/types/BreederAddLinkDialog'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { BREEDER_LINK_PREVIEW_DEBOUNCE_MS } from '~/constants/breederOptions'
import { BreedersService } from '~/services/breedersService'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederAddLinkDialogProps = defineProps({
  open: { type: Boolean, required: true },
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})

const emit: BreederAddLinkDialogEmits = defineEmits<{
  (event: 'update:open', isOpen: boolean): void
}>()

const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()

let previewTimer: ReturnType<typeof setTimeout> | null = null

const address: Ref<string> = ref('')
const preview: Ref<BreederLinkPreview | null> = ref(null)
const isPreviewing: Ref<boolean> = ref(false)
const previewError: Ref<string | null> = ref(null)
const isAdding: Ref<boolean> = ref(false)
const addError: Ref<string | null> = ref(null)

const recognition: ComputedRef<BreederLinkRecognition | null> = computed((): BreederLinkRecognition | null =>
  preview.value === null ? null : BreederPresentation.buildLinkRecognition(preview.value, props.breeder),
)
const errorMessage: ComputedRef<string | null> = computed((): string | null => addError.value ?? previewError.value)

/**
 * Ask the API what the address is once the typing pauses; a blank address forgets the previous answer.
 *
 * @param typedAddress - The address typed or pasted.
 */
function previewAfterTypingPause(typedAddress: string): void {
  if (previewTimer !== null) {
    clearTimeout(previewTimer)
  }
  preview.value = null
  previewError.value = null
  addError.value = null
  isPreviewing.value = typedAddress.trim() !== ''
  if (!isPreviewing.value) {
    return
  }
  previewTimer = setTimeout(async (): Promise<void> => {
    previewTimer = null
    try {
      const linkPreview: BreederLinkPreview = await BreedersService.previewLink(props.breeder.id, { url: typedAddress })
      if (address.value === typedAddress) {
        preview.value = linkPreview
      }
    } catch (error: unknown) {
      if (address.value === typedAddress) {
        previewError.value = error instanceof Error ? error.message : 'Adresse non reconnue'
      }
    } finally {
      if (address.value === typedAddress) {
        isPreviewing.value = false
      }
    }
  }, BREEDER_LINK_PREVIEW_DEBOUNCE_MS)
}

/**
 * Add the link to the breeder, then close; when the API refuses it, say why in red.
 */
async function addLink(): Promise<void> {
  if (address.value.trim() === '' || isAdding.value) {
    return
  }
  isAdding.value = true
  addError.value = null
  try {
    await breedersStore.addLink(props.breeder.id, address.value)
    emit('update:open', false)
  } catch (error: unknown) {
    addError.value = error instanceof Error ? error.message : 'Ajout impossible'
  } finally {
    isAdding.value = false
  }
}

/**
 * Start each opening with an empty address.
 */
function resetForm(): void {
  if (previewTimer !== null) {
    clearTimeout(previewTimer)
    previewTimer = null
  }
  address.value = ''
  preview.value = null
  isPreviewing.value = false
  previewError.value = null
  addError.value = null
}

watch(address, (typedAddress: string): void => {
  previewAfterTypingPause(typedAddress)
})

watch(
  (): boolean => props.open,
  (isOpen: boolean): void => {
    if (isOpen) {
      resetForm()
    }
  },
)

onBeforeUnmount((): void => {
  if (previewTimer !== null) {
    clearTimeout(previewTimer)
  }
})
</script>
