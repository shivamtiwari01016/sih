import { useEffect, useState } from 'react'
import { Bell, Globe, LogOut, Sparkles } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'
import { useLanguage } from '../../context/LanguageContext'
import { Badge } from '../ui'
import DailyBriefingModal from '../DailyBriefingModal'

export default function Header() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const { lang, setLang, t } = useLanguage()
  const [unread, setUnread] = useState(0)
  const [briefingOpen, setBriefingOpen] = useState(false)

  useEffect(() => {
    if (!user) return
    let active = true
    const load = async () => {
      try {
        const response = await api.get<{ unread: number }>('/api/notifications/unread-count')
        if (active) setUnread(response.data.unread)
      } catch {
        // Header badge is non-critical.
      }
    }
    void load()
    const timer = window.setInterval(load, 30000)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [user, location.pathname])

  const initials = (user?.full_name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')

  const getPageTitle = () => {
    if (location.pathname === '/dashboard') return t('nav.dashboard')
    if (location.pathname === '/institutions') return t('nav.institutions')
    if (location.pathname === '/complaints') return t('nav.complaints')
    if (location.pathname === '/overlaps') return t('nav.overlaps')
    if (location.pathname === '/coordination') return t('nav.coordination')
    if (location.pathname === '/notifications') return t('nav.notifications')
    if (location.pathname === '/reports') return t('nav.reports')
    if (location.pathname === '/bureaus') return t('nav.bureaus')
    if (location.pathname === '/users') return t('nav.users')
    if (location.pathname === '/audit-logs') return t('nav.audit')
    if (location.pathname === '/settings') return t('nav.settings')
    return t('brand.name')
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b bg-white px-6">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">
          {getPageTitle()}
        </h2>
        <span className="hidden text-xs text-slate-400 lg:inline-block">|</span>
        <span className="hidden text-xs font-medium text-slate-600 lg:inline-block">
          {t('brand.subtitle')}
        </span>
      </div>
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Language Toggle */}
        <button
          type="button"
          onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
          className="flex items-center gap-1.5 rounded-full border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
          title="Toggle Language / भाषा बदलें"
        >
          <Globe className="h-3.5 w-3.5 text-blue-600" />
          <span>{lang === 'en' ? 'हिन्दी' : 'English'}</span>
        </button>

        <Badge className="hidden bg-emerald-100 text-emerald-800 font-medium sm:inline-flex">
          {t('demo.badge')}
        </Badge>

        {/* Daily Briefing button */}
        <button
          type="button"
          onClick={() => setBriefingOpen(true)}
          className="flex items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-semibold text-purple-700 hover:bg-purple-100 transition-colors"
          title="Daily 60-Second Briefing"
        >
          <Sparkles className="h-3.5 w-3.5 text-purple-600" />
          <span className="hidden sm:inline">Daily Briefing</span>
        </button>

        <button
          type="button"
          onClick={() => navigate('/notifications')}
          className="relative rounded-md p-2 text-slate-600 hover:bg-slate-100"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unread > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {unread > 99 ? '99+' : unread}
            </span>
          )}
        </button>
        <div className="hidden items-center gap-2 rounded-md border border-slate-200 px-2.5 py-1.5 sm:flex">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-navy text-xs font-semibold text-white">
            {initials}
          </div>
          <div className="leading-tight">
            <p className="text-xs font-semibold text-slate-900">{user?.full_name || 'AICTE Officer'}</p>
            <p className="text-[11px] text-slate-500 font-medium">{user?.role || 'Officer'}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void logout()}
          className="flex items-center gap-1.5 rounded-md p-2 text-sm text-slate-600 hover:bg-slate-100"
          title="Sign out"
        >
          <LogOut className="h-5 w-5" />
          <span className="hidden md:inline">Sign out</span>
        </button>
      </div>

      <DailyBriefingModal
        open={briefingOpen}
        onClose={() => setBriefingOpen(false)}
      />
    </header>
  )
}
