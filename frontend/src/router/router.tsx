import { useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import PublicLayout from '../layouts/PublicLayout'
import AppLayout from '../layouts/AppLayout'
import HomePage from '../pages/public/HomePage'
import FeaturesPage from '../pages/public/FeaturesPage'
import HowItWorksPage from '../pages/public/HowItWorksPage'
import NotFoundPage from '../pages/public/NotFoundPage'
import SignInPage from '../pages/auth/SignInPage'
import SignUpPage from '../pages/auth/SignUpPage'
import DashboardPage from '../pages/app/DashboardPage'
import ProjectsPage from '../pages/app/ProjectsPage'
import ProjectDetailPage from '../pages/app/ProjectDetailPage'
import EvaluationsPage from '../pages/app/EvaluationsPage'
import ResultsPage from '../pages/app/ResultsPage'
import SettingsPage from '../pages/app/SettingsPage'

const titles: Record<string, string> = {
  '/': 'Know what works before you ship.',
  '/features': 'Features', '/how-it-works': 'How It Works',
  '/sign-in': 'Sign In', '/sign-up': 'Sign Up', '/dashboard': 'Dashboard',
  '/projects': 'Projects', '/evaluations': 'Evaluations', '/results': 'Results', '/settings': 'Settings',
}

export default function AppRoutes() {
  const { pathname } = useLocation()
  useEffect(() => {
    const title = titles[pathname] ?? (pathname.startsWith('/projects/') ? 'Project workspace' : 'Page not found')
    document.title = `${title} | Ragify`
    window.scrollTo({ top: 0, behavior: 'instant' })
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [pathname])

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="features" element={<FeaturesPage />} />
        <Route path="how-it-works" element={<HowItWorksPage />} />
        <Route path="sign-in" element={<SignInPage />} />
        <Route path="sign-up" element={<SignUpPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      {/* UI preview only. Add real Clerk protection here when authentication is integrated. */}
      <Route element={<AppLayout />}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="evaluations" element={<EvaluationsPage />} />
        <Route path="results" element={<ResultsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
