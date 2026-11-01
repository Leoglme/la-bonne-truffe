<template>
  <span
    v-if="props.logo === 'website'"
    aria-hidden="true"
    class="inline-flex size-10 shrink-0 items-center justify-center rounded-[10px] border border-line bg-card text-ink-secondary md:size-11"
  >
    <UIcon name="i-lucide-globe" class="size-5" />
  </span>
  <img
    v-else
    :src="LINK_LOGO_IMAGES[props.logo]"
    alt=""
    width="44"
    height="44"
    class="size-10 shrink-0 rounded-[10px] border border-line md:size-11"
  />
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LinkLogo, UiLinkLogoProps } from '~/types/UiLinkLogo'
import { LINK_LOGO_IMAGES } from '~/constants/linkLogos'

const props: UiLinkLogoProps = defineProps({
  logo: { type: String as PropType<LinkLogo>, required: true },
})
</script>
