import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { FormEvent } from 'react'
import AuthFormLayout from '../../components/auth/AuthFormLayout'

export default function SignInPage() {
  const [message, setMessage] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Clerk integration belongs here later. Never simulate a session or navigation.
    setMessage('Sign in is not connected yet. No credentials were sent and you have not been signed in.')
  }

  return (
    <AuthFormLayout title="Welcome back." description="Sign in to continue to your Ragify workspace.">
      <form className="form-stack" onSubmit={handleSubmit}>
        <div className="field"><label htmlFor="signin-email">Email</label><input id="signin-email" type="email" autoComplete="email" required placeholder="you@example.com" /></div>
        <div className="field"><label htmlFor="signin-password">Password</label><input id="signin-password" type="password" autoComplete="current-password" required /></div>
        <button className="text-link forgot-password" type="button" onClick={() => setMessage('Password recovery is not connected yet. No reset email has been sent.')}>Forgot password?</button>
        <button className="button button-primary w-full" type="submit">Sign In</button>
        <p className="form-status" role="status">{message}</p>
      </form>
      <p className="auth-switch">New to Ragify? <Link to="/sign-up">Create account</Link></p>
    </AuthFormLayout>
  )
}
