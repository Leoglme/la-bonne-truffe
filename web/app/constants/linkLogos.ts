import type { LinkLogoImage } from '~/types/UiLinkLogo'

export const LINK_LOGO_IMAGES: Record<LinkLogoImage, string> = {
  centrale_canine: '/images/link-logos/centrale-canine.svg',
  chiens_de_france: '/images/link-logos/chiens-de-france.svg',
  facebook: '/images/link-logos/facebook.png',
  instagram: '/images/link-logos/instagram.png',
  youtube: '/images/link-logos/youtube.png',
}

export const LINK_LOGOS_BY_DOMAIN: [string, LinkLogoImage][] = [
  ['centrale-canine.fr', 'centrale_canine'],
  ['chiens-de-france.com', 'chiens_de_france'],
  ['facebook.com', 'facebook'],
  ['fb.com', 'facebook'],
  ['instagram.com', 'instagram'],
  ['youtube.com', 'youtube'],
  ['youtu.be', 'youtube'],
]
