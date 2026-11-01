<template>
  <section class="flex flex-col gap-3">
    <h2 class="m-0 font-display text-[19px] font-semibold md:text-xl">Vu sur</h2>
    <ul v-if="links.length > 0" class="m-0 flex list-none flex-col gap-2.5 p-0">
      <li v-for="link in links" :key="link.key">
        <component
          :is="link.href ? 'a' : 'div'"
          :href="link.href ?? undefined"
          :target="link.href ? '_blank' : undefined"
          :rel="link.href ? 'noopener' : undefined"
          class="flex min-h-14 items-center gap-3 rounded-[20px] bg-card px-4 py-3 text-ink no-underline shadow-card hover:text-ink md:px-[18px]"
        >
          <span class="flex min-w-0 grow flex-col gap-0.5">
            <span class="text-[11px] font-extrabold tracking-[0.04em] text-ink-label uppercase md:text-[13px]">
              {{ link.label }}
            </span>
            <span class="truncate text-[15px] font-bold md:text-base">{{ link.description }}</span>
          </span>
          <UIcon v-if="link.href" name="i-lucide-external-link" class="size-5 shrink-0 text-coral-text" />
        </component>
      </li>
    </ul>
    <button
      type="button"
      aria-haspopup="dialog"
      class="inline-flex min-h-12 items-center gap-2 self-start border-0 bg-transparent px-1 text-base font-extrabold text-coral-text"
      @click="isAddLinkDialogOpen = true"
    >
      <UIcon name="i-lucide-plus" class="size-5" />
      Ajouter un lien
    </button>
    <BreederAddLinkDialog v-model:open="isAddLinkDialogOpen" :breeder="props.breeder" />
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType, Ref } from 'vue'
import type { BreederDetail } from '~/types/api'
import type { BreederSeenOnLink } from '~/types/Breeder'
import type { BreederSeenOnListProps } from '~/types/BreederSeenOnList'
import { computed, ref } from 'vue'
import { BreederPresentation } from '~/utils/breederPresentation'

const props: BreederSeenOnListProps = defineProps({
  breeder: { type: Object as PropType<BreederDetail>, required: true },
})

const isAddLinkDialogOpen: Ref<boolean> = ref(false)

const links: ComputedRef<BreederSeenOnLink[]> = computed((): BreederSeenOnLink[] =>
  BreederPresentation.listSeenOnLinks(props.breeder, new Date()),
)
</script>
