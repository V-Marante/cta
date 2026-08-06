import type { HeroPassive } from './models'

export function fourthAbilityName(passive: HeroPassive) {
  return passive.name ?? passive.code ?? 'Fourth ability unavailable'
}
