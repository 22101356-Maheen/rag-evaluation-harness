import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './router/router'
import ThemeProvider from './components/shared/ThemeProvider'

export default function App() {
  return <ThemeProvider><BrowserRouter><AppRoutes /></BrowserRouter></ThemeProvider>
}
