import { useState } from 'react'
import { API_URL } from '../api'
import type { Hero } from '../models'

export function Portrait({ hero, large = false }: { hero: Hero; large?: boolean }) {
  const [failed, setFailed] = useState(false)
  if (!hero.portraitUrl || failed) return <div className={`portrait placeholder ${large ? 'large' : ''}`} aria-label="Portrait unavailable">{hero.name}</div>
  return <img className={`portrait ${large ? 'large' : ''}`} src={`${API_URL}${hero.portraitUrl}`} alt={`${hero.name} portrait`} onError={() => setFailed(true)} />
}
