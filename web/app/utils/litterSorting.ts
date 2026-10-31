import type { LitterCard } from '~/types/api'
import type { LitterSortKey } from '~/types/Litter'
import type { DevicePosition } from '~/types/Location'
import { CrowFliesDistance } from '~/utils/crowFliesDistance'
import { FrenchDate } from '~/utils/frenchDate'

/** Orders the cards of the home the way the sort drawer asks; a card without the fact sorted on goes last. */
export class LitterSorting {
  /**
   * Sort the cards. The order the API gives (by score) is kept between equal cards.
   *
   * @param cards - Cards in the order of the API.
   * @param sortKey - The sort chosen.
   * @param position - Position of the device, needed to sort by distance.
   * @returns A new array, sorted.
   */
  static sort(cards: LitterCard[], sortKey: LitterSortKey, position: DevicePosition | null): LitterCard[] {
    if (sortKey === 'score') {
      return [...cards]
    }
    const isDescending: boolean = sortKey === 'departure_latest'
    return [...cards].sort((first: LitterCard, second: LitterCard): number => {
      const firstMeasure: number | null = this.measureOf(first, sortKey, position)
      const secondMeasure: number | null = this.measureOf(second, sortKey, position)
      if (firstMeasure === null) {
        return secondMeasure === null ? 0 : 1
      }
      if (secondMeasure === null) {
        return -1
      }
      return isDescending ? secondMeasure - firstMeasure : firstMeasure - secondMeasure
    })
  }

  /**
   * The number a card is sorted on.
   *
   * @param card - The card.
   * @param sortKey - The sort chosen.
   * @param position - Position of the device.
   * @returns Kilometres, cents or the departure day as a timestamp; null while unknown.
   */
  private static measureOf(card: LitterCard, sortKey: LitterSortKey, position: DevicePosition | null): number | null {
    if (sortKey === 'distance') {
      if (position === null || card.breeder_latitude === null || card.breeder_longitude === null) {
        return null
      }
      return CrowFliesDistance.kilometersBetween(position, {
        latitude: card.breeder_latitude,
        longitude: card.breeder_longitude,
      })
    }
    if (sortKey === 'price') {
      return card.price_cents
    }
    return card.available_from === null ? null : FrenchDate.parseDay(card.available_from).getTime()
  }
}
