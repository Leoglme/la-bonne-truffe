<template>
  <section class="flex flex-col rounded-[26px] bg-card px-[22px] py-5 shadow-card">
    <h2 v-if="props.title" class="m-0 font-display text-[22px] font-semibold">{{ props.title }}</h2>
    <slot />
  </section>
</template>

<script lang="ts" setup>
import type { UiSectionCardProps } from '~/types/UiSectionCard'

const props: UiSectionCardProps = defineProps({
  title: { type: String, default: '' },
})
</script>
