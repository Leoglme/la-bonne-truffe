import { describe, expect, it } from 'vitest'
import { FollowUpPresentation } from '../app/utils/followUpPresentation'

describe('FollowUpPresentation last contact', (): void => {
  it('says when the breeder was last contacted', (): void => {
    expect(FollowUpPresentation.buildLastContactLabel('2026-10-24T14:05:00')).toBe('Contacté le 24 oct.')
  })

  it('says nothing before the first contact', (): void => {
    expect(FollowUpPresentation.buildLastContactLabel(null)).toBeNull()
  })
})
