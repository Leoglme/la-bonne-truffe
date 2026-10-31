import { describe, expect, it } from 'vitest'
import { LitterDetailPresentation } from '../app/utils/litterDetailPresentation'

describe('LitterDetailPresentation.buildParentRatingLabel', (): void => {
  it('names the level of a father', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(1, 'sire')).toBe('Confirmé')
    expect(LitterDetailPresentation.buildParentRatingLabel(6, 'sire')).toBe('Élite A')
  })

  it('agrees the level with a mother', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(4, 'dam')).toBe('Recommandée')
  })

  it('keeps the number of a level outside the grid', (): void => {
    expect(LitterDetailPresentation.buildParentRatingLabel(7, 'dam')).toBe('Niveau 7 sur 6')
  })
})
