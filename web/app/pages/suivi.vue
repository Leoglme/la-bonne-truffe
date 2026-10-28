<template>
  <div class="flex flex-col gap-5 px-5 pt-[58px] pb-6 md:gap-7 md:px-8 md:pt-9 md:pb-8 lg:px-10">
    <UiPageHeader title="Suivi" subtitle="Tes échanges avec les éleveurs, et qui rappeler." />
    <UiEmptyStateCard
      title="Rien pour l’instant"
      description="Quand tu suis une portée, elle arrive ici avec le statut de l’échange et le prochain rappel."
    >
      <template #illustration>
        <UIcon name="i-lucide-heart" class="size-9 shrink-0 text-coral" aria-hidden="true" />
      </template>
    </UiEmptyStateCard>
  </div>
</template>

<script lang="ts" setup>
useHead({ title: 'Suivi · La Bonne Truffe' })
</script>
