<template>
  <section v-if="puppyLines.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <div class="mb-0.5 flex items-baseline justify-between gap-3">
      <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Les chiots</h2>
      <span v-if="caption" class="text-[13px] font-bold text-ink-label md:text-sm">{{ caption }}</span>
    </div>
    <div :class="props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-3' : 'contents'">
      <div
        v-for="line in puppyLines"
        :key="line.key"
        class="relative flex items-center gap-3 rounded-[18px] bg-card py-2.5 pr-3.5 pl-2.5 text-ink shadow-card md:gap-4 md:rounded-[20px] md:pr-[18px]"
        :class="line.isGone ? 'opacity-60' : ''"
      >
        <a
          v-if="line.href"
          :href="line.href"
          target="_blank"
          rel="noopener"
          :aria-label="`Voir l’annonce du ${line.label.toLowerCase()}`"
          class="absolute inset-0 rounded-[inherit]"
        />
        <DogPortrait
          :photo-url="line.photoUrl"
          :color="line.color"
          size-class="size-16 rounded-[14px] md:size-[72px] md:rounded-2xl"
          :illustration-size-in-pixels="PUPPY_ILLUSTRATION_SIZE_IN_PIXELS"
        />
        <span class="flex min-w-0 grow flex-col">
          <span class="text-[15px] font-extrabold md:text-[17px]">
            {{ line.label
            }}<template v-if="line.sexLabel">
              · <span :class="PUPPY_SEX_TEXT_CLASSES[line.sex]">{{ line.sexLabel }}</span></template
            >
          </span>
          <span
            class="text-sm md:text-[15px]"
            :class="line.isAvailable ? 'font-bold text-ink-secondary' : 'text-ink-muted'"
          >
            <button
              type="button"
              :aria-label="line.knownColor ? `Changer la couleur du ${line.label.toLowerCase()}` : undefined"
              class="relative z-[1] inline-flex min-h-8 items-center gap-1.5 border-0 bg-transparent p-0 align-middle"
              :class="line.knownColor ? 'font-[inherit] text-[inherit]' : 'font-extrabold text-coral-text'"
              @click="openPuppyColorDialog(line)"
            >
              <template v-if="line.knownColor">
                <CockerIllustration :coat="ILLUSTRATED_COATS[line.knownColor]" :size-in-pixels="22" />
                {{ COAT_COLOR_LABELS[line.knownColor] }}
              </template>
              <template v-else>Couleur ?</template>
            </button>
            <template v-if="line.stateLabel"> · {{ writeStateAfterColor(line.stateLabel) }}</template>
          </span>
        </span>
        <UIcon
          v-if="line.href"
          name="i-lucide-external-link"
          class="size-5 shrink-0 text-coral-text"
          aria-hidden="true"
        />
      </div>
    </div>
    <LitterPuppyColorDialog
      v-model:open="isPuppyColorDialogOpen"
      :litter="props.litter"
      :puppy-line="puppyLineOfDialog"
    />
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterPuppyLine } from '~/types/Litter'
import type { LitterPuppiesListProps } from '~/types/LitterPuppiesList'
import { computed, ref } from 'vue'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import { ILLUSTRATED_COATS } from '~/constants/cockerCoatPalettes'
import { PUPPY_SEX_TEXT_CLASSES } from '~/constants/litterLabels'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterPuppiesListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInWideLayout: { type: Boolean, default: false },
})

const PUPPY_ILLUSTRATION_SIZE_IN_PIXELS: number = 48

const isPuppyColorDialogOpen: Ref<boolean> = ref(false)
const puppyLineOfDialog: Ref<LitterPuppyLine | null> = ref(null)

const puppyLines: ComputedRef<LitterPuppyLine[]> = computed((): LitterPuppyLine[] =>
  LitterDetailPresentation.buildPuppyLines(props.litter),
)
const caption: ComputedRef<string | null> = computed((): string | null =>
  LitterDetailPresentation.buildPuppiesCaption(props.litter.listings, new Date()),
)

/**
 * Open the window that notes the colour of a puppy.
 *
 * @param line - The row of the puppy.
 */
function openPuppyColorDialog(line: LitterPuppyLine): void {
  puppyLineOfDialog.value = line
  isPuppyColorDialogOpen.value = true
}

/**
 * Write where a puppy stands after its colour, in the middle of the line.
 *
 * @param stateLabel - « Disponible · 1 400 € », « Réservée ».
 * @returns « disponible · 1 400 € », « réservée ».
 */
function writeStateAfterColor(stateLabel: string): string {
  return stateLabel.charAt(0).toLowerCase() + stateLabel.slice(1)
}
</script>
