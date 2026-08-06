import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

const apiTarget = 'http://localhost:5080'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(['/api', '/health', '/ready', '/assets', '/portraits', '/ui-icons'].map(path => [path, apiTarget])),
  },
  test: { environment: 'jsdom', setupFiles: './src/test/setup.ts' },
})
