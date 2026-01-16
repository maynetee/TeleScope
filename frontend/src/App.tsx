import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, createContext, useContext } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Dashboard from './components/Dashboard'
import Feed from './components/Feed'
import ChannelList from './components/ChannelList'
import ChannelView from './components/ChannelView'
import Settings from './components/Settings'
import { messagesApi, LANGUAGES } from './api/client'

// Language context
interface LanguageContextType {
  language: string
  setLanguage: (lang: string) => void
  isTranslating: boolean
}

export const LanguageContext = createContext<LanguageContextType>({
  language: 'en',
  setLanguage: () => {},
  isTranslating: false,
})

export const useLanguage = () => useContext(LanguageContext)

function Navigation() {
  const location = useLocation()
  const { language, setLanguage, isTranslating } = useLanguage()
  const queryClient = useQueryClient()

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/feed', label: 'Feed' },
    { path: '/channels', label: 'Channels' },
    { path: '/settings', label: 'Settings' },
  ]

  const handleLanguageChange = async (newLang: string) => {
    setLanguage(newLang)
    try {
      await messagesApi.translate(newLang)
      // Refresh messages after translation
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      queryClient.invalidateQueries({ queryKey: ['daily-summary'] })
    } catch (error) {
      console.error('Translation failed:', error)
    }
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">TeleScope</h1>
            </div>
            <div className="ml-6 flex space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === item.path
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Language Selector */}
          <div className="flex items-center space-x-2">
            {isTranslating && (
              <span className="text-sm text-blue-600 animate-pulse">Translating...</span>
            )}
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              disabled={isTranslating}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  const [language, setLanguage] = useState(
    localStorage.getItem('telescope_language') || 'en'
  )
  const [isTranslating, setIsTranslating] = useState(false)

  const handleSetLanguage = async (lang: string) => {
    setIsTranslating(true)
    localStorage.setItem('telescope_language', lang)
    setLanguage(lang)
    // The actual translation is triggered in Navigation
    setTimeout(() => setIsTranslating(false), 2000) // Reset after 2s
  }

  return (
    <LanguageContext.Provider
      value={{ language, setLanguage: handleSetLanguage, isTranslating }}
    >
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/feed" element={<Feed />} />
              <Route path="/channels" element={<ChannelList />} />
              <Route path="/channels/:channelId" element={<ChannelView />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </LanguageContext.Provider>
  )
}

export default App
