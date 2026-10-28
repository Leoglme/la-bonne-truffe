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
    <UiAppIcon :class="props.placement === 'sidebar' ? 'size-[38px]' : 'size-8 md:size-9'" />
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
