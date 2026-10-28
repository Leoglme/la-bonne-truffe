<template>
  <NuxtLink
    to="/"
    aria-label="La Bonne Truffe, accueil"
    class="text-ink no-underline hover:text-ink"
    :class="
      props.placement === 'sidebar'
        ? 'flex items-center gap-2.5 px-2.5 pt-1.5 pb-[22px]'
        : 'inline-flex items-center gap-2 md:gap-2.5'
    "
  >
    <svg
      viewBox="0 0 100 100"
      aria-hidden="true"
      class="shrink-0"
      :class="props.placement === 'sidebar' ? 'size-[38px]' : 'size-8 md:size-9'"
    >
      <rect x="0" y="0" width="100" height="100" rx="22.5" fill="#E2552F" />
      <path
        d="M50 28 C58 28 64 31 68 35 C77 36 82 42 82 50 C82 66 66 78 50 86 C34 78 18 66 18 50 C18 42 23 36 32 35 C36 31 42 28 50 28 Z"
        fill="#FFF3E6"
      />
      <ellipse cx="39" cy="50" rx="6" ry="8.5" transform="rotate(-14 39 50)" fill="#E2552F" />
      <ellipse cx="61" cy="50" rx="6" ry="8.5" transform="rotate(14 61 50)" fill="#E2552F" />
    </svg>
    <span
      class="font-display font-semibold"
      :class="props.placement === 'sidebar' ? 'text-[21px] leading-[1.5]' : 'text-[19px] md:text-[22px]'"
    >
      La Bonne Truffe
    </span>
  </NuxtLink>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { UiAppLogoPlacement, UiAppLogoProps } from '~/types/UiAppLogo'

const props: UiAppLogoProps = defineProps({
  placement: { type: String as PropType<UiAppLogoPlacement>, default: 'header' },
})
</script>
