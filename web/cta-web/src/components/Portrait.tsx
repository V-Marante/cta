import { useState } from 'react'
import { API_URL } from '../api'
import type { Hero } from '../models'

export function portraitUrl(path: string, apiBase = API_URL, assetBase = import.meta.env.VITE_ASSET_BASE_URL ?? '') {
  if (/^https?:\/\//.test(path)) return path
  const base = assetBase.trim().replace(/\/$/, '') || apiBase
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

export function Portrait({ hero, large = false }: { hero: Hero; large?: boolean }) {
  const [failed, setFailed] = useState(false)
  if (!hero.portraitUrl || failed) return <div className={`portrait placeholder ${large ? 'large' : ''}`} aria-label="Portrait unavailable">{hero.name}</div>
  return <img className={`portrait ${large ? 'large' : ''}`} src={portraitUrl(hero.portraitUrl)} alt={`${hero.name} portrait`} onError={() => setFailed(true)} />
}
