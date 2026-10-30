import type { ColorPreferenceLevel, LofPreference, SexPreference } from '~/types/api'
import type { CriteriaColorRow, CriteriaHourOption } from '~/types/Criteria'
import type { UiChoiceButtonsOption } from '~/types/UiChoiceButtons'

export const MAIN_COLOR_ROWS: CriteriaColorRow[] = [
  { color: 'gold', coat: 'gold' },
  { color: 'noir_et_feu', coat: 'noir_et_feu' },
  { color: 'noir', coat: 'noir' },
  { color: 'marron', coat: 'marron' },
  { color: 'bleu_rouan', coat: 'bleu_rouan' },
]

export const OTHER_COLOR_ROWS: CriteriaColorRow[] = [
  { color: 'marron_et_feu', coat: 'inconnue' },
  { color: 'orange_rouan', coat: 'inconnue' },
  { color: 'marron_rouan', coat: 'inconnue' },
  { color: 'tricolore', coat: 'inconnue' },
  { color: 'particolore', coat: 'inconnue' },
  { color: 'zibeline', coat: 'inconnue' },
]

export const ALL_COLOR_ROWS: CriteriaColorRow[] = [...MAIN_COLOR_ROWS, ...OTHER_COLOR_ROWS]

export const COLOR_LEVEL_OPTIONS: UiChoiceButtonsOption[] = [
  { value: 'preferred', label: 'Préférée' },
  { value: 'acceptable', label: 'Acceptable' },
  { value: 'ignored', label: 'Ignorée' },
]

export const LOF_OPTIONS: UiChoiceButtonsOption[] = [
  { value: 'required', label: 'Obligatoire' },
  { value: 'preferred', label: 'Préféré' },
  { value: 'any', label: 'Peu importe' },
]

export const SEX_OPTIONS: UiChoiceButtonsOption[] = [
  { value: 'male', label: 'Mâle' },
  { value: 'female', label: 'Femelle' },
  { value: 'any', label: 'Peu importe' },
]

/** Regions offered as chips, the closest to Rennes first. */
export const NEARBY_REGIONS: string[] = ['Bretagne', 'Pays de la Loire', 'Normandie', 'Centre-Val de Loire']

export const COLOR_LEVELS: ColorPreferenceLevel[] = ['preferred', 'acceptable', 'ignored']
export const LOF_PREFERENCES: LofPreference[] = ['required', 'preferred', 'any']
export const SEX_PREFERENCES: SexPreference[] = ['male', 'female', 'any']

/** Hours the evening digest can be sent at, in French time. */
export const DIGEST_HOUR_OPTIONS: CriteriaHourOption[] = [17, 18, 19, 20, 21, 22, 23].map(
  (hour: number): CriteriaHourOption => ({ label: `${hour} h`, value: hour }),
)
