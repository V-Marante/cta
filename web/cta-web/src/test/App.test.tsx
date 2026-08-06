import { render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { App } from '../App'
import { hero, response } from './fixtures'

afterEach(() => vi.restoreAllMocks())

it('renders a navigated hero detail', async () => {
  history.replaceState({}, '', '/heroes/Ada')
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ hero, skills: [{ id: 'Arrow', name: 'Arrow', description: 'Chance {value}.', unresolvedPlaceholders: ['value'], components: [{ kind: 'spec', attributes: { cooldown: '0', effectChance: '0.20' }, attribute_semantics: { cooldown: { raw_value: '0', value: 0, display_value: 0, status: 'strongly_supported', meaning: 'duration', unit: 'seconds', source_attribute: 'cooldown' }, effectChance: { raw_value: '0.20', value: 0.2, display_value: 20, status: 'strongly_supported', meaning: 'probability', unit: 'percent', source_attribute: 'effectChance' } } }] }] }))
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Ada Hero', level: 1 })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Ada Hero', level: 1 })).toHaveFocus()
  expect(screen.getByRole('heading', { name: 'Arrow' })).toBeInTheDocument()
  expect(screen.getByText('Raw BaseStars')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Explicit medal acquisition' })).toBeInTheDocument()
  expect(screen.getByText(/Test Chest/)).toBeInTheDocument()
  expect(screen.getByText('Legacy availability indicators')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Base combat values' })).toBeInTheDocument()
  expect(screen.getByText('ATK')).toBeInTheDocument()
  expect(screen.getByText('0%')).toBeInTheDocument()
  expect(screen.getByText('Unresolved source scores')).toBeInTheDocument()
  expect(screen.getByText('Chance [unresolved: value].')).toBeInTheDocument()
  expect(screen.getByText('Unresolved source placeholders: value')).toBeInTheDocument()
  expect(screen.getByText('Cooldown 0s')).toBeInTheDocument()
  expect(screen.getByText('Effect chance 20%')).toBeInTheDocument()
})

it('routes directly to the tier list maker', async () => {
  history.replaceState({}, '', '/tier-list')
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ items: [hero], total: 1, page: 1, pageSize: 250 }))
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Tier List Maker', level: 1 })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Tier List Maker', level: 1 })).toHaveFocus()
})
