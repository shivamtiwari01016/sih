import { useCallback, useEffect, useState } from 'react'
import { ArrowRight, CheckCircle2, MessageSquare, Plus, RefreshCw, Users } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { formatDateTime, reviewStatusClass, statusClass } from '../lib/utils'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  Field,
  LoadingBlock,
  Modal,
  PageHeader,
  Select,
  Textarea,
} from '../components/ui'

interface Coordination {
  id: string
  complaint_id: string
  complaint_number: string | null
  complaint_subject: string | null
  complaint_status: string | null
  institution: string | null
  from_bureau: string | null
  from_bureau_id: string
  to_bureau: string | null
  to_bureau_id: string
  reason: string
  status: string | null
  requested_by: string | null
  approved_by: string | null
  created_at: string | null
  completed_at: string | null
}

interface ComplaintOption {
  id: string
  complaint_number: string
  subject: string
  current_status: string | null
  assigned_bureau: string | null
  assigned_bureau_id: string | null
}

interface BureauOption {
  id: string
  bureau_code: string
  bureau_name: string
}

const statuses = ['Pending', 'Approved', 'Completed', 'Rejected']

export default function Coordination() {
  const { canWrite } = useAuth()
  const [requests, setRequests] = useState<Coordination[]>([])
  const [complaints, setComplaints] = useState<ComplaintOption[]>([])
  const [bureaus, setBureaus] = useState<BureauOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ complaint_id: '', to_bureau_id: '', reason: '' })
  const [saving, setSaving] = useState(false)
  const [commentFor, setCommentFor] = useState<Coordination | null>(null)
  const [comment, setComment] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [requestResponse, complaintResponse, bureauResponse] = await Promise.all([
        api.get<Coordination[]>('/api/coordination', {
          params: { ...(statusFilter ? { status: statusFilter } : {}), limit: 500 },
        }),
        api.get<ComplaintOption[]>('/api/complaints', { params: { limit: 500 } }),
        api.get<BureauOption[]>('/api/bureaus'),
      ])
      setRequests(requestResponse.data)
      setComplaints(complaintResponse.data)
      setBureaus(bureauResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  const submit = async () => {
    if (!form.complaint_id || !form.to_bureau_id || form.reason.trim().length < 3) {
      toast.error('Select a complaint, destination bureau and enter a reason')
      return
    }
    setSaving(true)
    try {
      const response = await api.post('/api/coordination', {
        complaint_id: form.complaint_id,
        to_bureau_id: form.to_bureau_id,
        reason: form.reason.trim(),
      })
      toast.success(response.data.message || 'Coordination request created')
      setCreateOpen(false)
      setForm({ complaint_id: '', to_bureau_id: '', reason: '' })
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const act = async (label: string, request: () => Promise<{ data: any }>) => {
    setSaving(true)
    try {
      const response = await request()
      toast.success(response.data.message || label)
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const addComment = async () => {
    if (!commentFor || !comment.trim()) {
      toast.error('Enter a comment')
      return
    }
    await act('Comment added', () =>
      api.post(`/api/coordination/${commentFor.id}/comments`, { comment: comment.trim() }),
    )
    setCommentFor(null)
    setComment('')
  }

  const selectedComplaint = complaints.find((item) => item.id === form.complaint_id)
  const pending = requests.filter((request) => request.status === 'Pending').length
  const completed = requests.filter((request) => request.status === 'Completed').length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Case Coordination"
        subtitle="Cross-bureau requests, acknowledgements and resolution"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            {canWrite && (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" /> New request
              </Button>
            )}
          </>
        }
      />

      <ErrorBanner message={error} />

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total requests', value: requests.length, tone: 'text-slate-900' },
          { label: 'Pending', value: pending, tone: 'text-amber-600' },
          { label: 'Completed', value: completed, tone: 'text-green-600' },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {card.label}
            </p>
            <p className={`mt-1 text-2xl font-bold ${card.tone}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Select
          className="w-full max-w-xs"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All statuses</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </Select>
        <p className="text-sm text-slate-500">{requests.length} request(s)</p>
      </div>

      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <LoadingBlock label="Loading coordination requests…" />
        </div>
      ) : requests.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <EmptyState
            title="No coordination requests"
            description="Create a request to involve another bureau in a complaint."
            action={
              canWrite ? (
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" /> New request
                </Button>
              ) : undefined
            }
          />
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {requests.map((request) => (
            <div
              key={request.id}
              className="flex flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-blue-700">
                    {request.complaint_number}
                  </p>
                  <p className="mt-0.5 line-clamp-2 text-sm text-slate-800">
                    {request.complaint_subject}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500">
                    {request.institution || 'Unknown institution'}
                  </p>
                </div>
                <Badge className={reviewStatusClass(request.status)}>{request.status}</Badge>
              </div>

              <div className="mt-3 flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <span className="font-medium">{request.from_bureau || 'Unassigned'}</span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
                <span className="font-medium">{request.to_bureau}</span>
                {request.complaint_status && (
                  <Badge className={`ml-auto ${statusClass(request.complaint_status)}`}>
                    {request.complaint_status}
                  </Badge>
                )}
              </div>

              <p className="mt-2 flex-1 text-xs text-slate-600">{request.reason}</p>

              <div className="mt-3 border-t border-slate-100 pt-2 text-[11px] text-slate-400">
                Requested by {request.requested_by || '—'} ·{' '}
                {formatDateTime(request.created_at)}
                {request.approved_by ? ` · acknowledged by ${request.approved_by}` : ''}
              </div>

              {canWrite && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {request.status === 'Pending' && (
                    <Button
                      size="sm"
                      variant="outline"
                      loading={saving}
                      onClick={() =>
                        void act('Request acknowledged', () =>
                          api.post(`/api/coordination/${request.id}/acknowledge`),
                        )
                      }
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" /> Acknowledge
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setCommentFor(request)
                      setComment('')
                    }}
                  >
                    <MessageSquare className="h-3.5 w-3.5" /> Comment
                  </Button>
                  {request.status !== 'Completed' && (
                    <Button
                      size="sm"
                      variant="success"
                      loading={saving}
                      onClick={() =>
                        void act('Coordination resolved', () =>
                          api.post(`/api/coordination/${request.id}/resolve`),
                        )
                      }
                    >
                      <Users className="h-3.5 w-3.5" /> Resolve
                    </Button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New coordination request"
        description="Ask another bureau to jointly review or take over a complaint."
        footer={
          <>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button loading={saving} onClick={() => void submit()}>
              Create request
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Complaint" required>
            <Select
              value={form.complaint_id}
              onChange={(event) =>
                setForm({ ...form, complaint_id: event.target.value, to_bureau_id: '' })
              }
            >
              <option value="">Select a complaint…</option>
              {complaints.map((complaint) => (
                <option key={complaint.id} value={complaint.id}>
                  {complaint.complaint_number} — {complaint.subject}
                </option>
              ))}
            </Select>
          </Field>
          {selectedComplaint && (
            <p className="text-xs text-slate-500">
              Current bureau: {selectedComplaint.assigned_bureau || 'Unassigned'} · Status:{' '}
              {selectedComplaint.current_status || '—'}
            </p>
          )}
          <Field label="Destination bureau" required>
            <Select
              value={form.to_bureau_id}
              onChange={(event) => setForm({ ...form, to_bureau_id: event.target.value })}
            >
              <option value="">Select bureau…</option>
              {bureaus
                .filter((bureau) => isOtherBureau(bureau.id, selectedComplaint))
                .map((bureau) => (
                  <option key={bureau.id} value={bureau.id}>
                    {bureau.bureau_code} — {bureau.bureau_name}
                  </option>
                ))}
            </Select>
          </Field>
          <Field label="Reason" required>
            <Textarea
              value={form.reason}
              onChange={(event) => setForm({ ...form, reason: event.target.value })}
              placeholder="Explain why cross-bureau coordination is required…"
            />
          </Field>
        </div>
      </Modal>

      <Modal
        open={Boolean(commentFor)}
        onClose={() => setCommentFor(null)}
        title="Add coordination comment"
        description={commentFor?.complaint_number || undefined}
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setCommentFor(null)}>
              Cancel
            </Button>
            <Button loading={saving} onClick={() => void addComment()}>
              Add comment
            </Button>
          </>
        }
      >
        <Field label="Comment" required>
          <Textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Add context for both bureaus…"
          />
        </Field>
      </Modal>
    </div>
  )
}

function isOtherBureau(bureauId: string, complaint: ComplaintOption | undefined) {
  if (!complaint) return true
  return bureauId !== complaint.assigned_bureau_id
}
