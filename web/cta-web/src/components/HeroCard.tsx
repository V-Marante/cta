import { humanize } from '../format'
import type { Hero } from '../models'
import { navigate } from '../navigation'
import { Portrait } from './Portrait'
import { ElementIcon, JobIcon } from './HeroSymbols'

export function HeroCard({ hero }: { hero: Hero }) {
  return <button className="card" onClick={() => navigate(`/heroes/${encodeURIComponent(hero.id)}`)}><Portrait hero={hero} /><div><h2>{hero.name}</h2><p className="hero-symbols"><JobIcon job={hero.class} /><i>–</i><ElementIcon element={hero.element} /></p><span>{hero.progression.rarity_name ?? 'Unknown rarity'} · {humanize(hero.mobility ?? 'Unknown')}</span></div></button>
}
