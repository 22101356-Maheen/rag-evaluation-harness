import { Link } from 'react-router-dom'
import logo from '../../assets/ragify-logo.png'

export default function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Ragify home">
      <img src={logo} width="60" height="40" alt="" />
      <span>Ragify<span className="brand-period">.</span></span>
    </Link>
  )
}
