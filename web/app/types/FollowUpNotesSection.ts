/** A dated note of a follow, as the API returns it for a litter or a breeder. */
export type FollowUpNoteLine = {
  id: number
  created_at: string
  text: string
}

export type FollowUpNotesSectionProps = {
  notes: FollowUpNoteLine[]
  placeholder: string
  addNote: (text: string) => Promise<void>
  removeNote: (noteId: number) => Promise<void>
}
