import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const next = theme === 'light' ? 'dark' : 'light'
  return (
    <button className="icon-button" type="button" onClick={() => setTheme(next)} aria-label={`Switch to ${next} mode`}>
      {theme === 'light' ? <Moon size={18} aria-hidden="true" /> : <Sun size={18} aria-hidden="true" />}
    </button>
  )
}
