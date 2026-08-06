import type { Filters, Hero } from '../models'

export const hero: Hero = { id: 'Ada', name: 'Ada Hero', class: 'Ranger', tribe: 'Human', element: 'Fire', damageType: 'Physical', sex: 'f', mobility: 'ground', stats: { attack: 42 }, traits: [], passive: {}, progression: { rarity_name: 'Epic', base_stars: 3, max_stars: 8 }, availability: {}, acquisition: [], classification: 'collectible' }
export const filters: Filters = { classes: ['Ranger'], tribes: ['Human'], elements: ['Fire'], damageTypes: ['Physical'], rarities: ['Epic'], mobilities: ['ground'], acquisitions: ['Chest'], attributes: [{ value: 'Evade', label: 'Evade' }] }
export function response(value: unknown, ok = true, status = 200) { return Promise.resolve({ ok, status, json: () => Promise.resolve(value) } as Response) }
