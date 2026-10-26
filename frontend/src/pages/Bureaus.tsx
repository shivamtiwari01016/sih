import { useCallback, useEffect, useState } from 'react'
import { Briefcase, Pencil, Plus, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
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
  Textarea,
} from '../components/ui'

interface Bureau {
  id: string
  bureau_code: string
  bureau_name: string
  description: string | null
  active: boolean
  complaint_count: number
  user_count: number
}

export default function Bureaus() {
  const { isSuperAdmin } = useAuth()
  const [bureaus, setBureaus] = useState<Bureau[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Bureau | null>(null)
  const [form, setForm] = useState({ bureau_code: '', bureau_name: '', description: '' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<Bureau[]>('/api/bureaus')
      setBureaus(response.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const openCreate = () => {
    setEditing(null)
    setForm({ bureau_code: '', bureau_name: '', description: '' })
    setOpen(true)
  }

  const openEdit = (bureau: Bureau) => {
    setEditing(bureau)
    setForm({
      bureau_code: bureau.bureau_code,
      bureau_name: bureau.bureau_name,
      description: bureau.description || '',
    })
    setOpen(true)
  }

  const submit = async () => {
    if (form.bureau_name.trim().length < 2) {
      toast.error('Bureau name is required')
      return
    }
    if (!editing && form.bureau_code.trim().length < 2) {
      toast.error('Bureau code is required')
      return
    }
    setSaving(true)
    try {
      if (editing) {
        const response = await api.patch(`/api/bureaus/${editing.id}`, {
          bureau_name: form.bureau_name.trim(),
          description: form.description.trim() || null,
        })
        toast.success(response.data.message || 'Bureau updated')
      } else {
        const response = await api.post('/api/bureaus', {
          bureau_code: form.bureau_code.trim(),
          bureau_name: form.bureau_name.trim(),
          description: form.description.trim() || null,
        })
        toast.success(response.data.message || 'Bureau created')
      }
      setOpen(false)
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (bureau: Bureau) => {
    try {
      await api.patch(`/api/bureaus/${bureau.id}`, { active: !bureau.active })
      toast.success(bureau.active ? 'Bureau deactivated' : 'Bureau activated')
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bureau Management"
        subtitle="Bureaus that handle complaints and coordinate on overlapping cases"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            {isSuperAdmin && (
              <Button onClick={openCreate}>
                <Plus className="h-4 w-4" /> Add bureau
              </Button>
            )}
          </>
        }
      />

      <ErrorBanner message={error} />

      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <LoadingBlock label="Loading bureaus…" />
        </div>
      ) : bureaus.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <EmptyState
            title="No bureaus configured"
            description="Create a bureau before assigning complaints."
            action={
              isSuperAdmin ? (
                <Button onClick={openCreate}>
                  <Plus className="h-4 w-4" /> Add bureau
                </Button>
              ) : undefined
            }
          />
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {bureaus.map((bureau) => (
            <div
              key={bureau.id}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2">
                  <span className="rounded-md bg-blue-50 p-2 text-blue-600">
                    <Briefcase className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{bureau.bureau_name}</p>
                    <p className="text-xs font-medium text-slate-500">{bureau.bureau_code}</p>
                  </div>
                </div>
                <Badge
                  className={
                    bureau.active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-slate-200 text-slate-600'
                  }
                >
                  {bureau.active ? 'Active' : 'Inactive'}
                </Badge>
              </div>

              <p className="mt-2 min-h-[2.5rem] text-xs text-slate-600">
                {bureau.description || 'No description provided.'}
              </p>

              <div className="mt-3 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-center">
                <div>
                  <p className="text-lg font-bold text-slate-900">{bureau.complaint_count}</p>
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Complaints</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-slate-900">{bureau.user_count}</p>
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Users</p>
                </div>
              </div>

              {isSuperAdmin && (
                <div className="mt-3 flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(bureau)}>
                    <Pencil className="h-3.5 w-3.5" /> Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void toggleActive(bureau)}
                  >
                    {bureau.active ? 'Deactivate' : 'Activate'}
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Edit bureau' : 'Add bureau'}
        description={
          editing
            ? 'Update the bureau name or description.'
            : 'Create a new bureau to route complaints.'
        }
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button loading={saving} onClick={() => void submit()}>
              {editing ? 'Save changes' : 'Create bureau'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Bureau code" required hint="Short unique code, e.g. REG">
            <Input
              value={form.bureau_code}
              disabled={Boolean(editing)}
              onChange={(event) => setForm({ ...form, bureau_code: event.target.value })}
              placeholder="REG"
            />
          </Field>
          <Field label="Bureau name" required>
            <Input
              value={form.bureau_name}
              onChange={(event) => setForm({ ...form, bureau_name: event.target.value })}
              placeholder="Regulation Bureau"
            />
          </Field>
          <Field label="Description">
            <Textarea
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="What kind of complaints does this bureau handle?"
            />
          </Field>
        </div>
      </Modal>
    </div>
  )
}
