export interface CategoryOption {
  id: number
  emoji: string
  name: string
  voice: string
}

export const CATEGORIES: CategoryOption[] = [
  { id: 1, emoji: '🧠', name: '심리학', voice: 'SunHi' },
  { id: 2, emoji: '📜', name: '역사 충격', voice: 'InJoon' },
  { id: 3, emoji: '🔬', name: '뇌과학', voice: 'SunHi' },
  { id: 4, emoji: '🏯', name: '한국사 X파일', voice: 'Hyunsu' },
  { id: 5, emoji: '💰', name: '돈의 심리학', voice: 'InJoon' },
  { id: 6, emoji: '📊', name: '경제 다큐', voice: 'InJoon' },
]
