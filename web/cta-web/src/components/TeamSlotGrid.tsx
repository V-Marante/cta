import type { Hero } from '../models'
import type { TeamSlots } from '../teamPlannerState'
import { Portrait } from './Portrait'
import { ClassificationMarker } from './ClassificationMarker'

export function TeamSlotGrid({ slots, heroes, remove }: { slots: TeamSlots; heroes: Map<string, Hero>; remove: (index: number) => void }) {
  return <section className="team-slot-grid" aria-label="Selected heroes">{slots.map((id, index) => {
    const hero = id ? heroes.get(id) : undefined
    return <article key={index} className={`team-slot${hero ? ' filled' : ''}`} aria-label={`Team slot ${index + 1}${hero ? `: ${hero.name}` : ': empty'}`}>
      <span className="slot-number">{index + 1}</span>
      {!hero ? <span className="empty-slot">Empty</span> : <button type="button" className="selected-portrait" aria-label={`Remove ${hero.name} from team`} title={`Remove ${hero.name}`} onClick={() => remove(index)}><Portrait hero={hero} /><span>{hero.name}<ClassificationMarker hero={hero} /></span></button>}
    </article>
  })}</section>
}
