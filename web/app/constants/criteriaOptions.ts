import type { CockerCoat } from '~/constants/cockerCoatPalettes'
import type { CoatColor, ColorPreferenceLevel, LofPreference, SexPreference } from '~/types/api'
import type { UiSegmentedControlOption } from '~/types/UiSegmentedControl'

/** A colour row of the criteria screen: canonical colour, label, and the coat of its illustration. */
export type CriteriaColorRow = {
  color: CoatColor
  label: string
  coat: CockerCoat
}

/** The five colours shown first (design/mockup/Criteres.dc.html), then the others behind « Voir les… ». */
export const MAIN_COLOR_ROWS: readonly CriteriaColorRow[] = [
  { color: 'gold', label: 'Gold', coat: 'gold' },
  { color: 'noir_et_feu', label: 'Noir et feu', coat: 'noir_et_feu' },
  { color: 'noir', label: 'Noir', coat: 'noir' },
  { color: 'marron', label: 'Marron', coat: 'marron' },
  { color: 'bleu_rouan', label: 'Bleu rouan', coat: 'bleu_rouan' },
]

export const OTHER_COLOR_ROWS: readonly CriteriaColorRow[] = [
  { color: 'marron_et_feu', label: 'Marron et feu', coat: 'inconnue' },
  { color: 'orange_rouan', label: 'Orange rouan', coat: 'inconnue' },
  { color: 'marron_rouan', label: 'Marron rouan', coat: 'inconnue' },
  { color: 'tricolore', label: 'Tricolore', coat: 'inconnue' },
  { color: 'particolore', label: 'Particolore', coat: 'inconnue' },
  { color: 'zibeline', label: 'Zibeline', coat: 'inconnue' },
]

export const COLOR_LEVEL_OPTIONS: UiSegmentedControlOption[] = [
  { value: 'preferred', label: 'Préférée' },
  { value: 'acceptable', label: 'Acceptable' },
  { value: 'ignored', label: 'Ignorée' },
]

export const LOF_OPTIONS: UiSegmentedControlOption[] = [
  { value: 'required', label: 'Obligatoire' },
  { value: 'preferred', label: 'Préféré' },
  { value: 'any', label: 'Peu importe' },
]

export const SEX_OPTIONS: UiSegmentedControlOption[] = [
  { value: 'male', label: 'Mâle' },
  { value: 'female', label: 'Femelle' },
  { value: 'any', label: 'Peu importe' },
]

/** Regions offered as chips, the closest to Rennes first (design/mockup/Criteres.dc.html). */
export const NEARBY_REGIONS: readonly string[] = ['Bretagne', 'Pays de la Loire', 'Normandie', 'Centre-Val de Loire']

const COLOR_LEVELS: readonly ColorPreferenceLevel[] = ['preferred', 'acceptable', 'ignored']
const LOF_PREFERENCES: readonly LofPreference[] = ['required', 'preferred', 'any']
const SEX_PREFERENCES: readonly SexPreference[] = ['male', 'female', 'any']

/** Narrow the string a segmented control emits back to the typed values of the profile. */
export class CriteriaValues {
  /**
   * Whether a value is a colour level.
   *
   * @param value - Emitted value.
   * @returns True for « preferred », « acceptable » or « ignored ».
   */
  static isColorLevel(value: string): value is ColorPreferenceLevel {
    return (COLOR_LEVELS as readonly string[]).includes(value)
  }

  /**
   * Whether a value is a LOF preference.
   *
   * @param value - Emitted value.
   * @returns True for « required », « preferred » or « any ».
   */
  static isLofPreference(value: string): value is LofPreference {
    return (LOF_PREFERENCES as readonly string[]).includes(value)
  }

  /**
   * Whether a value is a sex preference.
   *
   * @param value - Emitted value.
   * @returns True for « male », « female » or « any ».
   */
  static isSexPreference(value: string): value is SexPreference {
    return (SEX_PREFERENCES as readonly string[]).includes(value)
  }
}
