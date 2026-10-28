<template>
  <UiTabScreen title="Critères" subtitle="Ce que la truffe cherche pour toi, toutes les heures.">
    <template #actions>
      <button
        type="button"
        class="min-h-[52px] shrink-0 rounded-full border-0 px-[22px] text-[17px] font-extrabold"
        :class="criteriaStore.hasUnsavedChanges ? 'bg-coral text-white' : 'bg-chip text-ink-muted'"
        :disabled="!criteriaStore.hasUnsavedChanges || criteriaStore.isSaving"
        @click="criteriaStore.save()"
      >
        {{ saveLabel }}
      </button>
    </template>

    <p v-if="criteriaStore.loadError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
      {{ criteriaStore.loadError }}
    </p>
    <div v-else-if="draft" class="flex flex-col gap-[22px]">
      <p v-if="criteriaStore.saveError" role="alert" class="m-0 text-[15px] font-bold text-coral-text">
        {{ criteriaStore.saveError }}
      </p>

      <section class="flex items-center gap-[18px] rounded-[26px] bg-card px-[22px] py-[18px] shadow-card">
        <span class="inline-flex size-[76px] shrink-0 items-center justify-center rounded-tile bg-gold-pastel">
          <CockerIllustration coat="gold" :size-in-pixels="60" />
        </span>
        <div class="flex min-w-0 grow flex-col">
          <span class="text-[13px] font-extrabold tracking-[0.04em] text-ink-label uppercase">Race</span>
          <span class="font-display text-xl font-semibold md:text-2xl">Cocker spaniel anglais</span>
        </div>
        <UButton
          color="neutral"
          variant="outline"
          disabled
          title="Une seule race est suivie pour l’instant"
          class="hidden shrink-0 disabled:cursor-default disabled:opacity-100 md:inline-flex"
        >
          Changer
        </UButton>
      </section>

      <UiSectionCard title="Couleurs" class="gap-1.5">
        <p class="m-0 mb-2 text-[15px] text-ink-muted">
          Préférée : on te prévient tout de suite. Acceptable : dans le récap du soir.
        </p>
        <ul class="m-0 flex list-none flex-col p-0">
          <li
            v-for="row in shownColorRows"
            :key="row.color"
            class="flex flex-wrap items-center justify-between gap-3 border-t border-line py-3"
          >
            <span class="inline-flex items-center gap-3 text-[17px] font-bold md:min-w-40">
              <CockerIllustration :coat="row.coat" :size-in-pixels="40" />
              {{ COAT_COLOR_LABELS[row.color] }}
            </span>
            <UiChoiceButtons
              :model-value="criteriaStore.getColorLevel(row.color)"
              :options="COLOR_LEVEL_OPTIONS"
              :label="`Niveau pour la couleur ${COAT_COLOR_LABELS[row.color]}`"
              @update:model-value="(level: string): void => setColorLevel(row.color, level)"
            />
          </li>
        </ul>
        <button
          type="button"
          class="min-h-11 self-start border-0 bg-transparent px-1 text-[15px] font-extrabold text-coral-text"
          :aria-expanded="areOtherColorsShown"
          @click="areOtherColorsShown = !areOtherColorsShown"
        >
          {{
            areOtherColorsShown ? 'Masquer les autres couleurs' : `Voir les ${OTHER_COLOR_ROWS.length} autres couleurs`
          }}
        </button>
      </UiSectionCard>

      <UiSectionCard title="Où chercher" class="gap-3.5">
        <div role="group" aria-label="Régions" class="flex flex-wrap gap-2.5">
          <button
            v-for="region in NEARBY_REGIONS"
            :key="region"
            type="button"
            :aria-pressed="criteriaStore.isRegionSelected(region)"
            class="box-content min-h-[46px] rounded-full border-2 px-[18px] text-[15px] font-extrabold"
            :class="
              criteriaStore.isRegionSelected(region)
                ? 'border-ink bg-ink text-cream'
                : 'border-line-strong bg-card text-ink-secondary'
            "
            @click="criteriaStore.toggleRegion(region)"
          >
            {{ region }}
          </button>
        </div>
        <p class="m-0 text-[15px] text-ink-muted">{{ departmentsSentence }}</p>
      </UiSectionCard>

      <UiSectionCard title="Le chiot" class="gap-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span class="text-[17px] font-bold md:min-w-40">Pedigree LOF</span>
          <UiChoiceButtons
            :model-value="draft.lof_preference"
            :options="LOF_OPTIONS"
            label="Pedigree LOF"
            @update:model-value="setLofPreference"
          />
        </div>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span class="text-[17px] font-bold md:min-w-40">Sexe</span>
          <UiChoiceButtons
            :model-value="draft.sex_preference"
            :options="SEX_OPTIONS"
            label="Sexe"
            @update:model-value="setSexPreference"
          />
        </div>
        <div class="flex items-center justify-between gap-3">
          <span class="flex flex-col">
            <span class="text-[17px] font-bold">Portées à naître</span>
            <span class="text-sm text-ink-muted">Pour appeler l’éleveur avant la naissance</span>
          </span>
          <USwitch v-model="draft.include_expected_litters" aria-label="Inclure les portées à naître" />
        </div>
      </UiSectionCard>

      <UiSectionCard title="Notifications" class="gap-4">
        <div class="flex items-center justify-between gap-3">
          <span class="flex flex-col">
            <span class="text-[17px] font-bold">Portée préférée</span>
            <span class="text-sm text-ink-muted">Tout de suite, sur l’iPad et l’iPhone</span>
          </span>
          <USwitch
            v-model="draft.notify_preferred_immediately"
            aria-label="Notifier tout de suite une portée préférée"
          />
        </div>
        <div class="flex items-center justify-between gap-3">
          <span class="flex flex-col">
            <span class="text-[17px] font-bold">Récap du soir</span>
            <span class="text-sm text-ink-muted">Les acceptables et tes suivis, à {{ draft.digest_hour }} h</span>
          </span>
          <USwitch v-model="draft.notify_acceptable_in_digest" aria-label="Recevoir le récap du soir" />
        </div>
      </UiSectionCard>
    </div>
  </UiTabScreen>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { CoatColor, SearchProfileUpdate } from '~/types/api'
import type { CriteriaColorRow } from '~/types/Criteria'
import { computed, onMounted, ref } from 'vue'
import { COAT_COLOR_LABELS } from '~/constants/coatColorLabels'
import {
  COLOR_LEVEL_OPTIONS,
  LOF_OPTIONS,
  MAIN_COLOR_ROWS,
  NEARBY_REGIONS,
  OTHER_COLOR_ROWS,
  SEX_OPTIONS,
} from '~/constants/criteriaOptions'
import { ChoiceValues } from '~/utils/choiceValues'
import { FrenchText } from '~/utils/frenchText'

useHead({ title: 'Critères · La Bonne Truffe' })

const criteriaStore: ReturnType<typeof useCriteriaStore> = useCriteriaStore()

const areOtherColorsShown: Ref<boolean> = ref(false)

const draft: ComputedRef<SearchProfileUpdate | null> = computed((): SearchProfileUpdate | null => criteriaStore.draft)
const shownColorRows: ComputedRef<CriteriaColorRow[]> = computed((): CriteriaColorRow[] =>
  areOtherColorsShown.value ? [...MAIN_COLOR_ROWS, ...OTHER_COLOR_ROWS] : MAIN_COLOR_ROWS,
)
const saveLabel: ComputedRef<string> = computed((): string => {
  if (criteriaStore.isSaving) {
    return 'Enregistrement…'
  }
  return criteriaStore.hasUnsavedChanges ? 'Enregistrer' : 'À jour'
})
const departmentsSentence: ComputedRef<string> = computed((): string => {
  const codes: string[] = criteriaStore.draft?.department_codes ?? []
  if (codes.length === 0) {
    return 'Aucun département : choisis au moins une région.'
  }
  const countWord: string = FrenchText.spellOutCount(codes.length, 'masculine')
  const departments: string = FrenchText.pickForm(codes.length, 'département', 'départements')
  return `${countWord} ${departments}, du plus proche au plus loin : ${codes.join(' · ')}. Plus c’est proche, plus ça compte.`
})

/**
 * Set the level of a colour from its choice buttons.
 *
 * @param color - Canonical colour.
 * @param level - Emitted level.
 */
function setColorLevel(color: CoatColor, level: string): void {
  if (ChoiceValues.isColorLevel(level)) {
    criteriaStore.setColorLevel(color, level)
  }
}

/**
 * Set the LOF preference from its choice buttons.
 *
 * @param value - Emitted value.
 */
function setLofPreference(value: string): void {
  if (criteriaStore.draft !== null && ChoiceValues.isLofPreference(value)) {
    criteriaStore.draft.lof_preference = value
  }
}

/**
 * Set the sex preference from its choice buttons.
 *
 * @param value - Emitted value.
 */
function setSexPreference(value: string): void {
  if (criteriaStore.draft !== null && ChoiceValues.isSexPreference(value)) {
    criteriaStore.draft.sex_preference = value
  }
}

onMounted((): Promise<void> => criteriaStore.load())
</script>
