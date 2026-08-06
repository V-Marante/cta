import type { Hero, Skill } from './models'

export function humanize(value: string) { return value.replaceAll('_', ' ').replace(/([a-z])([A-Z])/g, '$1 $2') }
export function formatText(value: string | undefined, hero: Hero) { return (value ?? 'Description unavailable.').replaceAll('{element}', hero.element ?? 'element').replaceAll('{evade}', String(hero.stats.evade ?? '?')).replaceAll('*', '') }
export function skillMechanics(skill: Skill) { const values: string[] = []; for (const part of skill.components) { if (part.attributes.cooldown) values.push(`Cooldown ${part.attributes.cooldown}s`); if (part.attributes.splashRad) values.push(`AoE radius ${part.attributes.splashRad}`); if (part.attributes.count) values.push(`${part.attributes.count} projectiles`) } return [...new Set(values)] }
