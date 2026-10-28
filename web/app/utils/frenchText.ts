import type { FrenchGender } from '~/types/FrenchText'
import { FRENCH_NUMBER_WORDS } from '~/constants/frenchNumberWords'

const FRENCH_PLURAL_RULES: Intl.PluralRules = new Intl.PluralRules('fr-FR')

/** French words that follow a count: the singular or plural form, and small numbers spelled out. */
export class FrenchText {
  /**
   * Pick the form a word takes after a count: French keeps the singular for 0 and 1.
   *
   * @param count - The count.
   * @param singularForm - « portée vue ».
   * @param pluralForm - « portées vues ».
   * @returns The form that agrees with the count.
   */
  static pickForm(count: number, singularForm: string, pluralForm: string): string {
    return FRENCH_PLURAL_RULES.select(count) === 'one' ? singularForm : pluralForm
  }

  /**
   * Spell out a count up to twelve, before a noun of the given gender.
   *
   * @param count - The count.
   * @param gender - Gender of the noun that follows.
   * @returns « Neuf », « Une », « Aucun », or the digits beyond twelve.
   */
  static spellOutCount(count: number, gender: FrenchGender): string {
    return FRENCH_NUMBER_WORDS[gender][count] ?? String(count)
  }
}
