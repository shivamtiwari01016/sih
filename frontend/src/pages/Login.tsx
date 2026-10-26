import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../lib/api'
import { Button, ErrorBanner, Field, Input } from '../components/ui'

const demoAccounts = [
  { label: 'Super Admin', email: 'admin@civicresolve.demo' },
  { label: 'Bureau Admin', email: 'regadmin@civicresolve.demo' },
  { label: 'Case Officer', email: 'officer1@civicresolve.demo' },
  { label: 'Management', email: 'mgmt@civicresolve.demo' },
]

export default function Login() {
  const [email, setEmail] = useState('admin@civicresolve.demo')
  const [password, setPassword] = useState('DemoPass123!')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { user, login } = useAuth()

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(email.trim(), password)
      navigate('/dashboard')
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
                <h1 className="text-xl font-bold">CivicResolve Intelligence</h1>
                <p className="text-xs text-slate-300">Institution Complaint Monitoring</p>
              </div>
            </div>
            <h2 className="mt-10 text-3xl font-bold leading-tight">
              One coordinated view of every institution complaint.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-slate-300">
              Track complaints across AICTE bureaus, review explainable overlap suggestions,
              coordinate transfers, monitor SLAs and generate reports.
            </p>
            <ul className="mt-8 space-y-3 text-sm text-slate-200">
              <li>• Unified institution and complaint registry</li>
              <li>• Cross-bureau coordination and transfers</li>
              <li>• Explainable AI-assisted overlap review</li>
              <li>• SLA, ageing and disposal analytics</li>
            </ul>
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-3 text-xs text-slate-300">
            Demo prototype — use only synthetic demonstration data. Not affiliated with AICTE.
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
                placeholder="admin@civicresolve.demo"
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
            <div className="mt-2 flex flex-wrap gap-2">
              {demoAccounts.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => {
                    setEmail(account.email)
                    setPassword('DemoPass123!')
                    setError('')
                  }}
                  className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:border-slate-400 hover:bg-slate-50"
                >
                  {account.label}
                </button>
              ))}
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
