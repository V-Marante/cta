import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { TeamPlannerPage } from '../components/TeamPlannerPage'
import type { Hero } from '../models'
import { TEAM_STORAGE_KEY } from '../teamPlannerState'
import { hero, response } from './fixtures'

const bea: Hero = { ...hero, id: 'Bea', name: 'Bea Hero', element: 'Water', class: 'Knight', mobility: 'flying', traits: [{ code: 'AntiStun', name: 'Anti-Stun' }, { code: 'Stunner', name: 'Stunner' }], passive: { code: 'BuffHP', name: 'Buff HP', description: 'Dark heroes: +20% HP', source_value: 20, target: 'Dark', semantics: { status: 'strongly_supported', meaning: 'team_stat_modifier', unit: 'percent', target_kind: 'hero_group' } } }
const page = { items: [hero, bea], total: 2, page: 1, pageSize: 250 }

beforeEach(() => { localStorage.clear(); vi.restoreAllMocks(); history.replaceState({}, '', '/team-planner') })

it('renders ten compact empty slots and a graceful missing-fourth-ability fallback', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response(page))
  render(<TeamPlannerPage />)
  expect(await screen.findAllByText('Empty')).toHaveLength(10)
  expect(screen.getByText('Fourth ability unavailable')).toBeInTheDocument()
  const beaCard = screen.getByRole('button', { name: 'Add Bea Hero to team' })
  expect(within(beaCard).getByLabelText('Water')).toBeInTheDocument()
  expect(within(beaCard).getByLabelText('Dark')).toBeInTheDocument()
  expect(within(beaCard).getByText('Anti-Stun')).toBeInTheDocument()
  expect(within(beaCard).getByText('Stunner')).toBeInTheDocument()
  expect(within(beaCard).getByText('Flying')).toBeInTheDocument()
  expect(screen.getByText('Team: 0 / 10 heroes · Add at least one hero')).toBeInTheDocument()
})

it('toggles a hero from either portrait list, clears, and updates summaries', async () => {
  const user = userEvent.setup()
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response(page))
  render(<TeamPlannerPage />)
  await user.click(await screen.findByRole('button', { name: 'Add Ada Hero to team' }))
  expect(screen.getByText('Team: 1 / 10 heroes · Valid')).toBeInTheDocument()
  const summary = screen.getByLabelText('Team summary')
  expect(within(summary).getByLabelText('Fire').parentElement).toHaveTextContent('1')
  expect(within(summary).getByText('Ranger').parentElement).toHaveTextContent('1')
  expect(screen.getAllByRole('button', { name: 'Remove Ada Hero from team' })).toHaveLength(2)
  await user.click(screen.getByTitle('Remove Ada Hero'))
  expect(screen.getByText('Team: 0 / 10 heroes · Add at least one hero')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Add Bea Hero to team' }))
  const selectedSummary = screen.getByLabelText('Team summary')
  expect(within(selectedSummary).getByText('Buff HP')).toBeInTheDocument()
  expect(within(selectedSummary).getAllByLabelText('Dark').length).toBeGreaterThan(0)
  await user.click(within(screen.getByLabelText('Available heroes')).getByRole('button', { name: 'Remove Bea Hero from team' }))
  expect(screen.getByText('Team: 0 / 10 heroes · Add at least one hero')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Add Bea Hero to team' }))
  await user.click(screen.getByRole('button', { name: 'Clear team' }))
  expect(screen.getByText('Team: 0 / 10 heroes · Add at least one hero')).toBeInTheDocument()
  expect(localStorage.getItem(TEAM_STORAGE_KEY)).toBeNull()
})

it('filters by search, element, and job and groups by job, element, or fourth ability', async () => {
  const user = userEvent.setup()
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response(page))
  render(<TeamPlannerPage />)
  await screen.findByRole('button', { name: 'Add Ada Hero to team' })
  expect(screen.getByRole('region', { name: 'Ranger heroes' })).toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('Group by'), 'element')
  expect(screen.getByRole('region', { name: 'Fire heroes' })).toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('Group by'), 'ability')
  expect(screen.getByRole('region', { name: 'Buff HP heroes' })).toBeInTheDocument()
  await user.type(screen.getByLabelText('Search heroes'), 'Bea')
  expect(screen.queryByRole('button', { name: 'Add Ada Hero to team' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Bea Hero to team' })).toBeInTheDocument()
  await user.clear(screen.getByLabelText('Search heroes'))
  await user.selectOptions(screen.getByLabelText('Element'), 'Fire')
  expect(screen.queryByRole('button', { name: 'Add Bea Hero to team' })).not.toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('Element'), '')
  await user.selectOptions(screen.getByLabelText('Job (Class)'), 'Knight')
  expect(screen.getByRole('button', { name: 'Add Bea Hero to team' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Add Ada Hero to team' })).not.toBeInTheDocument()
})

it('restores stored IDs after loading and safely ignores absent IDs', async () => {
  localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(['Bea', 'Gone']))
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response(page))
  render(<TeamPlannerPage />)
  expect(await screen.findByLabelText('Team slot 1: Bea Hero')).toBeInTheDocument()
  expect(screen.getByLabelText('Team slot 2: empty')).toBeInTheDocument()
})

it('shows API errors and retries with existing async-state behavior', async () => {
  const user = userEvent.setup()
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => response({}, false, 500)).mockImplementation(() => response(page))
  render(<TeamPlannerPage />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not load heroes')
  await user.click(screen.getByRole('button', { name: 'Try again' }))
  expect(await screen.findByRole('button', { name: 'Add Ada Hero to team' })).toBeInTheDocument()
  expect(fetch).toHaveBeenCalledTimes(2)
})
