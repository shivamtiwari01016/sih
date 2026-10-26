import { useState, type FormEvent } from 'react'
import { CheckCircle2, Lock, ShieldCheck, UserCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Badge, Button, DetailRow, ErrorBanner, Field, Input, PageHeader } from '../components/ui'

export default function Settings() {
  const { user, refreshUser } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const changePassword = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match')
      return
    }
    setSaving(true)
    try {
      const response = await api.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success(response.data.message || 'Password updated')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      await refreshUser()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Account details, security and environment information"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <UserCircle2 className="h-5 w-5 text-slate-500" />
            <h2 className="text-base font-semibold text-slate-900">Your profile</h2>
          </div>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <DetailRow label="Full name" value={user?.full_name || '—'} />
            <DetailRow label="Email" value={user?.email || '—'} />
            <DetailRow label="Role" value={user?.role || '—'} />
            <DetailRow label="Bureau" value={user?.bureau_name || 'Not assigned'} />
            <DetailRow
              label="Account status"
              value={
                <Badge
                  className={
                    user?.active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-slate-200 text-slate-600'
                  }
                >
                  {user?.active ? 'Active' : 'Inactive'}
                </Badge>
              }
            />
            <DetailRow label="User ID" value={<span className="font-mono text-xs">{user?.id}</span>} />
          </dl>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-slate-500" />
            <h2 className="text-base font-semibold text-slate-900">Change password</h2>
          </div>
          <form className="mt-4 space-y-3" onSubmit={changePassword}>
            <ErrorBanner message={error} />
            <Field label="Current password" required>
              <Input
                type="password"
                required
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            </Field>
            <Field label="New password" required hint="Minimum 8 characters.">
              <Input
                type="password"
                required
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </Field>
            <Field label="Confirm new password" required>
              <Input
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </Field>
            <Button type="submit" loading={saving}>
              <CheckCircle2 className="h-4 w-4" /> Update password
            </Button>
          </form>
        </div>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-5 w-5 text-amber-600" />
          <div>
            <h2 className="text-base font-semibold text-amber-900">Demo environment</h2>
            <p className="mt-1 text-sm text-amber-800">
              This prototype runs on synthetic demonstration data. It is not affiliated with
              AICTE and must not be used with real complainant information.
            </p>
            <ul className="mt-2 list-inside list-disc text-sm text-amber-800">
              <li>API documentation: <span className="font-mono">/docs</span> on port 8000</li>
              <li>Semantic matching gracefully falls back to explainable rule-based scoring</li>
              <li>All demo accounts share the password <span className="font-mono">DemoPass123!</span></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
