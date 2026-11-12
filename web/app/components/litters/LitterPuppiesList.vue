<template>
  <section v-if="puppyLines.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <div class="mb-0.5 flex items-baseline justify-between gap-3">
      <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Les chiots</h2>
      <span v-if="caption" class="text-[13px] font-bold text-ink-label md:text-sm">{{ caption }}</span>
    </div>
    <div :class="props.isInWideLayout ? 'grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-3' : 'contents'">
      <component
        :is="line.href ? 'a' : 'div'"
        v-for="line in puppyLines"
        :key="line.key"
        :href="line.href ?? undefined"
        :target="line.href ? '_blank' : undefined"
        :rel="line.href ? 'noopener' : undefined"
        class="flex items-center gap-3 rounded-[18px] bg-card py-2.5 pr-3.5 pl-2.5 text-ink no-underline shadow-card hover:text-ink md:gap-4 md:rounded-[20px] md:pr-[18px]"
        :class="line.isGone ? 'opacity-60' : ''"
      >
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
            v-if="line.stateLabel"
            class="text-sm md:text-[15px]"
            :class="line.isAvailable ? 'font-bold text-ink-secondary' : 'text-ink-muted'"
          >
            {{ line.stateLabel }}
          </span>
        </span>
        <UIcon v-if="line.href" name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
      </component>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterPuppyLine } from '~/types/Litter'
import type { LitterPuppiesListProps } from '~/types/LitterPuppiesList'
import { computed } from 'vue'
import { PUPPY_SEX_TEXT_CLASSES } from '~/constants/litterLabels'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterPuppiesListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
  isInWideLayout: { type: Boolean, default: false },
})

const PUPPY_ILLUSTRATION_SIZE_IN_PIXELS: number = 48

const puppyLines: ComputedRef<LitterPuppyLine[]> = computed((): LitterPuppyLine[] =>
  LitterDetailPresentation.buildPuppyLines(props.litter),
)
const caption: ComputedRef<string | null> = computed((): string | null =>
  LitterDetailPresentation.buildPuppiesCaption(props.litter.listings, new Date()),
)
</script>
