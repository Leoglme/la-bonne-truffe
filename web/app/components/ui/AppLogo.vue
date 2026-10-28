<template>
  <NuxtLink
    to="/"
    aria-label="La Bonne Truffe, accueil"
    class="inline-flex items-center gap-2 text-ink no-underline md:gap-2.5"
  >
    <svg viewBox="0 0 100 100" aria-hidden="true" class="size-8 md:size-9">
      <rect x="0" y="0" width="100" height="100" rx="22.5" fill="#E2552F" />
      <path
        d="M50 28 C58 28 64 31 68 35 C77 36 82 42 82 50 C82 66 66 78 50 86 C34 78 18 66 18 50 C18 42 23 36 32 35 C36 31 42 28 50 28 Z"
        fill="#FFF3E6"
      />
      <ellipse cx="39" cy="50" rx="6" ry="8.5" transform="rotate(-14 39 50)" fill="#E2552F" />
      <ellipse cx="61" cy="50" rx="6" ry="8.5" transform="rotate(14 61 50)" fill="#E2552F" />
      <ellipse cx="40" cy="37" rx="5" ry="2.6" transform="rotate(-18 40 37)" fill="#FFFFFF" opacity="0.6" />
    </svg>
    <span class="font-display text-[19px] font-semibold whitespace-nowrap md:text-[22px] lg:text-[21px]"
      >La Bonne Truffe</span
    >
  </NuxtLink>
</template>

<script lang="ts" setup>
/** The app logo: the rounded coral icon followed by the name in Fredoka (docs/06, « Le logo dans l'app »). */
</script>
