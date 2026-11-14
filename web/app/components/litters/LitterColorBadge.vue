<template>
  <span
    class="inline-flex max-w-full items-center gap-1.5 rounded-full py-0.5 pr-2.5 pl-0.5 font-extrabold"
    :class="badgeClass"
  >
    <span class="inline-flex shrink-0 items-center" aria-hidden="true">
      <CockerIllustration
        v-for="(coat, coatIndex) in badgeCoats"
        :key="coat"
        :coat="coat"
        :size-in-pixels="22"
        aria-hidden="true"
        class="rounded-full bg-card ring-2 ring-card"
        :class="coatIndex > 0 ? '-ml-1' : ''"
      />
    </span>
    <span class="min-w-0 truncate">
      <span v-if="!props.isLabelAlwaysShort" class="lg:hidden">
        {{ LitterPresentation.buildColorLabel(props.colors, false) }}
      </span>
      <span :class="props.isLabelAlwaysShort ? '' : 'hidden lg:inline'">
        {{ LitterPresentation.buildColorLabel(props.colors, true) }}
      </span>
    </span>
    <template v-if="isConfirmedByCall">
      <UIcon name="i-lucide-check" class="size-3.5 shrink-0" aria-hidden="true" />
      <span class="sr-only">, confirmée après ton appel</span>
    </template>
  </span>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import type { LitterColor } from '~/types/api'
import type { CockerCoat } from '~/types/CockerCoat'
import type { LitterColorBadgeProps } from '~/types/LitterColorBadge'
import { computed } from 'vue'
import { LitterPresentation } from '~/utils/litterPresentation'

const props: LitterColorBadgeProps = defineProps({
  colors: { type: Array as PropType<LitterColor[]>, required: true },
  isLabelAlwaysShort: { type: Boolean, default: false },
})

const badgeCoats: ComputedRef<CockerCoat[]> = computed((): CockerCoat[] =>
  LitterPresentation.listBadgeCoats(props.colors),
)
const badgeClass: ComputedRef<string> = computed((): string => LitterPresentation.resolveBadgeClass(props.colors))
const isConfirmedByCall: ComputedRef<boolean> = computed((): boolean =>
  LitterPresentation.isColorConfirmedByCall(props.colors),
)
</script>
