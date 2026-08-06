import React from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './styles.css'
import './hero-detail.css'
import './tier-list.css'
import './tier-title.css'

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
