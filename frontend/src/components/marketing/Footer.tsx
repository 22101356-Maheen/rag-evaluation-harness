import { Link } from 'react-router-dom'
import { navigation } from '../../lib/constants'
import Brand from '../shared/Brand'

const currentYear = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="site-footer container">
      <div className="footer-main">
        <div><Brand /><p>A clearer view of your RAG performance.</p></div>
        <nav aria-label="Footer navigation">
          {navigation.map(link => <Link key={link.href} to={link.href}>{link.label}</Link>)}
          <Link className="text-button" to="/sign-in">Sign In</Link>
        </nav>
      </div>
      <div className="footer-bottom"><span>© {currentYear} Ragify</span><span>Know what works before you ship.</span></div>
    </footer>
  )
}
