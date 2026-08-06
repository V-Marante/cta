import { render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { App } from '../App'
import { hero, response } from './fixtures'

afterEach(() => vi.restoreAllMocks())

it('renders a navigated hero detail', async () => {
  history.replaceState({}, '', '/heroes/Ada')
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ hero, skills: [{ id: 'Arrow', name: 'Arrow', description: 'Hits.', components: [] }] }))
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Ada Hero', level: 1 })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Arrow' })).toBeInTheDocument()
})
