import type { HeroPassive } from '../models'
import { ElementIcon } from './HeroSymbols'

const elements = new Set(['Fire', 'Water', 'Earth', 'Light', 'Dark'])

export function FourthAbilityTarget({ passive }: { passive: HeroPassive }) {
  if (!passive.target) return <span className="ability-target unknown">Target unavailable</span>
  if (passive.target === 'All') return <span className="ability-target">All</span>
  if (elements.has(passive.target)) return <span className="ability-target" title={`Targets ${passive.target} heroes`}><ElementIcon element={passive.target} /></span>
  return <span className="ability-target">{passive.target}</span>
}
