import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { TierListMaker, tierColors } from '../components/TierListMaker'
import { hero, response } from './fixtures'

const exportPng = vi.hoisted(() => vi.fn((..._args: unknown[]) => Promise.resolve()))
vi.mock('../tierListPng', () => ({ exportTierListPng: exportPng }))

afterEach(() => { vi.restoreAllMocks(); exportPng.mockClear() })

function loadHeroes() {
  const heroes = [{ ...hero, portraitUrl: '/portraits/Ada.png' }, { ...hero, id: 'Bea', name: 'Bea Hero', portraitUrl: '/portraits/Bea.png' }]
  return vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ items: heroes, total: 2, page: 1, pageSize: 250 }))
}

describe('TierListMaker', () => {
  it('starts with only S and renders every hero in the sticky unranked pool', async () => {
    loadHeroes(); render(<TierListMaker />)
    expect(await screen.findByRole('button', { name: 'Select Ada Hero' })).toContainElement(screen.getByAltText('Ada Hero portrait'))
    expect(screen.getByRole('button', { name: 'Select Ada Hero' })).toHaveTextContent('Ada Hero')
    expect(screen.getByRole('button', { name: 'Select Bea Hero' })).toBeInTheDocument()
    expect(screen.getAllByLabelText('Tier name')).toHaveLength(1)
    expect(screen.getByRole('region', { name: 'S tier' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: /Unranked/ })).toHaveClass('unranked')
  })

  it('places a selected hero and persists its title and renamed tiers locally', async () => {
    loadHeroes(); const view = render(<TierListMaker />); await screen.findByRole('button', { name: 'Select Ada Hero' })
    fireEvent.change(screen.getByLabelText('Tier list title'), { target: { value: 'My Arena Picks' } })
    fireEvent.change(screen.getByLabelText('Tier name'), { target: { value: 'Excellent' } })
    fireEvent.click(screen.getByRole('button', { name: 'Select Ada Hero' }))
    fireEvent.click(within(screen.getByRole('region', { name: 'Excellent tier' })).getByRole('button', { name: 'Place here' }))
    await waitFor(() => expect(JSON.parse(localStorage.getItem('cta.hero-tier-list.v2')!).tiers[0]).toEqual(expect.objectContaining({ name: 'Excellent' })))
    view.unmount(); render(<TierListMaker />)
    const restored = await screen.findByRole('region', { name: 'Excellent tier' })
    expect(screen.getByLabelText('Tier list title')).toHaveValue('My Arena Picks')
    expect(within(restored).getByRole('button', { name: 'Select Ada Hero' })).toBeInTheDocument()
  })

  it('uses unique deterministic colors and returns deleted-tier heroes to unranked', async () => {
    expect(tierColors).toHaveLength(15); expect(new Set(tierColors).size).toBe(15)
    loadHeroes(); render(<TierListMaker />); await screen.findByRole('button', { name: 'Select Ada Hero' })
    expect(screen.getByRole('region', { name: 'S tier' }).querySelector('.tier-label')).toHaveStyle({ backgroundColor: '#d95f59' })
    fireEvent.click(screen.getByRole('button', { name: 'Add tier' }))
    const added = screen.getByRole('region', { name: 'Tier 2 tier' })
    expect(added.querySelector('.tier-label')).toHaveStyle({ backgroundColor: '#4f86c6' })
    expect(screen.queryByRole('textbox', { name: /color/i })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Select Ada Hero' })); fireEvent.click(within(added).getByRole('button', { name: 'Place here' }))
    fireEvent.click(within(added).getByRole('button', { name: 'Delete Tier 2 tier' }))
    expect(within(screen.getByRole('region', { name: /Unranked/ })).getByRole('button', { name: 'Select Ada Hero' })).toBeInTheDocument()
  })

  it('moves created tiers and reapplies colors by position', async () => {
    loadHeroes(); render(<TierListMaker />); await screen.findByRole('button', { name: 'Select Ada Hero' })
    fireEvent.click(screen.getByRole('button', { name: 'Add tier' }))
    fireEvent.click(screen.getByRole('button', { name: 'Move Tier 2 tier up' }))
    expect(screen.getAllByLabelText('Tier name').map(input => (input as HTMLInputElement).value)).toEqual(['Tier 2', 'S'])
    expect(screen.getByRole('region', { name: 'Tier 2 tier' }).querySelector('.tier-label')).toHaveStyle({ backgroundColor: '#d95f59' })
    expect(screen.getByRole('region', { name: 'S tier' }).querySelector('.tier-label')).toHaveStyle({ backgroundColor: '#4f86c6' })
  })

  it('randomly fills the current tiers in development', async () => {
    loadHeroes(); render(<TierListMaker />); await screen.findByRole('button', { name: 'Select Ada Hero' })
    fireEvent.click(screen.getByRole('button', { name: 'Random fill' }))
    expect(within(screen.getByRole('region', { name: 'S tier' })).getAllByRole('button', { name: /Select .* Hero/ })).toHaveLength(2)
    expect(within(screen.getByRole('region', { name: /Unranked/ })).queryAllByRole('button', { name: /Select .* Hero/ })).toHaveLength(0)
  })

  it('exports the current ranked list as PNG', async () => {
    loadHeroes(); render(<TierListMaker />); await screen.findByRole('button', { name: 'Select Ada Hero' })
    fireEvent.change(screen.getByLabelText('Tier list title'), { target: { value: 'My Best Heroes' } })
    fireEvent.click(screen.getByRole('button', { name: 'Select Ada Hero' })); fireEvent.click(screen.getByRole('button', { name: 'Place here' }))
    fireEvent.click(screen.getByRole('button', { name: 'Export PNG' }))
    await waitFor(() => expect(exportPng).toHaveBeenCalledOnce())
    expect(exportPng.mock.calls[0][0]).toBe('My Best Heroes')
    expect(exportPng.mock.calls[0][3]).toEqual({ Ada: 's' })
  })
})
