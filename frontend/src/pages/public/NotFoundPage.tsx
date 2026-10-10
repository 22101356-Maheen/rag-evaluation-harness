import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="container public-page-intro not-found">
      <p className="eyebrow">PAGE NOT FOUND</p><h1>That page isn’t here.</h1>
      <p>Check the address or return to Ragify.</p>
      <Link className="button button-primary" to="/">Back to Home</Link>
    </section>
  )
}
