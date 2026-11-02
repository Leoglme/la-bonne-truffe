/** The filters and sorts chosen on the screens, kept on the device so that the next launch opens on them. */
export class SavedChoices {
  /**
   * Read a choice kept on the device; storage is missing on the server and refused in some private windows.
   *
   * @param storageKey - Where the choice is kept (« lbt-litter-sort »).
   * @param offeredValues - The values the screen offers now.
   * @param fallbackValue - The value when none is kept, or when the kept one is no longer offered.
   * @returns The kept value, else the fallback.
   */
  static read<TValue extends string>(storageKey: string, offeredValues: TValue[], fallbackValue: TValue): TValue {
    try {
      const keptValue: string | null = localStorage.getItem(storageKey)
      return offeredValues.find((value: TValue): boolean => value === keptValue) ?? fallbackValue
    } catch {
      return fallbackValue
    }
  }

  /**
   * Keep a choice on the device for the next launches; a refused storage keeps nothing.
   *
   * @param storageKey - Where the choice is kept.
   * @param value - The value chosen.
   */
  static keep(storageKey: string, value: string): void {
    try {
      localStorage.setItem(storageKey, value)
    } catch {
      return
    }
  }
}
