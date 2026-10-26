import { useCallback, useEffect, useMemo, useState } from 'react'
import { Pencil, Plus, RefreshCw, Search, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { formatDateTime } from '../lib/utils'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  Field,
  Input,
  LoadingBlock,
  Modal,
  PageHeader,
  Select,
} from '../components/ui'

interface UserRow {
  id: string
  full_name: string
  email: string
  role: string
  bureau_id: string | null
  bureau_name: string | null
  region_permissions: string | null
  active: boolean
  last_login_at: string | null
  created_at: string | null
}

interface BureauOption {
  id: string
  bureau_code: string
  bureau_name: string
}

const roles = [
  'Super Administrator',
  'Bureau Administrator',
  'Case Officer',
  'Regional Officer',
  'Senior Management',
]

const bureauRequiredRoles = ['Bureau Administrator', 'Case Officer', 'Regional Officer']

const emptyForm = {
  full_name: '',
  email: '',
  password: '',
  role: 'Case Officer',
  bureau_id: '',
  region_permissions: '',
  active: true,
}

export default function Users() {
  const { isSuperAdmin, user: currentUser } = useAuth()
  const [users, setUsers] = useState<UserRow[]>([])
  const [bureaus, setBureaus] = useState<BureauOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<UserRow | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [userResponse, bureauResponse] = await Promise.all([
        api.get<UserRow[]>('/api/users'),
        api.get<BureauOption[]>('/api/bureaus'),
      ])
      setUsers(userResponse.data)
      setBureaus(bureauResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return users.filter((user) => {
      if (roleFilter && user.role !== roleFilter) return false
      if (!term) return true
      return (
        user.full_name.toLowerCase().includes(term) ||
        user.email.toLowerCase().includes(term) ||
        (user.bureau_name || '').toLowerCase().includes(term)
      )
    })
  }, [users, search, roleFilter])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setOpen(true)
  }

  const openEdit = (user: UserRow) => {
    setEditing(user)
    setForm({
      full_name: user.full_name,
      email: user.email,
      password: '',
      role: user.role,
      bureau_id: user.bureau_id || '',
      region_permissions: user.region_permissions || '',
      active: user.active,
    })
    setOpen(true)
  }

  const submit = async () => {
    if (form.full_name.trim().length < 2 || !form.email.includes('@')) {
      toast.error('Enter a valid name and email address')
      return
    }
    if (!editing && form.password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    if (form.password && form.password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    if (bureauRequiredRoles.includes(form.role) && !form.bureau_id) {
      toast.error('This role requires a bureau')
      return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        role: form.role,
        bureau_id: form.bureau_id || null,
        region_permissions: form.region_permissions.trim() || null,
        active: form.active,
      }
      if (form.password) payload.password = form.password

      if (editing) {
        const response = await api.patch(`/api/users/${editing.id}`, payload)
        toast.success(response.data.message || 'User updated')
      } else {
        if (!form.password) {
          toast.error('Password is required for a new user')
          setSaving(false)
          return
        }
        const response = await api.post('/api/users', payload)
        toast.success(response.data.message || 'User created')
      }
      setOpen(false)
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (target: UserRow) => {
    if (target.id === currentUser?.id) {
      toast.error('You cannot deactivate your own account')
      return
    }
    try {
      await api.patch(`/api/users/${target.id}`, { active: !target.active })
      toast.success(target.active ? 'User deactivated' : 'User activated')
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Management"
        subtitle="Accounts, roles and bureau assignments"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            {isSuperAdmin && (
              <Button onClick={openCreate}>
                <Plus className="h-4 w-4" /> Add user
              </Button>
            )}
          </>
        }
      />

      <ErrorBanner message={error} />

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            placeholder="Search name, email or bureau…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <Select
          className="w-full max-w-xs"
          value={roleFilter}
          onChange={(event) => setRoleFilter(event.target.value)}
        >
          <option value="">All roles</option>
          {roles.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </Select>
        <p className="text-sm text-slate-500">{filtered.length} account(s)</p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <LoadingBlock label="Loading users…" />
        ) : filtered.length === 0 ? (
          <EmptyState title="No users found" description="Adjust the filters to see accounts." />
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                {['User', 'Role', 'Bureau', 'Status', 'Last login', ''].map((heading) => (
                  <th
                    key={heading}
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy text-xs font-semibold text-white">
                        {row.full_name
                          .split(' ')
                          .slice(0, 2)
                          .map((part) => part[0]?.toUpperCase())
                          .join('')}
                      </span>
                      <div>
                        <p className="font-medium text-slate-900">
                          {row.full_name}
                          {row.id === currentUser?.id && (
                            <span className="ml-1 text-[11px] text-slate-400">(you)</span>
                          )}
                        </p>
                        <p className="text-xs text-slate-500">{row.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <Badge className="bg-slate-100 text-slate-700">
                      {row.role === 'Super Administrator' && (
                        <ShieldCheck className="mr-1 h-3 w-3" />
                      )}
                      {row.role}
                    </Badge>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{row.bureau_name || '—'}</td>
                  <td className="px-5 py-3">
                    <Badge
                      className={
                        row.active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-slate-200 text-slate-600'
                      }
                    >
                      {row.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-5 py-3 text-slate-500">
                    {formatDateTime(row.last_login_at)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {isSuperAdmin && (
                      <div className="flex justify-end gap-1">
                        <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>
                          <Pencil className="h-3.5 w-3.5" /> Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => void toggleActive(row)}
                        >
                          {row.active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Edit user' : 'Add user'}
        description={
          editing
            ? 'Update role, bureau or reset the password.'
            : 'Create a new account with a role and bureau assignment.'
        }
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button loading={saving} onClick={() => void submit()}>
              {editing ? 'Save changes' : 'Create user'}
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" required>
            <Input
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              placeholder="e.g. Asha Verma"
            />
          </Field>
          <Field label="Email" required>
            <Input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="name@civicresolve.demo"
            />
          </Field>
          <Field
            label={editing ? 'New password' : 'Password'}
            required={!editing}
            hint={editing ? 'Leave blank to keep the current password.' : 'Minimum 8 characters.'}
          >
            <Input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              placeholder="••••••••"
            />
          </Field>
          <Field label="Role" required>
            <Select
              value={form.role}
              onChange={(event) =>
                setForm({
                  ...form,
                  role: event.target.value,
                  bureau_id: bureauRequiredRoles.includes(event.target.value)
                    ? form.bureau_id
                    : '',
                })
              }
            >
              {roles.map((role) => (
                <option key={role}>{role}</option>
              ))}
            </Select>
          </Field>
          <Field
            label="Bureau"
            required={bureauRequiredRoles.includes(form.role)}
            hint={
              bureauRequiredRoles.includes(form.role)
                ? 'Required for this role.'
                : 'Optional for this role.'
            }
          >
            <Select
              value={form.bureau_id}
              onChange={(event) => setForm({ ...form, bureau_id: event.target.value })}
            >
              <option value="">No bureau</option>
              {bureaus.map((bureau) => (
                <option key={bureau.id} value={bureau.id}>
                  {bureau.bureau_code} — {bureau.bureau_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Region permissions" hint="Comma separated regions, optional.">
            <Input
              value={form.region_permissions}
              onChange={(event) =>
                setForm({ ...form, region_permissions: event.target.value })
              }
              placeholder="West, South"
            />
          </Field>
          <label className="flex items-center gap-2 text-sm text-slate-700 sm:col-span-2">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300"
              checked={form.active}
              onChange={(event) => setForm({ ...form, active: event.target.checked })}
            />
            Account is active
          </label>
        </div>
      </Modal>
    </div>
  )
}
