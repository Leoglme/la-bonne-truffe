<template>
  <div v-if="lines.length > 0" class="flex flex-col gap-2 md:gap-2.5">
    <a
      v-for="line in lines"
      :key="line.key"
      :href="line.href ?? undefined"
      target="_blank"
      rel="noopener"
      class="flex min-h-14 items-center gap-3 rounded-2xl bg-card px-3.5 py-3 text-ink no-underline shadow-card hover:text-ink md:gap-4 md:rounded-[20px] md:px-[18px]"
    >
      <img
        v-if="line.thumbnailUrl"
        :src="line.thumbnailUrl"
        alt=""
        class="size-12 shrink-0 rounded-xl object-cover md:size-14 md:rounded-2xl"
      />
      <span class="flex min-w-0 grow flex-col">
        <span class="text-[11px] font-extrabold text-ink-label uppercase md:text-[13px]">{{ line.label }}</span>
        <span class="text-[15px] font-bold md:text-[17px]">{{ line.description }}</span>
      </span>
      <UIcon name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
    </a>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterDetail } from '~/types/api'
import type { LitterListingLine } from '~/types/Litter'
import type { LitterListingsListProps } from '~/types/LitterListingsList'
import { computed } from 'vue'
import { LitterDetailPresentation } from '~/utils/litterDetailPresentation'

const props: LitterListingsListProps = defineProps({
  litter: { type: Object as PropType<LitterDetail>, required: true },
})

const lines: ComputedRef<LitterListingLine[]> = computed((): LitterListingLine[] =>
  LitterDetailPresentation.buildListingLines(props.litter),
)
</script>
