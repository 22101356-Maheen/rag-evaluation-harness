import { useEffect, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { ArrowUpRight, Menu, X } from 'lucide-react'
import { navigation } from '../../lib/constants'
import ThemeToggle from '../shared/ThemeToggle'
import Brand from '../shared/Brand'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuButton = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    function onEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && menuOpen) {
        setMenuOpen(false)
        menuButton.current?.focus()
      }
    }
    const desktop = matchMedia('(min-width: 1024px)')
    const closeOnDesktop = () => { if (desktop.matches) setMenuOpen(false) }
    document.addEventListener('keydown', onEscape)
    desktop.addEventListener('change', closeOnDesktop)
    return () => {
      document.removeEventListener('keydown', onEscape)
      desktop.removeEventListener('change', closeOnDesktop)
    }
  }, [menuOpen])

  return (
    <header className="site-header">
      <div className="container nav-bar">
        <Brand />
        <nav className="desktop-nav" aria-label="Main navigation">
          {navigation.map(link => <NavLink key={link.href} to={link.href} end>{link.label}</NavLink>)}
        </nav>
        <div className="nav-actions">
          <ThemeToggle />
          <Link className="text-button desktop-action" to="/sign-in">Sign In</Link>
          <Link className="button button-primary desktop-action" to="/sign-up">Try Ragify <ArrowUpRight size={16} aria-hidden="true" /></Link>
          <button ref={menuButton} className="icon-button menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-controls="mobile-navigation" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}>
            {menuOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
          </button>
        </div>
      </div>
      <nav id="mobile-navigation" className="mobile-nav container" aria-label="Mobile navigation" hidden={!menuOpen}>
        {navigation.map(link => <NavLink key={link.href} to={link.href} end onClick={() => setMenuOpen(false)}>{link.label}</NavLink>)}
        <Link className="text-button" to="/sign-in" onClick={() => setMenuOpen(false)}>Sign In</Link>
        <Link className="button button-primary" to="/sign-up" onClick={() => setMenuOpen(false)}>Try Ragify <ArrowUpRight size={16} aria-hidden="true" /></Link>
      </nav>
    </header>
  )
}
