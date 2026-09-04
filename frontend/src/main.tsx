import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import StudioApp from './StudioApp'
import './styles.css'

const studioRoute = window.location.pathname === '/studio' || new URLSearchParams(window.location.search).get('ui') === 'studio'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {studioRoute ? <StudioApp /> : <App />}
  </StrictMode>,
)
