import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import AuthFormLayout from '../../components/auth/AuthFormLayout'

export default function SignUpPage() {
  const [message, setMessage] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const password = form.elements.namedItem('password') as HTMLInputElement
    const confirmation = form.elements.namedItem('confirmation') as HTMLInputElement
    confirmation.setCustomValidity(password.value === confirmation.value ? '' : 'Passwords must match.')
    if (!form.reportValidity()) return
    // Replace this boundary with Clerk later. No credentials are stored or sent.
    setMessage('Account creation is not connected yet. No account was created and no credentials were sent.')
  }

  return (
    <AuthFormLayout title="Start with clarity." description="Create an account for your Ragify workspace.">
      <form className="form-stack" onSubmit={handleSubmit}>
        <div className="field"><label htmlFor="signup-name">Name</label><input id="signup-name" name="name" autoComplete="name" required maxLength={100} /></div>
        <div className="field"><label htmlFor="signup-email">Email</label><input id="signup-email" type="email" autoComplete="email" required placeholder="you@example.com" /></div>
        <div className="field"><label htmlFor="signup-password">Password</label><input id="signup-password" name="password" type="password" autoComplete="new-password" required minLength={8} aria-describedby="password-hint" onInput={event => {
          const confirmation = event.currentTarget.form?.elements.namedItem('confirmation') as HTMLInputElement | null
          confirmation?.setCustomValidity('')
        }} /><p id="password-hint">Use at least 8 characters for this form preview.</p></div>
        <div className="field"><label htmlFor="signup-confirmation">Confirm Password</label><input id="signup-confirmation" name="confirmation" type="password" autoComplete="new-password" required onInput={event => event.currentTarget.setCustomValidity('')} /></div>
        <button className="button button-primary w-full" type="submit">Create Account</button>
        <p className="form-status" role="status">{message}</p>
      </form>
      <p className="auth-switch">Already have an account? <Link to="/sign-in">Sign In</Link></p>
    </AuthFormLayout>
  )
}
