import type { CoatColor } from '~/types/api'
import type { CockerCoat, CockerCoatPalette } from '~/types/CockerCoat'

export const COCKER_COAT_PALETTES: Record<CockerCoat, CockerCoatPalette> = {
  gold: {
    coat: '#E9B363',
    ear: '#CF8F3A',
    muzzle: '#F3CF95',
    tileClass: 'bg-gold-pastel',
    chipTextClass: 'text-gold-ink',
  },
  noir_et_feu: {
    coat: '#3A2F2A',
    ear: '#2B2420',
    muzzle: '#C98A4B',
    tileClass: 'bg-lilac-pastel',
    chipTextClass: 'text-ink-secondary',
  },
  noir: {
    coat: '#2F2724',
    ear: '#1E1816',
    muzzle: '#4A3C34',
    tileClass: 'bg-neutral-pastel',
    chipTextClass: 'text-ink-secondary',
  },
  marron: {
    coat: '#7B5033',
    ear: '#5E3A22',
    muzzle: '#A97A55',
    tileClass: 'bg-neutral-pastel',
    chipTextClass: 'text-ink-secondary',
  },
  bleu_rouan: {
    coat: '#8B8F99',
    ear: '#4E525C',
    muzzle: '#D9DBE0',
    tileClass: 'bg-neutral-pastel',
    chipTextClass: 'text-ink-secondary',
  },
  inconnue: {
    coat: '#6B5A50',
    ear: '#4A3C34',
    muzzle: '#B59A86',
    tileClass: 'bg-neutral-pastel',
    chipTextClass: 'text-ink-secondary',
  },
}

export const ILLUSTRATED_COATS: Partial<Record<CoatColor, CockerCoat>> = {
  gold: 'gold',
  noir_et_feu: 'noir_et_feu',
  noir: 'noir',
  marron: 'marron',
  bleu_rouan: 'bleu_rouan',
}
