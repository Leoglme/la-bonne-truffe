import type { PuppyArrivalChecklistSection, PuppyArrivalPreparation } from '~/types/PuppyArrival'

export const PUPPY_ARRIVAL_CHECKLIST: PuppyArrivalChecklistSection[] = [
  {
    title: 'À la maison',
    preparations: [
      { key: 'basket', label: 'Panier et couverture', description: null },
      { key: 'bowls', label: 'Gamelles', description: null },
      { key: 'leash', label: 'Laisse, collier et harnais', description: null },
      { key: 'chew_toys', label: 'Jouets à mâcher', description: null },
      { key: 'stair_gate', label: 'Barrière pour l’escalier', description: null },
      {
        key: 'breeder_food',
        label: 'Les croquettes de l’éleveur',
        description: 'La même marque les premières semaines',
      },
    ],
  },
  {
    title: 'Chez le vétérinaire',
    preparations: [
      { key: 'vet_visit', label: 'Premier rendez-vous', description: 'Dans la semaine de son arrivée' },
      { key: 'insurance', label: 'Assurance santé', description: null },
    ],
  },
  {
    title: 'Le jour J, à récupérer',
    preparations: [
      { key: 'sale_contract', label: 'Contrat de vente', description: null },
      { key: 'lof_certificate', label: 'Certificat de naissance LOF', description: null },
      { key: 'health_booklet', label: 'Carnet de santé et puce', description: null },
      { key: 'icad_transfer', label: 'Attestation de cession i-CAD', description: null },
    ],
  },
]

export const PUPPY_ARRIVAL_CHECKLIST_KEYS: string[] = PUPPY_ARRIVAL_CHECKLIST.flatMap(
  (section: PuppyArrivalChecklistSection): string[] =>
    section.preparations.map((preparation: PuppyArrivalPreparation): string => preparation.key),
)
