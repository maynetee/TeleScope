import { Navigate } from 'react-router-dom'

// Registration is now handled in the login page
export function RegisterPage() {
  return <Navigate to="/login" replace />
}
