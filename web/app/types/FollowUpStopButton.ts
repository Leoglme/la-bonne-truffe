export type FollowUpStopButtonProps = {
  label: string
  question: string
  consequence: string
  stopAction: () => Promise<void>
}
