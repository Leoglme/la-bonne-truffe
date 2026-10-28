const MASCULINE_NUMBER_WORDS: readonly string[] = [
  'Aucun',
  'Un',
  'Deux',
  'Trois',
  'Quatre',
  'Cinq',
  'Six',
  'Sept',
  'Huit',
  'Neuf',
  'Dix',
  'Onze',
  'Douze',
]

/** Small numbers written in words, as the mockup does (« Neuf départements »). */
export class FrenchNumbers {
  /**
   * A count before a masculine noun.
   *
   * @param count - The count.
   * @returns The word up to twelve, the digits beyond.
   */
  static masculine(count: number): string {
    return MASCULINE_NUMBER_WORDS[count] ?? String(count)
  }
}
