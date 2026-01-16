import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name?: string
  role?: string
}

interface AuthTokens {
  accessToken: string
  refreshToken: string
  refreshExpiresAt: string
}

interface UserState {
  user: User | null
  tokens: AuthTokens | null
  _hasHydrated: boolean
  setUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens | null) => void
  logout: () => void
  setHasHydrated: (state: boolean) => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      _hasHydrated: false,
      setUser: (user) => set({ user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null }),
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'telescope-auth',
      partialize: (state) => ({ user: state.user, tokens: state.tokens }),
      onRehydrateStorage: () => (_state, error) => {
        if (error) {
          console.error('Error rehydrating auth store:', error)
        }
        // Always mark as hydrated, even on error
        useUserStore.setState({ _hasHydrated: true })
      },
    }
  )
)

// Ensure hydration happens even if onRehydrateStorage doesn't fire
if (typeof window !== 'undefined') {
  setTimeout(() => {
    if (!useUserStore.getState()._hasHydrated) {
      useUserStore.setState({ _hasHydrated: true })
    }
  }, 100)
}
