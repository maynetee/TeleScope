import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUserStore } from '@/stores/user-store'
import { authApi } from '@/lib/api/client'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

type LoginFormValues = z.infer<typeof loginSchema>
type RegisterFormValues = z.infer<typeof registerSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const { setUser, setTokens } = useUserStore()
  const { t } = useTranslation()
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const registerForm = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '' },
  })

  const handleLogin = async (values: LoginFormValues) => {
    setError(null)
    try {
      const response = await authApi.login(values.email, values.password)
      const { access_token, refresh_token, refresh_expires_at } = response.data

      setTokens({
        accessToken: access_token,
        refreshToken: refresh_token,
        refreshExpiresAt: refresh_expires_at,
      })

      // Fetch user profile
      const userResponse = await authApi.me()
      setUser({
        id: userResponse.data.id,
        email: userResponse.data.email,
        name: userResponse.data.email.split('@')[0],
      })

      navigate('/')
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || t('auth.loginError'))
    }
  }

  const handleRegister = async (values: RegisterFormValues) => {
    setError(null)
    try {
      await authApi.register(values.email, values.password)
      // After registration, login automatically
      await handleLogin(values)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || t('auth.registerError'))
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-auth px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{isRegister ? t('auth.registerTitle') : t('auth.loginTitle')}</CardTitle>
          <CardDescription>
            {isRegister ? t('auth.registerDescription') : t('auth.loginDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md bg-danger/10 p-3 text-sm text-danger">{error}</div>
          )}
          {isRegister ? (
            <form
              className="flex flex-col gap-4"
              onSubmit={registerForm.handleSubmit(handleRegister)}
            >
              <div className="flex flex-col gap-2">
                <Label htmlFor="reg-email">{t('auth.email')}</Label>
                <Input
                  id="reg-email"
                  type="email"
                  placeholder={t('auth.emailPlaceholder')}
                  {...registerForm.register('email')}
                />
                {registerForm.formState.errors.email && (
                  <span className="text-xs text-danger">
                    {registerForm.formState.errors.email.message}
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="reg-password">{t('auth.password')}</Label>
                <Input
                  id="reg-password"
                  type="password"
                  placeholder={t('auth.passwordPlaceholder')}
                  {...registerForm.register('password')}
                />
                {registerForm.formState.errors.password && (
                  <span className="text-xs text-danger">
                    {registerForm.formState.errors.password.message}
                  </span>
                )}
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={registerForm.formState.isSubmitting}
              >
                {registerForm.formState.isSubmitting
                  ? t('auth.registering')
                  : t('auth.createAccount')}
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full text-foreground/60"
                onClick={() => setIsRegister(false)}
              >
                {t('auth.alreadyHaveAccount')}
              </Button>
            </form>
          ) : (
            <form className="flex flex-col gap-4" onSubmit={loginForm.handleSubmit(handleLogin)}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="login-email">{t('auth.email')}</Label>
                <Input
                  id="login-email"
                  type="email"
                  placeholder={t('auth.emailPlaceholder')}
                  {...loginForm.register('email')}
                />
                {loginForm.formState.errors.email && (
                  <span className="text-xs text-danger">
                    {loginForm.formState.errors.email.message}
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="login-password">{t('auth.password')}</Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder={t('auth.passwordPlaceholder')}
                  {...loginForm.register('password')}
                />
                {loginForm.formState.errors.password && (
                  <span className="text-xs text-danger">
                    {loginForm.formState.errors.password.message}
                  </span>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={loginForm.formState.isSubmitting}>
                {loginForm.formState.isSubmitting ? t('auth.signingIn') : t('auth.signIn')}
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full text-foreground/60"
                onClick={() => setIsRegister(true)}
              >
                {t('auth.createAccount')}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
