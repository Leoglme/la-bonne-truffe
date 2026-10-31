<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <header class="flex shrink-0 items-center gap-2.5 px-5 pt-4 md:gap-3.5 md:px-8 md:pt-9 lg:max-w-5xl lg:px-10">
      <button
        type="button"
        aria-label="Retour aux éleveurs"
        class="inline-flex size-11 shrink-0 items-center justify-center rounded-full border-0 bg-card text-ink shadow-floating md:size-[52px]"
        @click="goBack"
      >
        <UIcon name="i-lucide-chevron-left" class="size-5 md:size-[22px]" />
      </button>
      <div
        class="relative flex min-h-[50px] grow items-center gap-3 rounded-full border-2 border-coral bg-card ps-4 pe-2 ring-4 ring-coral-pastel md:min-h-[58px] md:ps-5"
      >
        <UIcon name="i-lucide-search" class="size-5 shrink-0 text-ink md:size-[22px]" />
        <label :for="searchFieldId" class="sr-only">Rechercher un éleveur ou une portée</label>
        <input
          :id="searchFieldId"
          ref="searchField"
          type="search"
          :value="breedersStore.searchQuery"
          placeholder="Éleveur, affixe, ville…"
          autocomplete="off"
          enterkeyhint="search"
          class="min-w-0 grow border-0 bg-transparent py-2 text-[17px] font-bold text-ink outline-none placeholder:text-ink-label md:text-lg [&::-webkit-search-cancel-button]:hidden"
          @input="onInput"
          @keydown.enter="rememberQuery"
        />
        <button
          v-if="breedersStore.searchQuery !== ''"
          type="button"
          aria-label="Effacer la recherche"
          class="inline-flex size-9 shrink-0 items-center justify-center rounded-full border-0 bg-chip text-ink-secondary"
          @click="clearSearch"
        >
          <UIcon name="i-lucide-x" class="size-[18px]" />
        </button>
      </div>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="flex flex-col gap-5 px-5 pt-5 pb-6 md:gap-6 md:px-8 md:pt-6 md:pb-8 lg:max-w-5xl lg:px-10">
        <template v-if="breedersStore.searchQuery.trim() === ''">
          <section v-if="recentQueries.length > 0" class="flex flex-col gap-3">
            <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Récentes</h2>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="recentQuery in recentQueries"
                :key="recentQuery"
                type="button"
                class="min-h-10 rounded-full border-0 bg-card px-4 text-sm font-bold text-ink-secondary shadow-chip md:min-h-11 md:text-[15px]"
                @click="searchFor(recentQuery)"
              >
                {{ recentQuery }}
              </button>
            </div>
          </section>
          <section class="hidden items-center gap-6 rounded-card bg-gold-pastel px-7 py-6 md:flex">
            <div class="flex min-w-0 flex-col gap-2">
              <h2 class="m-0 font-display text-2xl font-semibold">Trouvé un éleveur sur Facebook ?</h2>
              <p class="m-0 text-base text-ink-secondary">
                Tape ce que tu as sous les yeux : l’affixe, le nom de la personne, la ville, le code postal ou le SIREN.
                L’app cherche sans tenir compte des accents, des espaces ni des majuscules, dans la Centrale Canine, le
                Spaniel Club, Chiens de France et tes propres ajouts.
              </p>
            </div>
            <CockerIllustration coat="gold" :size-in-pixels="132" class="shrink-0" />
          </section>
          <p class="m-0 text-[15px] text-ink-muted md:hidden">
            Tape l’affixe, le nom, la ville, le code postal ou le SIREN : les accents et les espaces ne comptent pas.
          </p>
        </template>

        <template v-else>
          <p v-if="breedersStore.searchError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
            {{ breedersStore.searchError }}
          </p>
          <div
            v-else-if="breedersStore.isSearching && breedersStore.searchResults === null"
            aria-busy="true"
            aria-label="Recherche en cours"
            class="flex flex-col gap-3"
          >
            <USkeleton v-for="placeholder in 2" :key="placeholder" class="h-[96px] rounded-card-compact" />
          </div>
          <template v-else-if="breedersStore.searchResults">
            <section v-if="breedersStore.searchResults.breeders.length > 0" class="flex flex-col gap-3">
              <span class="flex items-baseline justify-between gap-3">
                <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Élevages</h2>
                <span class="text-[13px] font-bold text-ink-label md:text-sm">{{ breedersCountLabel }}</span>
              </span>
              <BreederRowCard
                v-for="breeder in breedersStore.searchResults.breeders"
                :key="breeder.id"
                :breeder="breeder"
                is-source-shown
                @click="rememberQuery"
              />
            </section>
            <section v-if="breedersStore.searchResults.litters.length > 0" class="flex flex-col gap-3">
              <h2 class="m-0 font-display text-lg font-semibold md:text-xl">Portées</h2>
              <LitterRowCard
                v-for="litter in breedersStore.searchResults.litters"
                :key="litter.id"
                :litter="litter"
                @click="rememberQuery"
              />
            </section>
            <div
              v-if="
                breedersStore.searchResults.breeders.length === 0 && breedersStore.searchResults.litters.length === 0
              "
              class="flex flex-col gap-2 rounded-card bg-card px-5 py-5 shadow-card md:px-7 md:py-6"
            >
              <h2 class="m-0 font-display text-xl font-semibold md:text-[22px]">
                Rien avec « {{ breedersStore.searchQuery.trim() }} »
              </h2>
              <p class="m-0 text-[15px] text-ink-secondary md:text-base">
                Essaie la ville, le code postal ou une partie de l’affixe. Un élevage qui n’a jamais déclaré de portée
                de cocker n’est dans aucune source : ajoute-le à la main, l’app le rapprochera dès qu’une portée sort.
              </p>
            </div>
          </template>

          <NuxtLink
            :to="{ path: '/eleveurs/nouveau', query: { nom: breedersStore.searchQuery.trim() } }"
            class="flex items-center gap-3.5 rounded-card-compact border-2 border-dashed border-coral bg-card px-4 py-3.5 text-ink no-underline hover:text-ink md:px-5 md:py-4"
          >
            <span
              class="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-coral-pastel text-coral-text md:size-11"
            >
              <UIcon name="i-lucide-plus" class="size-5" />
            </span>
            <span class="flex min-w-0 flex-col gap-0.5">
              <span class="text-[15px] font-extrabold md:text-[17px]">
                Pas dans la liste ? Ajouter « {{ breedersStore.searchQuery.trim() }} » à la main
              </span>
              <span class="text-[13px] text-ink-muted md:text-sm">
                Un nom, une ville, un lien Facebook : ça suffit pour le suivre.
              </span>
            </span>
          </NuxtLink>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { UseBackNavigationReturn } from '~/types/Composables'
import { computed, onMounted, onUnmounted, ref, useId } from 'vue'
import {
  BREEDER_RECENT_SEARCHES_COUNT,
  BREEDER_RECENT_SEARCHES_STORAGE_KEY,
  BREEDER_SEARCH_DEBOUNCE_MS,
} from '~/constants/breederOptions'
import { FrenchText } from '~/utils/frenchText'

definePageMeta({ isPushedScreen: true })

useHead({ title: 'Rechercher un éleveur · La Bonne Truffe' })

const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
const { goBack }: UseBackNavigationReturn = useBackNavigation('/eleveurs')

const searchFieldId: string = useId()

const searchField: Ref<HTMLInputElement | null> = ref(null)
const recentQueries: Ref<string[]> = ref([])

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const breedersCountLabel: ComputedRef<string> = computed((): string => {
  const count: number = breedersStore.searchResults?.breeders.length ?? 0
  return `${count} ${FrenchText.pickForm(count, 'élevage', 'élevages')}`
})

/**
 * Search for what was typed, once the typing pauses.
 *
 * @param event - Input in the search field.
 */
function onInput(event: Event): void {
  const input: EventTarget | null = event.target
  if (!(input instanceof HTMLInputElement)) {
    return
  }
  const query: string = input.value
  breedersStore.searchQuery = query
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout((): void => {
    debounceTimer = null
    breedersStore.search(query)
  }, BREEDER_SEARCH_DEBOUNCE_MS)
}

/**
 * Search for a query at once, as when a recent one is tapped.
 *
 * @param query - The query.
 */
async function searchFor(query: string): Promise<void> {
  await breedersStore.search(query)
  searchField.value?.focus()
}

/**
 * Forget the query and its suggestions, and give the field back.
 */
function clearSearch(): void {
  breedersStore.clearSearch()
  searchField.value?.focus()
}

/**
 * Read the recent queries kept on this device.
 *
 * @returns The queries, the latest first.
 */
function readRecentQueries(): string[] {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(BREEDER_RECENT_SEARCHES_STORAGE_KEY) ?? '[]')
    return Array.isArray(stored) ? stored.filter((entry: unknown): entry is string => typeof entry === 'string') : []
  } catch {
    return []
  }
}

/**
 * Keep the query among the recent ones, when it led somewhere.
 */
function rememberQuery(): void {
  const query: string = breedersStore.searchQuery.trim()
  if (query === '') {
    return
  }
  const queries: string[] = [query, ...recentQueries.value.filter((entry: string): boolean => entry !== query)].slice(
    0,
    BREEDER_RECENT_SEARCHES_COUNT,
  )
  recentQueries.value = queries
  try {
    localStorage.setItem(BREEDER_RECENT_SEARCHES_STORAGE_KEY, JSON.stringify(queries))
  } catch {
    return
  }
}

onMounted((): void => {
  recentQueries.value = readRecentQueries()
  searchField.value?.focus()
})

onUnmounted((): void => {
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }
})
</script>
