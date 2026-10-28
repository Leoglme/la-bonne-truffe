import type { ComputedRef, Ref } from 'vue'
import type { CoatColor, ColorPreferenceLevel, Department, SearchProfile, SearchProfileUpdate } from '~/types/api'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { ProfilesService } from '~/services/profilesService'

/** Pinia store of the criteria screen: the active profile, its edited copy, and the departments. */
// Pinia ne fournit pas de type nommé pour un store : TypeScript l'élide, il est inécrivable.
// eslint-disable-next-line @typescript-eslint/typedef
export const useCriteriaStore = defineStore('criteria', () => {
  const savedProfile: Ref<SearchProfile | null> = ref(null)
  const draft: Ref<SearchProfileUpdate | null> = ref(null)
  const departments: Ref<Department[]> = ref([])
  const isSaving: Ref<boolean> = ref(false)
  const saveError: Ref<string | null> = ref(null)

  const hasUnsavedChanges: ComputedRef<boolean> = computed((): boolean => {
    if (savedProfile.value === null || draft.value === null) {
      return false
    }
    return JSON.stringify(toUpdate(savedProfile.value)) !== JSON.stringify(draft.value)
  })

  /**
   * Copy the editable fields of a profile.
   *
   * @param profile - Stored profile.
   * @returns Its criteria, detached from the stored object.
   */
  function toUpdate(profile: SearchProfile): SearchProfileUpdate {
    return {
      name: profile.name,
      is_active: profile.is_active,
      breed_ids: [...profile.breed_ids],
      department_codes: [...profile.department_codes],
      include_expected_litters: profile.include_expected_litters,
      sex_preference: profile.sex_preference,
      lof_preference: profile.lof_preference,
      color_preferences: { ...profile.color_preferences },
      price_max_cents: profile.price_max_cents ?? null,
      notify_preferred_immediately: profile.notify_preferred_immediately,
      notify_acceptable_in_digest: profile.notify_acceptable_in_digest,
      digest_hour: profile.digest_hour,
      notify_birth_of_followed: profile.notify_birth_of_followed,
    }
  }

  /**
   * Load the first profile of the user and the departments.
   */
  async function load(): Promise<void> {
    const [profiles, loadedDepartments]: [SearchProfile[], Department[]] = await Promise.all([
      ProfilesService.list(),
      ProfilesService.listDepartments(),
    ])
    departments.value = loadedDepartments
    savedProfile.value = profiles[0] ?? null
    draft.value = savedProfile.value ? toUpdate(savedProfile.value) : null
  }

  /**
   * Level of a colour in the edited criteria; a colour left out is ignored.
   *
   * @param color - Canonical colour.
   * @returns Its level.
   */
  function levelOf(color: CoatColor): ColorPreferenceLevel {
    return draft.value?.color_preferences[color] ?? 'ignored'
  }

  /**
   * Set the level of a colour.
   *
   * @param color - Canonical colour.
   * @param level - New level.
   */
  function setColorLevel(color: CoatColor, level: ColorPreferenceLevel): void {
    if (draft.value !== null) {
      draft.value.color_preferences = { ...draft.value.color_preferences, [color]: level }
    }
  }

  /**
   * Codes of the departments of a region.
   *
   * @param region - Region name.
   * @returns Its department codes.
   */
  function departmentCodesOf(region: string): string[] {
    return departments.value
      .filter((department: Department): boolean => department.region === region)
      .map((department: Department): string => department.code)
  }

  /**
   * Whether every department of a region is searched.
   *
   * @param region - Region name.
   * @returns True when the region is fully in the list.
   */
  function isRegionSelected(region: string): boolean {
    const codes: string[] = departmentCodesOf(region)
    return (
      codes.length > 0 && codes.every((code: string): boolean => draft.value?.department_codes.includes(code) ?? false)
    )
  }

  /**
   * Remove a region, or add it back: saved departments return to their place, new ones go at the end.
   *
   * @param region - Region name.
   */
  function toggleRegion(region: string): void {
    if (draft.value === null) {
      return
    }
    const regionCodes: string[] = departmentCodesOf(region)
    if (isRegionSelected(region)) {
      draft.value.department_codes = draft.value.department_codes.filter(
        (code: string): boolean => !regionCodes.includes(code),
      )
      return
    }
    const wantedCodes: Set<string> = new Set([...draft.value.department_codes, ...regionCodes])
    const savedCodes: string[] = savedProfile.value?.department_codes ?? []
    draft.value.department_codes = [
      ...savedCodes.filter((code: string): boolean => wantedCodes.has(code)),
      ...[...wantedCodes].filter((code: string): boolean => !savedCodes.includes(code)),
    ]
  }

  /**
   * Save the criteria; the API re-evaluates every litter.
   */
  async function save(): Promise<void> {
    if (savedProfile.value === null || draft.value === null) {
      return
    }
    isSaving.value = true
    saveError.value = null
    try {
      savedProfile.value = await ProfilesService.update(savedProfile.value.id, draft.value)
      draft.value = toUpdate(savedProfile.value)
    } catch (error: unknown) {
      saveError.value = error instanceof Error ? error.message : 'Enregistrement impossible'
    } finally {
      isSaving.value = false
    }
  }

  return {
    savedProfile,
    draft,
    departments,
    isSaving,
    saveError,
    hasUnsavedChanges,
    load,
    levelOf,
    setColorLevel,
    isRegionSelected,
    toggleRegion,
    save,
  }
})
