<template>
  <div class="flex flex-col gap-5 px-5 pt-[58px] pb-6 md:gap-7 md:px-8 md:pt-9 md:pb-8 lg:px-10">
    <UiPageHeader title="Critères" subtitle="Ce que la truffe cherche pour toi, toutes les heures." />
    <UiEmptyStateCard
      title="Bientôt modifiables ici"
      description="Race, couleurs, départements, LOF, sexe et notifications : ton profil de départ est déjà enregistré."
    >
      <template #illustration>
        <span class="inline-flex size-[76px] shrink-0 items-center justify-center rounded-tile bg-gold-pastel">
          <CockerIllustration coat="gold" :size-in-pixels="58" />
        </span>
      </template>
    </UiEmptyStateCard>
  </div>
</template>

<script lang="ts" setup>
useHead({ title: 'Critères · La Bonne Truffe' })
</script>
