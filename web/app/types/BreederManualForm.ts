export type BreederManualForm = {
  display_name: string
  place: string
  link: string
  phone: string
  note: string
}

export type BreederManualTextFieldKey = 'display_name' | 'place' | 'link' | 'phone'

export type BreederManualTextField = {
  key: BreederManualTextFieldKey
  label: string
  type: 'text' | 'url' | 'tel'
  placeholder: string
  autocomplete: string
  inputMode: 'text' | 'url' | 'tel'
}
