import type { LitterColor, LitterDetail } from '~/types/api'
import type { FrenchGender } from '~/types/FrenchText'
import type { GoldGenotype, GoldGenotypeFacts, GoldPuppyOddsSummary } from '~/types/GoldGenetics'
import {
  GOLD_GENOTYPE_LABELS,
  GOLD_ONLY_TRANSMISSION_LABELS,
  PARENTS_GENOTYPE_SOURCE_LABEL,
  TESTED_GENOTYPE_SOURCE_LABEL,
} from '~/constants/goldGenetics'
import { FrenchText } from '~/utils/frenchText'

const GOLD_GENOTYPE: GoldGenotype = 'e/e'
const CARRIER_GENOTYPE: GoldGenotype = 'E/e'
const TESTED_GENOTYPES: GoldGenotype[] = ['e/e', 'E/e', 'E/E']
const LARGEST_FRACTION_DENOMINATOR: number = 16
const HIGHEST_WRITTEN_PERCENT: number = 99

/** How the screens word the gold of the E locus: what a dog carries of it, and the odds of gold puppies. */
export class GoldGeneticsPresentation {
  /**
   * Word what a dog carries of the gold, for its line among the dogs of a breeding.
   *
   * @param facts - Its tested genotype, and whether its parents tell that it carries the gold.
   * @param gender - Its sex, as French agrees with it.
   * @returns « testée gold (e/e) », « porteur du gold (E/e), d’après ses parents », or null while unknown.
   */
  static buildGenotypeLabel(facts: GoldGenotypeFacts, gender: FrenchGender): string | null {
    const testedGenotype: GoldGenotype | null = this.readTestedGenotype(facts)
    if (testedGenotype !== null) {
      return GOLD_GENOTYPE_LABELS[testedGenotype][gender]
    }
    if (facts.carries_gold_by_parents) {
      return `${GOLD_GENOTYPE_LABELS[CARRIER_GENOTYPE][gender]}, ${PARENTS_GENOTYPE_SOURCE_LABEL}`
    }
    return null
  }

  /**
   * Word what a parent of a litter carries of the gold, with what it gives its puppies or how it is known.
   *
   * @param facts - Its tested genotype, and whether its parents tell that it carries the gold.
   * @param gender - Its sex, as French agrees with it.
   * @returns « testé gold (e/e) : il ne transmet que le gold », « porteuse du gold (E/e), d’après son test ADN »,
   *   or null while unknown.
   */
  static buildGenotypeExplanation(facts: GoldGenotypeFacts, gender: FrenchGender): string | null {
    const testedGenotype: GoldGenotype | null = this.readTestedGenotype(facts)
    if (testedGenotype === GOLD_GENOTYPE) {
      return `${GOLD_GENOTYPE_LABELS[GOLD_GENOTYPE][gender]} : ${GOLD_ONLY_TRANSMISSION_LABELS[gender]}`
    }
    if (testedGenotype !== null) {
      return `${GOLD_GENOTYPE_LABELS[testedGenotype][gender]}, ${TESTED_GENOTYPE_SOURCE_LABEL}`
    }
    return this.buildGenotypeLabel(facts, gender)
  }

  /**
   * Tell whether the parents make every puppy of a litter gold.
   *
   * @param odds - Share of gold puppies the parents give, null while unknown.
   * @returns True when both parents only give the gold.
   */
  static isEveryPuppyGold(odds: number | null): boolean {
    return odds !== null && odds >= 1
  }

  /**
   * Word the odds of gold puppies in the row of a litter, when only some of its puppies can be gold.
   *
   * @param odds - Share of gold puppies the parents give, null while unknown.
   * @returns « Gold possible : un chiot sur deux », or null when every puppy is gold or nothing is known.
   */
  static buildPuppyOddsLine(odds: number | null): string | null {
    if (odds === null || odds <= 0 || odds >= 1) {
      return null
    }
    return `Gold possible : un chiot sur ${this.spellOutOddsDenominator(odds)}`
  }

  /**
   * Word the odds of gold puppies of a litter: the figure of its circle and the sentence beside it.
   *
   * @param litter - The litter.
   * @returns The odds of each puppy, why, and how often one gold at least is born among its puppies; « Aucun gold » and
   *   the reason when the parents rule it out; null while the genotypes of the parents tell nothing.
   */
  static buildPuppyOddsSummary(litter: LitterDetail): GoldPuppyOddsSummary | null {
    const odds: number | null = litter.gold_puppy_odds ?? null
    if (odds === null || odds <= 0) {
      return this.buildRuledOutSummary(litter)
    }
    if (this.isEveryPuppyGold(odds)) {
      return {
        figure: 'Tous',
        figureCaption: 'gold',
        explanation: 'Le père et la mère sont gold : tous les chiots seront gold.',
        isGoldRuledOut: false,
      }
    }
    const oddsDenominator: number = Math.round(1 / odds)
    const parentsClause: string | null = this.buildParentsClause(litter)
    const chanceClause: string = `une chance sur ${this.spellOutOddsDenominator(odds)} d’être gold.`
    const sentences: string[] = [
      parentsClause === null ? `Chaque chiot a ${chanceClause}` : `${parentsClause} : chaque chiot a ${chanceClause}`,
    ]
    const atLeastOneGoldSentence: string | null = this.buildAtLeastOneGoldSentence(litter, oddsDenominator)
    if (atLeastOneGoldSentence !== null) {
      sentences.push(atLeastOneGoldSentence)
    }
    return {
      figure: `1 sur ${oddsDenominator}`,
      figureCaption: 'par chiot',
      explanation: sentences.join(' '),
      isGoldRuledOut: false,
    }
  }

  /**
   * Word why no puppy of a litter will be gold, when its parents rule the gold out and no source announces it.
   *
   * @param litter - The litter.
   * @returns « Aucun gold » and the reason the parents give, or null when nothing rules the gold out.
   */
  private static buildRuledOutSummary(litter: LitterDetail): GoldPuppyOddsSummary | null {
    const reason: string | null = litter.gold_exclusion_reason ?? null
    const isGoldAnnounced: boolean = litter.colors.some(
      (reading: LitterColor): boolean => reading.color === 'gold' && reading.confidence !== 'ambiguous',
    )
    if (reason === null || isGoldAnnounced) {
      return null
    }
    return { figure: 'Aucun', figureCaption: 'gold', explanation: reason, isGoldRuledOut: true }
  }

  /**
   * Tell which parent gives the gold to every puppy and which one carries it, from their genotypes.
   *
   * @param litter - The litter.
   * @returns « Le père ne transmet que le gold et la mère le porte », or null when the genotypes are not both known.
   */
  private static buildParentsClause(litter: LitterDetail): string | null {
    const sireGenotype: GoldGenotype | null = litter.sire === null ? null : this.resolveGenotype(litter.sire)
    const damGenotype: GoldGenotype | null = litter.dam === null ? null : this.resolveGenotype(litter.dam)
    if (sireGenotype === CARRIER_GENOTYPE && damGenotype === CARRIER_GENOTYPE) {
      return 'Le père et la mère portent le gold sans être gold'
    }
    if (sireGenotype === GOLD_GENOTYPE && damGenotype === CARRIER_GENOTYPE) {
      return 'Le père ne transmet que le gold et la mère le porte'
    }
    if (damGenotype === GOLD_GENOTYPE && sireGenotype === CARRIER_GENOTYPE) {
      return 'La mère ne transmet que le gold et le père le porte'
    }
    return null
  }

  /**
   * Say how often one gold puppy at least is born among the puppies of a litter.
   *
   * @param litter - The litter, born.
   * @param oddsDenominator - 2 for one gold puppy in two, 4 for one in four.
   * @returns « Au moins un gold sur les trois, 7 fois sur 8. », or null before the birth or for a single puppy.
   */
  private static buildAtLeastOneGoldSentence(litter: LitterDetail, oddsDenominator: number): string | null {
    if (litter.kind === 'litter_expected' || litter.male_count === null || litter.female_count === null) {
      return null
    }
    const puppiesCount: number = litter.male_count + litter.female_count
    if (puppiesCount < 2) {
      return null
    }
    const outcomesCount: number = oddsDenominator ** puppiesCount
    const outcomesWithoutGoldCount: number = (oddsDenominator - 1) ** puppiesCount
    const frequency: string =
      outcomesCount <= LARGEST_FRACTION_DENOMINATOR
        ? `${outcomesCount - outcomesWithoutGoldCount} fois sur ${outcomesCount}`
        : `${Math.min(HIGHEST_WRITTEN_PERCENT, Math.round((1 - outcomesWithoutGoldCount / outcomesCount) * 100))} fois sur 100`
    const puppiesWord: string = FrenchText.spellOutCount(puppiesCount, 'masculine').toLowerCase()
    return `Au moins un gold sur les ${puppiesWord}, ${frequency}.`
  }

  /**
   * The genotype of a parent as the API infers it: tested, else e/e for a gold coat, else E/e from a gold parent.
   *
   * @param facts - Its coat, its tested genotype, and whether its parents tell that it carries the gold.
   * @returns « e/e », « E/e », « E/E », or null while unknown.
   */
  private static resolveGenotype(facts: GoldGenotypeFacts): GoldGenotype | null {
    const testedGenotype: GoldGenotype | null = this.readTestedGenotype(facts)
    if (testedGenotype !== null) {
      return testedGenotype
    }
    if (facts.color === 'gold') {
      return GOLD_GENOTYPE
    }
    return facts.carries_gold_by_parents ? CARRIER_GENOTYPE : null
  }

  /**
   * Read the genotype of the E locus test of a dog.
   *
   * @param facts - What is known of its colour.
   * @returns « e/e », « E/e » or « E/E », or null without a test.
   */
  private static readTestedGenotype(facts: GoldGenotypeFacts): GoldGenotype | null {
    const eLocus: string | null = facts.e_locus ?? null
    return TESTED_GENOTYPES.find((genotype: GoldGenotype): boolean => genotype === eLocus) ?? null
  }

  /**
   * Spell out the « deux » of « un chiot sur deux ».
   *
   * @param odds - Share of gold puppies, 0.5 or 0.25.
   * @returns « deux », « quatre ».
   */
  private static spellOutOddsDenominator(odds: number): string {
    return FrenchText.spellOutCount(Math.round(1 / odds), 'feminine').toLowerCase()
  }
}
