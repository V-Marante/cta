import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HeroRoster } from '../components/HeroRoster'
import { filters, hero, response } from './fixtures'

afterEach(() => vi.restoreAllMocks())

function mockFetch(items = [hero]) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(url => String(url).includes('/filters') ? response(filters) : response({ items, total: items.length, page: 1, pageSize: 250 }))
}

describe('HeroRoster', () => {
  it('shows loading and then cards', async () => {
    mockFetch(); render(<HeroRoster />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading heroes')
    expect(await screen.findByRole('heading', { name: 'Ada Hero' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Hero filters' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Search heroes' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Hero roster' })).toBeInTheDocument()
  })
  it('shows empty state', async () => {
    mockFetch([]); render(<HeroRoster />)
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('No heroes match those filters.'))
  })
  it('shows failed request and retries', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch'); fetch.mockImplementationOnce(() => response(filters)).mockRejectedValueOnce(new Error('offline')).mockImplementation(url => String(url).includes('/filters') ? response(filters) : response({ items: [hero], total: 1, page: 1, pageSize: 250 }))
    render(<HeroRoster />); expect(await screen.findByRole('alert')).toHaveTextContent('Could not load heroes')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' })); expect(await screen.findByRole('heading', { name: 'Ada Hero' })).toBeInTheDocument()
  })
  it('changing a filter updates the request', async () => {
    const fetch = mockFetch(); render(<HeroRoster />); await screen.findByRole('heading', { name: 'Ada Hero' })
    fireEvent.change(screen.getByLabelText('Filter by Job (Class)'), { target: { value: 'Ranger' } })
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => String(url).includes('class=Ranger'))).toBe(true))
  })
  it('stale requests do not overwrite newer results', async () => {
    let resolveOld!: (value: Response) => void
    const old = new Promise<Response>(resolve => { resolveOld = resolve })
    vi.spyOn(globalThis, 'fetch').mockImplementation(url => {
      const value = String(url)
      if (value.includes('/filters')) return response(filters)
      if (value.includes('search=new')) return response({ items: [{ ...hero, id: 'New', name: 'New Hero' }], total: 1, page: 1, pageSize: 250 })
      return old
    })
    render(<HeroRoster />); await new Promise(resolve => setTimeout(resolve, 220))
    fireEvent.change(screen.getByPlaceholderText('Search heroes…'), { target: { value: 'new' } })
    expect(await screen.findByRole('heading', { name: 'New Hero' })).toBeInTheDocument()
    resolveOld(await response({ items: [hero], total: 1, page: 1, pageSize: 250 }))
    await new Promise(resolve => setTimeout(resolve, 10)); expect(screen.queryAllByText('Ada Hero')).toHaveLength(0)
  })
})
