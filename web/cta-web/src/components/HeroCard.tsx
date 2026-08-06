import { humanize } from '../format'
import type { Hero } from '../models'
import { navigate } from '../navigation'
import { Portrait } from './Portrait'

export function HeroCard({ hero }: { hero: Hero }) {
  return <button className="card" onClick={() => navigate(`/heroes/${encodeURIComponent(hero.id)}`)}><Portrait hero={hero} /><div><h2>{hero.name}</h2><p>{hero.class ?? 'Unknown job'} · {hero.element ?? 'Unknown element'}</p><span>{hero.classification === 'collectible' ? `${hero.progression.rarity_name ?? 'Unknown rarity'} · ${humanize(hero.mobility ?? 'Unknown')}` : humanize(hero.classification)}</span></div></button>
}
