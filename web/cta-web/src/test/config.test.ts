import { describe, expect, it } from 'vitest'
import { normalizeBaseUrl, publicAssetUrl } from '../api'
import { portraitUrl } from '../components/Portrait'

describe('deployment configuration', () => {
  it('uses same-origin API paths by default', () => expect(normalizeBaseUrl(undefined)).toBe(''))
  it('normalizes the API URL', () => expect(normalizeBaseUrl('https://api.example.test/')).toBe('https://api.example.test'))
  it('keeps portraits on the API origin', () => expect(portraitUrl('/assets/heroes/v1/a.png', 'https://api.test')).toBe('https://api.test/assets/heroes/v1/a.png'))
  it('uses same-origin public asset paths', () => expect(publicAssetUrl('/assets/ui-icons/v1/jobs/ranger.png')).toBe('/assets/ui-icons/v1/jobs/ranger.png'))
})
