import type { Hero } from '../models'
import { fourthAbilityName } from '../fourthAbility'
import { FourthAbilityTarget } from './FourthAbilityTarget'
import { ElementIcon } from './HeroSymbols'
import { Portrait } from './Portrait'
import { ClassificationMarker } from './ClassificationMarker'

export function PlannerHeroCard({ hero, selected, toggle }: { hero: Hero; selected: boolean; toggle: () => void }) {
  return <button type="button" className={`planner-hero-card${selected ? ' selected' : ''}`} aria-pressed={selected} aria-label={`${selected ? 'Remove' : 'Add'} ${hero.name} ${selected ? 'from' : 'to'} team`} title={`${hero.name} · ${hero.element ?? 'Unknown element'} · ${hero.class ?? 'Unknown job'}`} onClick={toggle}>
    <Portrait hero={hero} />
    <span className="planner-hero-name">{hero.name}<ClassificationMarker hero={hero} /></span>
    <span className="planner-hero-meta"><ElementIcon element={hero.element} /><span>{hero.class ?? 'Unknown job'}</span></span>
    <span className="planner-hero-ability"><span>{fourthAbilityName(hero.passive)}</span><FourthAbilityTarget passive={hero.passive} /></span>
    <span className="planner-hero-traits">{plannerTraits(hero).map(trait => <i key={trait}>{trait}</i>)}</span>
  </button>
}

function plannerTraits(hero: Hero) {
  const traits = hero.traits.map(trait => trait.name)
  if (hero.mobility === 'flying' && !traits.some(trait => trait.toLowerCase() === 'flying')) traits.push('Flying')
  return traits
}
