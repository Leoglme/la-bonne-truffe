export type LinkLogoImage = 'centrale_canine' | 'chiens_de_france' | 'facebook' | 'instagram' | 'youtube'

export type LinkLogo = LinkLogoImage | 'website'

export type UiLinkLogoProps = {
  logo: LinkLogo
}
