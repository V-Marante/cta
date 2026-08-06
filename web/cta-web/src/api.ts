import type { Filters, HeroDetailModel, HeroPage, HeroQuery } from './models'

// Development uses Vite's same-origin proxy. Besides simplifying API calls, this
// keeps portrait pixels readable by the tier-list export canvas.
export function normalizeBaseUrl(value: string | undefined, production = import.meta.env.PROD): string {
  const normalized = value?.trim().replace(/\/$/, '') ?? ''
  if (production && !normalized) throw new Error('VITE_API_URL is required for production builds')
  return normalized
}

export const API_URL = normalizeBaseUrl(import.meta.env.VITE_API_URL)

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { signal })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  return response.json() as Promise<T>
}

export function getFilters(signal?: AbortSignal) { return request<Filters>('/api/heroes/filters', signal) }
export function getHero(id: string, signal?: AbortSignal) { return request<HeroDetailModel>(`/api/heroes/${encodeURIComponent(id)}`, signal) }
export function getHeroes(query: HeroQuery, signal?: AbortSignal) {
  const parameters = new URLSearchParams({ pageSize: '250' })
  if (query.search) parameters.set('search', query.search)
  if (query.heroClass) parameters.set('class', query.heroClass)
  if (query.element) parameters.set('element', query.element)
  if (query.rarity) parameters.set('rarity', query.rarity)
  if (query.mobility) parameters.set('mobility', query.mobility)
  if (query.acquisition) parameters.set('acquisition', query.acquisition)
  if (query.attribute) parameters.set('attribute', query.attribute)
  return request<HeroPage>(`/api/heroes?${parameters}`, signal)
}
