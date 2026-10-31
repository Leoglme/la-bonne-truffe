export type PuppyArrivalPreparation = {
  key: string
  label: string
  description: string | null
}

export type PuppyArrivalChecklistSection = {
  title: string
  preparations: PuppyArrivalPreparation[]
}
