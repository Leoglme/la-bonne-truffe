<template>
  <section
    v-if="canConfirmColor"
    aria-label="Couleur de la portée"
    class="flex flex-col"
    :class="
      props.isInSidePanel
        ? 'gap-2.5'
        : 'gap-2.5 rounded-[20px] bg-card px-4 py-3.5 shadow-card md:gap-3 md:rounded-card-compact md:px-[22px] md:py-5'
    "
  >
    <template v-if="confirmedColor !== null && !isChooserOpen">
      <p class="m-0 text-sm text-ink-secondary md:text-base">
        Couleur confirmée après ton appel :
        <strong class="text-ink">{{ COAT_COLOR_LABELS[confirmedColor] }}</strong>
      </p>
      <div class="flex gap-5">
        <button
          type="button"
          :disabled="isSaving"
          class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text disabled:opacity-60"
          @click="openChooser"
        >
          Changer
        </button>
        <button
          type="button"
          :disabled="isSaving"
          class="min-h-9 border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
          @click="removeConfirmation"
        >
          Retirer
        </button>
      </div>
    </template>

    <template v-else-if="isChooserOpen">
      <p class="m-0 text-sm font-bold md:text-base">
        {{ confirmedColor === null ? 'Après ton appel, confirme la couleur' : 'Quelle couleur, finalement ?' }}
      </p>
      <div role="group" aria-label="Couleurs possibles" class="flex flex-wrap gap-2">
        <button
          v-for="color in offeredColors"
          :key="color"
          type="button"
          :aria-pressed="color === confirmedColor"
          :disabled="isSaving"
          class="inline-flex min-h-9 items-center gap-1.5 rounded-full border-0 px-3 text-[13px] font-extrabold disabled:opacity-60"
          :class="color === confirmedColor ? 'bg-ink text-cream' : 'bg-chip text-ink-secondary'"
          @click="confirmColor(color)"
        >
          <span
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: resolveCoatDotColor(color) }"
            aria-hidden="true"
          />
          {{ COAT_COLOR_LABELS[color] }}
        </button>
        <button
          v-if="canOfferEveryColor"
          type="button"
          :disabled="isSaving"
          class="min-h-9 rounded-full border-2 border-dashed border-line-strong bg-transparent px-3 text-[13px] font-extrabold text-ink-muted disabled:opacity-60"
          @click="isEveryColorOffered = true"
        >
          Une autre couleur
        </button>
      </div>
      <button
        type="button"
        :disabled="isSaving"
        class="min-h-9 self-start border-0 bg-transparent p-0 text-sm font-extrabold text-ink-muted disabled:opacity-60"
        @click="closeChooser"
      >
        {{ confirmedColor === null ? 'Je ne sais pas encore' : 'Annuler' }}
      </button>
    </template>

    <button
      v-else
      type="button"
      class="min-h-9 self-start border-0 bg-transparent p-0 text-sm font-extrabold text-coral-text"
      @click="openChooser"
    >
      Confirmer la couleur après ton appel
    </button>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { CoatColor, LitterColor, LitterDetail, LitterSourceListing } from '~/types/api'
import type { CriteriaColorRow } from '~/types/Criteria'
import type { LitterColorConfirmationProps } from '~/types/LitterColorConfirmation'
import { computed, ref, watch } from 'vue'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { COCKER_COAT_PALETTES, ILLUSTRATED_COATS } from '~/constants/cockerCoatPalettes'
import { MAIN_COLOR_ROWS, OTHER_COLOR_ROWS } from '~/constants/criteriaOptions'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterColorConfirmationProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInSidePanel: { type: Boolean, default: false },
})

const littersStore: ReturnType<typeof useLittersStore> = useLittersStore()
const toast: ReturnType<typeof useToast> = useToast()

const CONFIRMABLE_COAT_COLORS: CoatColor[] = [...MAIN_COLOR_ROWS, ...OTHER_COLOR_ROWS].map(
  (row: CriteriaColorRow): CoatColor => row.color,
)

const isChooserOpen: Ref<boolean> = ref(false)
const isEveryColorOffered: Ref<boolean> = ref(false)
const isSaving: Ref<boolean> = ref(false)

const confirmedColor: ComputedRef<CoatColor | null> = computed(
  (): CoatColor | null =>
    props.litter.colors.find((reading: LitterColor): boolean => reading.confidence === 'confirmed')?.color ?? null,
)
const canConfirmColor: ComputedRef<boolean> = computed(
  (): boolean => confirmedColor.value !== null || !LitterPresentation.hasKnownColors(props.litter.colors),
)
const ambiguousColors: ComputedRef<CoatColor[]> = computed((): CoatColor[] => {
  const colors: CoatColor[] = props.litter.listings
    .filter((listing: LitterSourceListing): boolean => listing.is_active)
    .flatMap((listing: LitterSourceListing): LitterColor[] => listing.colors)
    .filter((reading: LitterColor): boolean => reading.confidence === 'ambiguous' && reading.color !== 'inconnue')
    .map((reading: LitterColor): CoatColor => reading.color)
  return [...new Set(colors)]
})
const canOfferEveryColor: ComputedRef<boolean> = computed(
  (): boolean => !isEveryColorOffered.value && ambiguousColors.value.length > 0,
)
const offeredColors: ComputedRef<CoatColor[]> = computed((): CoatColor[] =>
  canOfferEveryColor.value ? ambiguousColors.value : CONFIRMABLE_COAT_COLORS,
)

/**
 * Pick the colour of the dot drawn before a colour name.
 *
 * @param color - Canonical colour.
 * @returns The coat colour of its illustration, the « à confirmer » one for a colour without illustration.
 */
function resolveCoatDotColor(color: CoatColor): string {
  return COCKER_COAT_PALETTES[ILLUSTRATED_COATS[color] ?? 'inconnue'].coat
}

/**
 * Show the colour buttons, the colours of the source bundle first.
 */
function openChooser(): void {
  isEveryColorOffered.value = false
  isChooserOpen.value = true
}

/**
 * Hide the colour buttons without changing anything.
 */
function closeChooser(): void {
  isChooserOpen.value = false
}

/**
 * Confirm the colour heard on the phone; the litter is re-scored at once.
 *
 * @param color - The colour.
 */
async function confirmColor(color: CoatColor): Promise<void> {
  if (await sendConfirmedColors([color])) {
    isChooserOpen.value = false
  }
}

/**
 * Go back to what the sources say about the colour.
 */
async function removeConfirmation(): Promise<void> {
  if (await sendConfirmedColors([])) {
    openChooser()
  }
}

/**
 * Send the confirmed colours to the API, and say why when it refuses.
 *
 * @param colors - The confirmed colours, none to remove the confirmation.
 * @returns Whether the API accepted.
 */
async function sendConfirmedColors(colors: CoatColor[]): Promise<boolean> {
  isSaving.value = true
  try {
    await littersStore.confirmColors(props.litter.id, colors)
    return true
  } catch (error: unknown) {
    toast.add({ title: error instanceof Error ? error.message : 'Couleur non enregistrée', color: 'error' })
    return false
  } finally {
    isSaving.value = false
  }
}

watch(
  (): number => props.litter.id,
  (): void => {
    isChooserOpen.value = confirmedColor.value === null
    isEveryColorOffered.value = false
  },
  { immediate: true },
)
</script>
