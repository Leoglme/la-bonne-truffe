import type { GeographicPoint } from '../app/types/Location'
import { describe, expect, it } from 'vitest'
import { CrowFliesDistance } from '../app/utils/crowFliesDistance'

const RENNES: GeographicPoint = { latitude: 48.1173, longitude: -1.6778 }
const SAINT_AUBIN_DU_CORMIER: GeographicPoint = { latitude: 48.26, longitude: -1.4 }

describe('CrowFliesDistance', (): void => {
  it('measures Rennes to Saint-Aubin-du-Cormier at about twenty-six kilometres', (): void => {
    const kilometers: number = CrowFliesDistance.kilometersBetween(RENNES, SAINT_AUBIN_DU_CORMIER)

    expect(kilometers).toBeGreaterThan(25)
    expect(kilometers).toBeLessThan(27)
    expect(CrowFliesDistance.kilometersBetween(SAINT_AUBIN_DU_CORMIER, RENNES)).toBeCloseTo(kilometers, 6)
  })

  it('measures nothing between a point and itself', (): void => {
    expect(CrowFliesDistance.kilometersBetween(RENNES, RENNES)).toBe(0)
  })

  it('writes the rounded kilometres, or less than one', (): void => {
    expect(CrowFliesDistance.buildLabel(25.6)).toBe('à 26 km')
    expect(CrowFliesDistance.buildLabel(0.3)).toBe('à moins d’un kilomètre')
  })
})
