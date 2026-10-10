import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { ThemeContext } from '../../lib/theme'
import type { Theme } from '../../lib/theme'

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, updateTheme] = useState<Theme>(() =>
    document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
  )

  function setTheme(next: Theme) {
    updateTheme(next)
    try { localStorage.setItem('ragify-theme', next) } catch { /* Keep working without storage. */ }
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#050A14' : '#F7F8FA')
  }, [theme])

  useEffect(() => {
    const syncPreference = (event: StorageEvent) => {
      if (event.key === 'ragify-theme') updateTheme(event.newValue === 'dark' ? 'dark' : 'light')
    }
    window.addEventListener('storage', syncPreference)
    return () => window.removeEventListener('storage', syncPreference)
  }, [])

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}
