import { Navigate, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useUserStore } from '@/stores/user-store'

export function AuthGuard() {
  const { t } = useTranslation()
  const tokens = useUserStore((state) => state.tokens)
  const hasHydrated = useUserStore((state) => state._hasHydrated)

  // Wait for store hydration before checking auth
  if (!hasHydrated) {
    return <div className="flex h-screen items-center justify-center text-foreground/60">{t('common.loading')}</div>
  }

  // Require authentication - check for tokens (user with valid JWT)
  if (!tokens?.accessToken) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
