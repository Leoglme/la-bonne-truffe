<template>
  <div
    class="mx-auto flex min-h-dvh w-full max-w-[820px] flex-col px-5 pt-6 pb-[34px] md:px-8 md:pt-9 md:pb-10 xl:grid xl:max-w-none xl:grid-cols-[minmax(0,1fr)_600px] xl:grid-rows-[auto_minmax(0,1fr)] xl:p-0"
  >
    <header class="flex xl:col-start-2 xl:row-start-1 xl:px-20 xl:pt-8">
      <UiAppLogo />
    </header>

    <div
      class="mt-4 md:mt-7 xl:sticky xl:top-0 xl:col-start-1 xl:row-span-2 xl:row-start-1 xl:mt-0 xl:h-dvh xl:self-start xl:py-6 xl:ps-6"
    >
      <slot name="visual" />
    </div>

    <div class="flex flex-col xl:col-start-2 xl:row-start-2 xl:justify-center xl:px-20 xl:pt-10 xl:pb-[88px]">
      <div class="mt-[22px] flex flex-col gap-0.5 md:mt-9 md:gap-1 xl:mt-0 xl:gap-1.5">
        <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px] xl:text-4xl">
          {{ props.title }}
        </h1>
        <p class="m-0 text-[15px] text-ink-muted md:text-lg xl:text-[17px]">
          <slot name="subtitle">{{ props.subtitle }}</slot>
        </p>
      </div>
      <div class="mt-4 md:mt-7 xl:mt-8">
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
