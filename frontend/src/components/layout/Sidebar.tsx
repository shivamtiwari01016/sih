import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Building2,
  FileText,
  GitBranch,
  Users,
  Bell,
  BarChart3,
  Briefcase,
  UserCog,
  FileSearch,
  Settings,
  ShieldCheck,
  Inbox,
  Target,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useLanguage } from '../../context/LanguageContext'

export default function Sidebar() {
  const { user, isAdmin } = useAuth()
  const { t } = useLanguage()

  const navItems = [
    { name: t('nav.my_desk'), path: '/dashboard?tab=my-desk', icon: Inbox },
    { name: t('nav.dashboard'), path: '/dashboard', icon: LayoutDashboard },
    { name: t('nav.institutions'), path: '/institutions', icon: Building2 },
    { name: t('nav.complaints'), path: '/complaints', icon: FileText },
    { name: t('nav.overlaps'), path: '/overlaps', icon: GitBranch },
    { name: t('nav.accuracy'), path: '/overlaps?tab=accuracy', icon: Target },
    { name: t('nav.coordination'), path: '/coordination', icon: Users },
    { name: t('nav.notifications'), path: '/notifications', icon: Bell },
    { name: t('nav.reports'), path: '/reports', icon: BarChart3 },
    { name: t('nav.bureaus'), path: '/bureaus', icon: Briefcase },
    { name: t('nav.users'), path: '/users', icon: UserCog, adminOnly: true },
    { name: t('nav.audit'), path: '/audit-logs', icon: FileSearch, adminOnly: true },
    { name: t('nav.settings'), path: '/settings', icon: Settings },
  ]

  return (
    <aside className="hidden h-full w-64 shrink-0 flex-col bg-navy text-white md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-slate-700 px-4">
        <ShieldCheck className="h-7 w-7 text-amber-400" />
        <div>
          <h1 className="text-sm font-bold leading-tight tracking-tight">Samanvay (समन्वय)</h1>
          <p className="text-[11px] text-slate-400">AICTE Complaint Coordination</p>
        </div>
      </div>
      <div className="bg-emerald-600 px-4 py-1.5 text-center text-[10px] font-bold tracking-wider text-white uppercase">
        {t('demo.badge')}
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
        {navItems
          .filter((item) => !item.adminOnly || isAdmin)
          .map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-white font-medium'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="h-4 w-4 text-slate-400" />
              {item.name}
            </NavLink>
          ))}
      </nav>
      <div className="border-t border-slate-700 px-4 py-3 bg-slate-900/40">
        <p className="truncate text-xs font-semibold text-slate-200">{user?.full_name}</p>
        <p className="truncate text-[11px] text-slate-400">
          {user?.role}
          {user?.bureau_name ? ` · ${user.bureau_name}` : ''}
        </p>
      </div>
    </aside>
  )
}
