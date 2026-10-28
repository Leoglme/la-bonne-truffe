<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <header
      class="flex shrink-0 items-start justify-between gap-4 px-5 pt-[58px] md:px-8 md:pt-9 lg:mx-auto lg:w-full lg:max-w-[820px]"
    >
      <div class="flex min-w-0 flex-col gap-0.5 md:gap-1">
        <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px]">{{ title }}</h1>
        <p v-if="subtitle" class="m-0 text-[15px] text-ink-muted md:text-lg">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>
    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="px-5 pt-5 pb-6 md:px-8 md:pt-7 md:pb-8 lg:mx-auto lg:max-w-[820px]">
        <slot />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * Frame of a tab screen (Suivi, Critères, Réglages): Fredoka title and subtitle above a scrolling area,
 * at the iPad measures of the mockup (36 px top, 32 px sides), 20 px sides on iPhone.
 */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
