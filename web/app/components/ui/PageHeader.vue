<template>
  <header class="flex flex-col gap-1">
    <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px]">{{ title }}</h1>
    <p class="m-0 text-[15px] text-ink-muted md:text-lg">{{ subtitle }}</p>
  </header>
</template>

<script lang="ts" setup>
/** Title of a tab screen in Fredoka, with its one-line subtitle. */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
