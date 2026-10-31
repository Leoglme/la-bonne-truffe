<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <header class="flex shrink-0 items-center gap-3.5 px-5 pt-4 md:px-8 md:pt-9 lg:max-w-5xl lg:px-10">
      <button
        type="button"
        aria-label="Retour"
        class="inline-flex size-11 shrink-0 items-center justify-center rounded-full border-0 bg-card text-ink shadow-floating md:size-[52px]"
        @click="goBack"
      >
        <UIcon name="i-lucide-chevron-left" class="size-5 md:size-[22px]" />
      </button>
      <UiAppLogo />
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <form
        class="flex flex-col gap-5 px-5 pt-5 pb-8 md:gap-6 md:px-8 md:pt-6 lg:max-w-3xl lg:px-10"
        novalidate
        @submit.prevent="submit(true)"
      >
        <div
          class="flex h-[140px] items-center justify-between overflow-hidden rounded-card bg-gold-pastel px-6 md:h-[180px] md:px-9"
        >
          <span
            class="rounded-full bg-card px-4 py-1.5 text-sm leading-normal font-extrabold tracking-[0.02em] text-coral-text uppercase"
          >
            Ajouté à la main
          </span>
          <CockerIllustration coat="gold" :size-in-pixels="150" class="-mb-7 shrink-0" />
        </div>

        <div class="flex flex-col gap-1 md:gap-2">
          <h1 class="m-0 font-display text-[30px] leading-[1.1] font-semibold md:text-[40px]">Ajouter un éleveur</h1>
          <p class="m-0 text-[15px] text-ink-muted md:text-lg">
            Trouvé sur Facebook, sur un panneau, par une amie ? Note ce que tu sais. L’app le rapprochera de la Centrale
            Canine et de Chiens de France dès qu’il déclare une portée.
          </p>
        </div>

        <p v-if="submitError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">{{ submitError }}</p>

        <div class="flex flex-col gap-3">
          <label
            v-for="field in TEXT_FIELDS"
            :key="field.key"
            class="flex flex-col gap-0.5 rounded-[20px] border-2 border-card bg-card px-5 py-3 shadow-card focus-within:border-coral focus-within:ring-4 focus-within:ring-coral-pastel"
          >
            <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">{{ field.label }}</span>
            <input
              v-model="form[field.key]"
              :type="field.type"
              :placeholder="field.placeholder"
              :autocomplete="field.autocomplete"
              :inputmode="field.inputMode"
              class="border-0 bg-transparent p-0 text-[17px] font-bold text-ink outline-none placeholder:font-semibold placeholder:text-ink-label md:text-lg"
            />
          </label>
          <label
            class="flex flex-col gap-0.5 rounded-[20px] border-2 border-card bg-card px-5 py-3 shadow-card focus-within:border-coral focus-within:ring-4 focus-within:ring-coral-pastel"
          >
            <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Une note pour toi</span>
            <textarea
              v-model="form.note"
              rows="2"
              placeholder="Vu dans le groupe « Cocker anglais Bretagne » : une portée gold prévue cet hiver…"
              class="resize-none border-0 bg-transparent p-0 text-[17px] font-bold text-ink outline-none placeholder:font-semibold placeholder:text-ink-label md:text-lg"
            />
          </label>
        </div>

        <div
          v-if="similarBreeders.length > 0"
          class="flex items-start gap-3 rounded-[20px] bg-chip px-4 py-3.5 text-[15px] text-ink-secondary"
        >
          <UIcon name="i-lucide-search" class="mt-0.5 size-5 shrink-0 text-coral-text" />
          <span>
            {{ similarIntro }}
            <template v-for="(similar, index) in similarBreeders" :key="similar.id">
              <NuxtLink :to="`/eleveurs/${similar.id}`" class="font-extrabold text-coral-text no-underline">
                {{ similar.name }}
              </NuxtLink>
              <span v-if="similar.city"> ({{ similar.city }})</span
              ><span>{{ index < similarBreeders.length - 1 ? ' et ' : '. ' }}</span>
            </template>
            Si c’est l’un d’eux, touche-le au lieu d’en créer une nouvelle fiche.
          </span>
        </div>

        <div class="flex flex-col gap-2.5">
          <UButton
            type="submit"
            size="xl"
            class="min-h-[56px] w-full justify-center gap-2 text-[17px] md:min-h-[60px] md:text-[19px]"
            :loading="isSubmitting"
            :disabled="form.display_name.trim() === ''"
          >
            <template #leading>
              <UiCustomIcon name="heart" :size-in-pixels="20" :stroke-width="2.2" />
            </template>
            Ajouter et suivre
          </UButton>
          <UButton
            type="button"
            color="neutral"
            variant="outline"
            size="xl"
            class="min-h-[52px] w-full justify-center text-[17px]"
            :disabled="isSubmitting || form.display_name.trim() === ''"
            @click="submit(false)"
          >
            Ajouter sans suivre
          </UButton>
        </div>
      </form>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LocationQueryValue, RouteLocationNormalizedLoaded } from 'vue-router'
import type { BreederCard, BreederCreate, BreederDetail, BreederSearchResults } from '~/types/api'
import type { BreederManualForm, BreederManualTextField } from '~/types/BreederManualForm'
import type { UseBackNavigationReturn } from '~/types/Composables'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { BREEDER_SEARCH_DEBOUNCE_MS, BREEDER_SIMILAR_NAMES_COUNT } from '~/constants/breederOptions'
import { BreedersService } from '~/services/breedersService'
import { BreederManualFormPresentation } from '~/utils/breederManualFormPresentation'

definePageMeta({ isPushedScreen: true })

useHead({ title: 'Ajouter un éleveur · La Bonne Truffe' })

const route: RouteLocationNormalizedLoaded = useRoute()
const breedersStore: ReturnType<typeof useBreedersStore> = useBreedersStore()
const { goBack }: UseBackNavigationReturn = useBackNavigation('/eleveurs')

const TEXT_FIELDS: BreederManualTextField[] = [
  {
    key: 'display_name',
    label: 'Nom de l’élevage ou de la personne',
    type: 'text',
    placeholder: 'Élevage des Joyaux du Lac',
    autocomplete: 'organization',
    inputMode: 'text',
  },
  {
    key: 'place',
    label: 'Ville ou code postal',
    type: 'text',
    placeholder: 'Guer, ou 56380',
    autocomplete: 'off',
    inputMode: 'text',
  },
  {
    key: 'link',
    label: 'Lien Facebook, Instagram ou site',
    type: 'url',
    placeholder: 'https://www.facebook.com/…',
    autocomplete: 'url',
    inputMode: 'url',
  },
  { key: 'phone', label: 'Téléphone', type: 'tel', placeholder: '06 …', autocomplete: 'tel', inputMode: 'tel' },
]

const form: Ref<BreederManualForm> = ref({ display_name: '', place: '', link: '', phone: '', note: '' })
const similarBreeders: Ref<BreederCard[]> = ref([])
const isSubmitting: Ref<boolean> = ref(false)
const submitError: Ref<string | null> = ref(null)

let similarTimer: ReturnType<typeof setTimeout> | null = null

const similarIntro: ComputedRef<string> = computed((): string =>
  similarBreeders.value.length === 1
    ? 'Un élevage connu ressemble à ce nom : '
    : 'Des élevages connus ressemblent à ce nom : ',
)

/**
 * Look for the breeders already known under a name close to the one typed, once the typing pauses.
 *
 * @param name - The name typed.
 */
function lookForSimilarBreeders(name: string): void {
  if (similarTimer !== null) {
    clearTimeout(similarTimer)
  }
  if (name.trim().length < 3) {
    similarBreeders.value = []
    return
  }
  similarTimer = setTimeout(async (): Promise<void> => {
    similarTimer = null
    try {
      const results: BreederSearchResults = await BreedersService.search(name, BREEDER_SIMILAR_NAMES_COUNT)
      if (form.value.display_name === name) {
        similarBreeders.value = results.breeders.filter((card: BreederCard): boolean => !card.is_manual)
      }
    } catch {
      similarBreeders.value = []
    }
  }, BREEDER_SEARCH_DEBOUNCE_MS)
}

/**
 * Add the breeder, then open its page in place of this screen.
 *
 * @param isFollowed - Whether to follow it at once.
 */
async function submit(isFollowed: boolean): Promise<void> {
  const payload: BreederCreate | null = BreederManualFormPresentation.buildPayload(form.value, isFollowed)
  if (payload === null || isSubmitting.value) {
    return
  }
  isSubmitting.value = true
  submitError.value = null
  try {
    const detail: BreederDetail = await breedersStore.createManual(payload)
    await navigateTo(`/eleveurs/${detail.id}`, { replace: true })
  } catch (error: unknown) {
    submitError.value = error instanceof Error ? error.message : 'Ajout impossible'
  } finally {
    isSubmitting.value = false
  }
}

watch(
  (): string => form.value.display_name,
  (name: string): void => lookForSimilarBreeders(name),
)

onMounted((): void => {
  const queryName: LocationQueryValue | LocationQueryValue[] | undefined = route.query['nom']
  if (typeof queryName === 'string' && queryName.trim() !== '') {
    form.value.display_name = queryName.trim()
  }
})

onUnmounted((): void => {
  if (similarTimer !== null) {
    clearTimeout(similarTimer)
  }
})
</script>
