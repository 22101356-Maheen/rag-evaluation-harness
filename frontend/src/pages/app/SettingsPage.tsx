import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import PageHeader from '../../components/shared/PageHeader'

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  return (
    <>
      <PageHeader title="Settings" description="Make the workspace comfortable for the way you work." />
      <section className="panel settings-panel">
        <div className="panel-heading"><h2>Appearance</h2></div>
        <div className="settings-body">
          <div><h3>Theme preference</h3><p>Light is the default on your first visit. Your selection is saved in this browser.</p></div>
          <fieldset className="theme-options"><legend className="sr-only">Choose your theme</legend>
            <label className={theme === 'light' ? 'is-selected' : ''}><input type="radio" name="theme" value="light" checked={theme === 'light'} onChange={() => setTheme('light')} /><Sun size={20} aria-hidden="true" /><span>Light</span></label>
            <label className={theme === 'dark' ? 'is-selected' : ''}><input type="radio" name="theme" value="dark" checked={theme === 'dark'} onChange={() => setTheme('dark')} /><Moon size={20} aria-hidden="true" /><span>Dark</span></label>
          </fieldset>
          <p className="small-note" role="status">Current theme: {theme === 'light' ? 'Light' : 'Dark'}</p>
        </div>
      </section>
      <p className="settings-footnote">Account settings will become available when authentication is connected.</p>
    </>
  )
}
