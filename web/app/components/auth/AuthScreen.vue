<template>
  <div
    class="mx-auto flex min-h-dvh w-full max-w-[820px] flex-col px-5 pt-14 pb-[34px] md:px-8 md:pt-9 md:pb-10 lg:grid lg:max-w-none lg:grid-cols-[600px_minmax(0,1fr)] lg:grid-rows-[auto_minmax(0,1fr)] lg:p-0"
  >
    <header class="flex lg:col-start-1 lg:row-start-1 lg:px-20 lg:pt-8">
      <UiAppLogo />
    </header>

    <div
      class="mt-4 md:mt-7 lg:sticky lg:top-0 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:mt-0 lg:h-dvh lg:self-start lg:py-6 lg:pe-6"
    >
      <slot name="visual" />
    </div>

    <div class="flex flex-col lg:col-start-1 lg:row-start-2 lg:justify-center lg:px-20 lg:pt-10 lg:pb-[88px]">
      <div class="mt-[22px] flex flex-col gap-0.5 md:mt-9 md:gap-1 lg:mt-0 lg:gap-1.5">
        <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px] lg:text-4xl">
          {{ props.title }}
        </h1>
        <p class="m-0 text-[15px] text-ink-muted md:text-lg lg:text-[17px]">
          <slot name="subtitle">{{ props.subtitle }}</slot>
        </p>
      </div>
      <div class="mt-4 md:mt-7 lg:mt-8">
        <slot />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { AuthScreenProps } from '~/types/AuthScreen'

const props: AuthScreenProps = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
