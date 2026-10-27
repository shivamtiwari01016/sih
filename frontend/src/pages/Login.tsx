import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { useAuth, type AuthUser } from '../context/AuthContext'
import { errorMessage } from '../lib/api'
import { Button, ErrorBanner, Field, Input } from '../components/ui'

const demoAccounts = [
  {
    chipLabel: 'RB Officer (R.K. Sharma)',
    role: 'RB Officer',
    bureau: 'Regulation Bureau',
    email: 'sharma@samanvay.demo',
  },
  {
    chipLabel: 'PGRC Officer (Sunita Verma)',
    role: 'PGRC Officer',
    bureau: 'PGRC',
    email: 'verma@samanvay.demo',
  },
  {
    chipLabel: 'Senior Management (Dr. Ramesh Rao)',
    role: 'Senior Management',
    bureau: 'AICTE HQ',
    email: 'rao@samanvay.demo',
  },
  {
    chipLabel: 'Auditor',
    role: 'Auditor',
    bureau: 'Audit Directorate',
    email: 'auditor@samanvay.demo',
  },
]

function getPostLoginRoute(roleStr: string): string {
  const role = (roleStr || '').toLowerCase()
  if (role.includes('auditor')) {
    return '/audit-logs'
  }
  if (role.includes('management')) {
    return '/dashboard?tab=cop'
  }
  return '/dashboard?tab=my-desk'
}

export default function Login() {
  const [email, setEmail] = useState('sharma@samanvay.demo')
  const [password, setPassword] = useState('DemoPass123!')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { user, login } = useAuth()

  if (user) {
    return <Navigate to={getPostLoginRoute(user.role)} replace />
  }

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const loggedUser: AuthUser = await login(email.trim(), password)
      const targetRoute = getPostLoginRoute(loggedUser?.role || '')
      navigate(targetRoute)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-white to-slate-200 p-4">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl md:grid-cols-2">
        <div className="hidden flex-col justify-between bg-navy p-10 text-white md:flex">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-amber-500 p-2 text-navy">
                <ShieldCheck className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Samanvay</h1>
                <p className="text-xs text-slate-300">AICTE SIH26264 · Secure Complaint Coordination</p>
              </div>
            </div>
            <h2 className="mt-10 text-3xl font-bold leading-tight">
              One coordinated view of every institution complaint.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-slate-300">
              Track complaints across AICTE bureaus, review explainable overlap suggestions,
              coordinate transfers, monitor SLAs and generate audit-proven reports.
            </p>
            <ul className="mt-8 space-y-3 text-sm text-slate-200">
              <li>• Unified institution and complaint registry</li>
              <li>• Cross-bureau coordination and transfers</li>
              <li>• Explainable AI-assisted overlap review</li>
              <li>• SLA, ageing and disposal analytics</li>
            </ul>
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-3 text-xs text-slate-300">
            Samanvay AICTE Prototype · AICTE SIH26264 · Secure Complaint Coordination System.
          </div>
        </div>

        <div className="p-6 sm:p-10">
          <div className="mb-6 inline-flex rounded bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
            DEMO ENVIRONMENT
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500">
            Use a demo account below or enter your credentials.
          </p>

          <form className="mt-6 space-y-4" onSubmit={handleLogin}>
            <ErrorBanner message={error} />
            <Field label="Email" required>
              <Input
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="sharma@samanvay.demo"
              />
            </Field>
            <Field label="Password" required>
              <Input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="DemoPass123!"
              />
            </Field>
            <Button type="submit" className="w-full" loading={loading} size="lg">
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <div className="mt-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Quick-fill demo accounts
            </p>
            <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {demoAccounts.map((account) => {
                const isSelected = email === account.email
                return (
                  <button
                    key={account.email}
                    type="button"
                    onClick={() => {
                      setEmail(account.email)
                      setPassword('DemoPass123!')
                      setError('')
                    }}
                    className={`rounded-lg border p-2.5 text-left transition-all ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/70 shadow-xs'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="text-xs font-bold text-slate-900 truncate">
                      {account.chipLabel}
                    </div>
                    <div className="mt-0.5 text-[11px] font-medium text-slate-500">
                      {account.role} · {account.bureau}
                    </div>
                  </button>
                )
              })}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              All demo accounts use the password <span className="font-mono">DemoPass123!</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
