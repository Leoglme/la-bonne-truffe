/** Elapsed time written the way the dashboard says it (« il y a 12 min »). */
export class RelativeTime {
  /**
   * How long ago a moment was.
   *
   * @param moment - The past moment.
   * @param now - Current time.
   * @returns « à l’instant », « il y a 12 min », « il y a 3 h » or « il y a 2 j ».
   */
  static since(moment: Date, now: Date): string {
    const elapsedMinutes: number = Math.max(0, Math.floor((now.getTime() - moment.getTime()) / 60_000))
    if (elapsedMinutes < 1) {
      return 'à l’instant'
    }
    if (elapsedMinutes < 60) {
      return `il y a ${elapsedMinutes} min`
    }
    const elapsedHours: number = Math.floor(elapsedMinutes / 60)
    if (elapsedHours < 24) {
      return `il y a ${elapsedHours} h`
    }
    return `il y a ${Math.floor(elapsedHours / 24)} j`
  }
}
