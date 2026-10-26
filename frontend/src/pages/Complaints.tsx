import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowRightLeft,
  CheckCircle2,
  ClipboardList,
  FilePlus2,
  GitBranch,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  UserCheck,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  addDaysISO,
  formatDate,
  formatDateTime,
  priorityClass,
  statusClass,
  todayISO,
} from '../lib/utils'
import {
  Badge,
  Button,
  DetailRow,
  EmptyState,
  ErrorBanner,
  Field,
  Input,
  LoadingBlock,
  Modal,
  PageHeader,
  Select,
  Textarea,
} from '../components/ui'

interface Complaint {
  id: string
  complaint_number: string
  institution_id: string
  institution_name: string | null
  category: string
  subcategory: string | null
  subject: string
  description: string
  current_status: string | null
  priority: string | null
  received_date: string
  source_channel: string | null
  complainant_reference: string | null
  assigned_bureau_id: string | null
  assigned_bureau: string | null
  assigned_officer_id: string | null
  assigned_officer: string | null
  expected_disposal_date: string | null
  disposed_at: string | null
  last_action_at: string | null
  next_action: string | null
  is_overdue: boolean
}

interface CaseAction {
  id: string
  action_type: string
  previous_status: string | null
  new_status: string | null
  remarks: string
  officer: string | null
  bureau: string | null
  timestamp: string | null
}

interface Transfer {
  id: string
  from_bureau: string | null
  to_bureau: string | null
  reason: string
  status: string | null
  requested_by: string | null
  created_at: string | null
}

interface RelatedCase {
  id: string
  complaint_number: string | null
  subject: string | null
  relationship_type: string | null
  similarity_score: number | null
  review_status: string | null
  matching_reasons: string | null
}

interface ComplaintDetail extends Complaint {
  institution: {
    id: string
    name: string
    aicte_permanent_id: string | null
    region: string | null
    state: string | null
  }
  actions: CaseAction[]
  transfers: Transfer[]
  related_cases: RelatedCase[]
}

interface InstitutionOption {
  id: string
  institution_name: string
}

interface BureauOption {
  id: string
  bureau_code: string
  bureau_name: string
}

interface OfficerOption {
  id: string
  full_name: string
  role: string
  bureau_name: string | null
}

const statuses = [
  'Received',
  'Under Scrutiny',
  'Under Process',
  'Awaiting Information',
  'Transferred',
  'Escalated',
  'Disposed',
  'Closed',
]

const priorities = ['Low', 'Medium', 'High', 'Urgent']

const categories = [
  'Faculty Related',
  'Infrastructure',
  'Fee Structure',
  'Admission',
  'Examination',
  'Affiliation',
  'Governance',
  'Other',
]

const channels = ['Online Portal', 'Email', 'Letter', 'Phone', 'In Person']

const emptyForm = {
  institution_id: '',
  category: 'Infrastructure',
  subcategory: '',
  subject: '',
  description: '',
  received_date: todayISO(),
  source_channel: 'Online Portal',
  priority: 'Medium',
  assigned_bureau_id: '',
  assigned_officer_id: '',
  expected_disposal_date: addDaysISO(30),
  next_action: '',
}

type DetailTab = 'overview' | 'action' | 'assign' | 'transfer' | 'dispose'

export default function Complaints() {
  const { canWrite } = useAuth()
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [institutions, setInstitutions] = useState<InstitutionOption[]>([])
  const [bureaus, setBureaus] = useState<BureauOption[]>([])
  const [officers, setOfficers] = useState<OfficerOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [bureauFilter, setBureauFilter] = useState('')
  const [overdueOnly, setOverdueOnly] = useState(false)

  const [addOpen, setAddOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [institutionQuery, setInstitutionQuery] = useState('')
  const [saving, setSaving] = useState(false)
  const [liveWarning, setLiveWarning] = useState<string | null>(null)

  // Break Glass
  const [breakGlassOpen, setBreakGlassOpen] = useState(false)
  const [breakGlassReason, setBreakGlassReason] = useState('')
  const [breakGlassLoading, setBreakGlassLoading] = useState(false)

  // Natural Language Search
  const [nlQuery, setNlQuery] = useState('')
  const [nlLoading, setNlLoading] = useState(false)

  // Pre-save overlap live warning check
  useEffect(() => {
    if (!form.institution_id) {
      setLiveWarning(null)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await api.post('/api/complaints/check-overlap-live', {
          institution_id: form.institution_id,
          category: form.category,
          subject: form.subject,
        })
        if (res.data.has_conflicts && res.data.warnings && res.data.warnings.length > 0) {
          setLiveWarning(res.data.warnings[0].message)
        } else {
          setLiveWarning(null)
        }
      } catch {
        setLiveWarning(null)
      }
    }, 350)
    return () => clearTimeout(timer)
  }, [form.institution_id, form.category, form.subject])

  const [detail, setDetail] = useState<ComplaintDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [tab, setTab] = useState<DetailTab>('overview')

  const [actionForm, setActionForm] = useState({
    action_type: 'Case Update',
    new_status: '',
    remarks: '',
    next_action: '',
  })
  const [assignForm, setAssignForm] = useState({
    bureau_id: '',
    officer_id: '',
    remarks: '',
  })
  const [transferForm, setTransferForm] = useState({ to_bureau_id: '', reason: '' })
  const [disposeForm, setDisposeForm] = useState({ disposal_outcome: 'Resolved', remarks: '' })
  const [busy, setBusy] = useState(false)

  const loadLookups = useCallback(async () => {
    try {
      const [institutionResponse, bureauResponse, officerResponse] = await Promise.all([
        api.get<InstitutionOption[]>('/api/institutions', { params: { limit: 500 } }),
        api.get<BureauOption[]>('/api/bureaus'),
        api.get<OfficerOption[]>('/api/users/officers'),
      ])
      setInstitutions(institutionResponse.data)
      setBureaus(bureauResponse.data)
      setOfficers(officerResponse.data)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<Complaint[]>('/api/complaints', {
        params: {
          limit: 500,
          ...(search.trim() ? { search: search.trim() } : {}),
          ...(statusFilter ? { status: statusFilter } : {}),
          ...(priorityFilter ? { priority: priorityFilter } : {}),
          ...(bureauFilter ? { bureau_id: bureauFilter } : {}),
          ...(overdueOnly ? { overdue_only: true } : {}),
        },
      })
      setComplaints(response.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, priorityFilter, bureauFilter, overdueOnly])

  useEffect(() => {
    void loadLookups()
  }, [loadLookups])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 300)
    return () => window.clearTimeout(timer)
  }, [load])

  const officersForBureau = useMemo(() => {
    if (!assignForm.bureau_id) return officers
    return officers.filter((officer) => {
      const bureau = bureaus.find((b) => b.id === assignForm.bureau_id)
      return officer.bureau_name === bureau?.bureau_name
    })
  }, [assignForm.bureau_id, officers, bureaus])

  const filteredInstitutions = useMemo(() => {
    const term = institutionQuery.trim().toLowerCase()
    if (!term) return institutions
    return institutions.filter((institution) =>
      institution.institution_name.toLowerCase().includes(term),
    )
  }, [institutions, institutionQuery])

  const openComplaintModal = () => {
    setForm(emptyForm)
    setInstitutionQuery('')
    setAddOpen(true)
  }

  const submitComplaint = async () => {
    if (!form.institution_id) {
      toast.error('Select an institution')
      return
    }
    if (form.subject.trim().length < 3) {
      toast.error('Subject must be at least 3 characters')
      return
    }
    if (form.description.trim().length < 5) {
      toast.error('Description must be at least 5 characters')
      return
    }
    setSaving(true)
    try {
      const response = await api.post('/api/complaints', {
        institution_id: form.institution_id,
        category: form.category,
        subcategory: form.subcategory.trim() || null,
        subject: form.subject.trim(),
        description: form.description.trim(),
        received_date: form.received_date || null,
        source_channel: form.source_channel,
        priority: form.priority,
        assigned_bureau_id: form.assigned_bureau_id || null,
        assigned_officer_id: form.assigned_officer_id || null,
        expected_disposal_date: form.expected_disposal_date || null,
        next_action: form.next_action.trim() || null,
      })
      toast.success(
        response.data.overlap_suggestions
          ? `Complaint ${response.data.complaint_number} registered · ${response.data.overlap_suggestions} overlap suggestion(s) found`
          : `Complaint ${response.data.complaint_number} registered`,
      )
      setAddOpen(false)
      setForm(emptyForm)
      setLiveWarning(null)
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handleBreakGlass = async () => {
    if (!detail || !breakGlassReason.trim()) {
      toast.error('Written emergency regulatory reason is required')
      return
    }
    setBreakGlassLoading(true)
    try {
      const res = await api.post<{ message: string }>(`/api/complaints/${detail.id}/break-glass`, {
        reason: breakGlassReason.trim(),
      })
      toast.success(res.data.message)
      setBreakGlassOpen(false)
      setBreakGlassReason('')
      await openDetail(detail.id)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBreakGlassLoading(false)
    }
  }

  const handleNlSearch = async () => {
    if (!nlQuery.trim()) return
    setNlLoading(true)
    try {
      const res = await api.get<{ count: number; parsed_interpretation: string; results: Complaint[] }>(
        '/api/complaints/nl-search',
        { params: { query: nlQuery.trim() } },
      )
      toast.success(`NL Search: ${res.data.parsed_interpretation} (${res.data.count} found)`)
      setComplaints(res.data.results)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setNlLoading(false)
    }
  }

  const openDetail = useCallback(async (id: string) => {
    setDetailLoading(true)
    setTab('overview')
    try {
      const response = await api.get<ComplaintDetail>(`/api/complaints/${id}`)
      setDetail(response.data)
      setActionForm({
        action_type: 'Case Update',
        new_status: response.data.current_status || '',
        remarks: '',
        next_action: response.data.next_action || '',
      })
      setAssignForm({
        bureau_id: response.data.assigned_bureau_id || '',
        officer_id: response.data.assigned_officer_id || '',
        remarks: '',
      })
      setTransferForm({ to_bureau_id: '', reason: '' })
      setDisposeForm({ disposal_outcome: 'Resolved', remarks: '' })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const refreshDetail = async () => {
    if (detail) await openDetail(detail.id)
  }

  const perform = async (
    label: string,
    request: () => Promise<{ data: any }>,
    after?: () => void,
  ) => {
    setBusy(true)
    try {
      const response = await request()
      toast.success(response.data?.message || label)
      after?.()
      await refreshDetail()
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const activeCount = complaints.length
  const overdueCount = complaints.filter((c) => c.is_overdue).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Complaint Registry"
        subtitle="Register, assign, track and dispose institution complaints"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            {canWrite && (
              <Button onClick={openComplaintModal}>
                <FilePlus2 className="h-4 w-4" /> Register Complaint
              </Button>
            )}
          </>
        }
      />

      <ErrorBanner message={error} />

      {/* Natural Language Search Input (Section 5.E) */}
      <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3 shadow-2xs flex flex-wrap items-center gap-2">
        <Sparkles className="h-4 w-4 text-blue-600 shrink-0 ml-1" />
        <span className="text-xs font-bold text-blue-900 shrink-0">Ask AICTE Intelligence:</span>
        <input
          type="text"
          value={nlQuery}
          onChange={(e) => setNlQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void handleNlSearch()}
          placeholder="e.g. pending fee complaints in Maharashtra older than 30 days"
          className="flex-1 min-w-[260px] rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 focus:outline-blue-500"
        />
        <Button
          size="sm"
          onClick={handleNlSearch}
          loading={nlLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
        >
          Parse & Filter
        </Button>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <div className="relative xl:col-span-2">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              className="pl-9"
              placeholder="Search number, subject, institution…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
          <Select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="">All priorities</option>
            {priorities.map((priority) => (
              <option key={priority} value={priority}>
                {priority}
              </option>
            ))}
          </Select>
          <Select value={bureauFilter} onChange={(e) => setBureauFilter(e.target.value)}>
            <option value="">All bureaus</option>
            {bureaus.map((bureau) => (
              <option key={bureau.id} value={bureau.id}>
                {bureau.bureau_code} — {bureau.bureau_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300"
              checked={overdueOnly}
              onChange={(event) => setOverdueOnly(event.target.checked)}
            />
            Overdue only
          </label>
          <p className="text-sm text-slate-500">
            {activeCount} complaint{activeCount === 1 ? '' : 's'} shown
            {overdueCount > 0 ? ` · ${overdueCount} overdue` : ''}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <LoadingBlock label="Loading complaints…" />
        ) : complaints.length === 0 ? (
          <EmptyState
            title="No complaints match your filters"
            description="Adjust the filters or register a new complaint."
            action={
              canWrite ? (
                <Button onClick={openComplaintModal}>
                  <FilePlus2 className="h-4 w-4" /> Register Complaint
                </Button>
              ) : undefined
            }
          />
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                {['Complaint', 'Institution', 'Category', 'Priority', 'Status', 'Bureau', 'Due', ''].map(
                  (heading) => (
                    <th
                      key={heading}
                      className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {complaints.map((complaint) => (
                <tr key={complaint.id} className="align-top hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-blue-700">{complaint.complaint_number}</p>
                    <p className="mt-0.5 line-clamp-2 max-w-xs text-xs text-slate-600">
                      {complaint.subject}
                    </p>
                    {complaint.is_overdue && (
                      <span className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-red-600">
                        <AlertTriangle className="h-3 w-3" /> Overdue
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {complaint.institution_name || '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{complaint.category}</td>
                  <td className="px-4 py-3">
                    <Badge className={priorityClass(complaint.priority)}>
                      {complaint.priority || '—'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={statusClass(complaint.current_status)}>
                      {complaint.current_status || '—'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {complaint.assigned_bureau || 'Unassigned'}
                    {complaint.assigned_officer && (
                      <p className="text-[11px] text-slate-400">{complaint.assigned_officer}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    <p>{formatDate(complaint.expected_disposal_date)}</p>
                    <p className="text-[11px] text-slate-400">
                      received {formatDate(complaint.received_date)}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="sm" onClick={() => void openDetail(complaint.id)}>
                      Open
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Register complaint */}
      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Register complaint"
        description="Every complaint must be linked to a registered institution."
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => void submitComplaint()} loading={saving}>
              Register complaint
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          {liveWarning && (
            <div className="sm:col-span-2 rounded-xl border border-amber-300 bg-amber-50 p-3.5">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-900 mb-1">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                Live Overlap Engine Alert: Active Case on College
              </div>
              <p className="text-xs text-amber-800 font-medium">{liveWarning}</p>
              <p className="text-[11px] text-amber-700 mt-1 italic">
                Samanvay automatically links cross-bureau cases into a Coordination Room upon submission without merging separate mandates.
              </p>
            </div>
          )}
          <Field label="Institution" required className="sm:col-span-2">
            <Input
              value={institutionQuery}
              onChange={(event) => setInstitutionQuery(event.target.value)}
              placeholder="Type to filter institutions…"
              className="mb-2"
            />
            <Select
              value={form.institution_id}
              onChange={(event) => setForm({ ...form, institution_id: event.target.value })}
            >
              <option value="">Select an institution…</option>
              {form.institution_id &&
                !filteredInstitutions.some((item) => item.id === form.institution_id) && (
                  <option value={form.institution_id}>
                    {institutions.find((item) => item.id === form.institution_id)
                      ?.institution_name || 'Selected institution'}
                  </option>
                )}
              {filteredInstitutions.map((institution) => (
                <option key={institution.id} value={institution.id}>
                  {institution.institution_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Category" required>
            <Select
              value={form.category}
              onChange={(event) => setForm({ ...form, category: event.target.value })}
            >
              {categories.map((category) => (
                <option key={category}>{category}</option>
              ))}
            </Select>
          </Field>
          <Field label="Sub-category">
            <Input
              value={form.subcategory}
              onChange={(event) => setForm({ ...form, subcategory: event.target.value })}
              placeholder="Optional sub-category"
            />
          </Field>
          <Field label="Subject" required className="sm:col-span-2">
            <Input
              value={form.subject}
              onChange={(event) => setForm({ ...form, subject: event.target.value })}
              placeholder="Short summary of the complaint"
            />
          </Field>
          <Field label="Description" required className="sm:col-span-2">
            <Textarea
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Describe the complaint in detail…"
            />
          </Field>
          <Field label="Received date" required>
            <Input
              type="date"
              max={todayISO()}
              value={form.received_date}
              onChange={(event) => setForm({ ...form, received_date: event.target.value })}
            />
          </Field>
          <Field label="Expected disposal date">
            <Input
              type="date"
              value={form.expected_disposal_date}
              onChange={(event) =>
                setForm({ ...form, expected_disposal_date: event.target.value })
              }
            />
          </Field>
          <Field label="Priority">
            <Select
              value={form.priority}
              onChange={(event) => setForm({ ...form, priority: event.target.value })}
            >
              {priorities.map((priority) => (
                <option key={priority}>{priority}</option>
              ))}
            </Select>
          </Field>
          <Field label="Source channel">
            <Select
              value={form.source_channel}
              onChange={(event) => setForm({ ...form, source_channel: event.target.value })}
            >
              {channels.map((channel) => (
                <option key={channel}>{channel}</option>
              ))}
            </Select>
          </Field>
          <Field label="Assign to bureau">
            <Select
              value={form.assigned_bureau_id}
              onChange={(event) =>
                setForm({ ...form, assigned_bureau_id: event.target.value, assigned_officer_id: '' })
              }
            >
              <option value="">Unassigned</option>
              {bureaus.map((bureau) => (
                <option key={bureau.id} value={bureau.id}>
                  {bureau.bureau_code} — {bureau.bureau_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Assign to officer">
            <Select
              value={form.assigned_officer_id}
              onChange={(event) => setForm({ ...form, assigned_officer_id: event.target.value })}
            >
              <option value="">Unassigned</option>
              {officers
                .filter(
                  (officer) =>
                    !form.assigned_bureau_id ||
                    officer.bureau_name ===
                      bureaus.find((b) => b.id === form.assigned_bureau_id)?.bureau_name,
                )
                .map((officer) => (
                  <option key={officer.id} value={officer.id}>
                    {officer.full_name} ({officer.role})
                  </option>
                ))}
            </Select>
          </Field>
          <Field label="Next action" className="sm:col-span-2">
            <Input
              value={form.next_action}
              onChange={(event) => setForm({ ...form, next_action: event.target.value })}
              placeholder="e.g. Initial scrutiny"
            />
          </Field>
        </div>
      </Modal>

      {/* Detail */}
      <Modal
        open={Boolean(detail) || detailLoading}
        onClose={() => {
          setDetail(null)
          setDetailLoading(false)
        }}
        title={detail ? `${detail.complaint_number} · ${detail.subject}` : 'Complaint'}
        description={detail?.institution?.name || 'Loading complaint…'}
        size="xl"
      >
        {detailLoading && !detail ? (
          <LoadingBlock label="Loading complaint…" />
        ) : detail ? (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={statusClass(detail.current_status)}>
                {detail.current_status}
              </Badge>
              <Badge className={priorityClass(detail.priority)}>{detail.priority}</Badge>
              {detail.is_overdue && (
                <Badge className="bg-red-100 text-red-800">
                  <AlertTriangle className="mr-1 h-3 w-3" /> Overdue
                </Badge>
              )}
              <span className="text-xs text-slate-500">
                Received {formatDate(detail.received_date)} · Due{' '}
                {formatDate(detail.expected_disposal_date)}
              </span>
            </div>

            <div className="flex flex-wrap gap-1 rounded-lg bg-slate-100 p-1">
              {(
                [
                  ['overview', 'Overview'],
                  ['action', 'Update / Status'],
                  ['assign', 'Assign'],
                  ['transfer', 'Transfer / Coordinate'],
                  ['dispose', 'Dispose'],
                ] as Array<[DetailTab, string]>
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setTab(value)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    tab === value
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {tab === 'overview' && (
              <div className="space-y-5">
                {(detail.description?.includes('[CONFIDENTIAL') || (detail as unknown as { access_level?: string }).access_level === 'L1_MASKED') && (
                  <div className="rounded-xl border border-red-300 bg-red-50 p-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h4 className="text-xs font-bold text-red-950 flex items-center gap-1.5">
                        <ShieldAlert className="h-4 w-4 text-red-600" />
                        ABAC Need-to-Know Security: Sensitive Complaint Content Masked (L1 Visibility)
                      </h4>
                      <p className="text-[11px] text-red-800 mt-0.5">
                        Categories like Ragging, Whistleblower and Harassment require formal access approval or emergency Break-Glass override.
                      </p>
                    </div>
                    <Button
                      size="sm"
                      className="bg-red-700 hover:bg-red-800 text-white font-bold text-xs"
                      onClick={() => setBreakGlassOpen(true)}
                    >
                      Break-Glass Emergency Access
                    </Button>
                  </div>
                )}
                <dl className="grid gap-4 sm:grid-cols-3">
                  <DetailRow label="Institution" value={detail.institution?.name} />
                  <DetailRow label="Category" value={detail.category} />
                  <DetailRow label="Sub-category" value={detail.subcategory || '—'} />
                  <DetailRow label="Bureau" value={detail.assigned_bureau || 'Unassigned'} />
                  <DetailRow label="Officer" value={detail.assigned_officer || 'Unassigned'} />
                  <DetailRow label="Source" value={detail.source_channel || '—'} />
                  <DetailRow label="Next action" value={detail.next_action || '—'} />
                  <DetailRow label="Last action" value={formatDateTime(detail.last_action_at)} />
                  <DetailRow label="Disposed at" value={formatDateTime(detail.disposed_at)} />
                </dl>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Description</h3>
                  <p className="mt-1 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm text-slate-700">
                    {detail.description}
                  </p>
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                  <div>
                    <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <ClipboardList className="h-4 w-4" /> Case history
                    </h3>
                    {detail.actions.length === 0 ? (
                      <p className="text-sm text-slate-500">No actions recorded.</p>
                    ) : (
                      <ol className="space-y-3 border-l border-slate-200 pl-4">
                        {detail.actions.map((action) => (
                          <li key={action.id} className="relative">
                            <span className="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-slate-400" />
                            <p className="text-sm font-medium text-slate-800">
                              {action.action_type}
                            </p>
                            <p className="text-xs text-slate-600">{action.remarks}</p>
                            <p className="mt-0.5 text-[11px] text-slate-400">
                              {action.officer || 'System'} · {formatDateTime(action.timestamp)}
                              {action.previous_status && action.new_status
                                ? ` · ${action.previous_status} → ${action.new_status}`
                                : ''}
                            </p>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>

                  <div className="space-y-5">
                    <div>
                      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                        <GitBranch className="h-4 w-4" /> Related cases
                      </h3>
                      {detail.related_cases.length === 0 ? (
                        <p className="text-sm text-slate-500">
                          No related cases yet. Run matching to look for overlaps.
                        </p>
                      ) : (
                        <ul className="space-y-2">
                          {detail.related_cases.map((related) => (
                            <li
                              key={related.id}
                              className="rounded-md border border-slate-200 p-2.5 text-sm"
                            >
                              <p className="font-medium text-blue-700">
                                {related.complaint_number}
                              </p>
                              <p className="line-clamp-1 text-xs text-slate-600">
                                {related.subject}
                              </p>
                              <p className="text-[11px] text-slate-400">
                                {related.relationship_type} ·{' '}
                                {related.similarity_score
                                  ? `${Math.round(related.similarity_score * 100)}%`
                                  : 'n/a'}{' '}
                                · {related.review_status}
                              </p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div>
                      <h3 className="mb-2 text-sm font-semibold text-slate-900">Transfers</h3>
                      {detail.transfers.length === 0 ? (
                        <p className="text-sm text-slate-500">No transfer requests.</p>
                      ) : (
                        <ul className="space-y-2">
                          {detail.transfers.map((transfer) => (
                            <li
                              key={transfer.id}
                              className="rounded-md border border-slate-200 p-2.5 text-sm"
                            >
                              <p className="text-slate-800">
                                {transfer.from_bureau} → {transfer.to_bureau}
                              </p>
                              <p className="text-xs text-slate-600">{transfer.reason}</p>
                              <p className="text-[11px] text-slate-400">
                                {transfer.status} · {formatDate(transfer.created_at)}
                              </p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>

                {canWrite && (
                  <Button
                    variant="outline"
                    loading={busy}
                    onClick={() =>
                      void perform(
                        'Matching completed',
                        () => api.post(`/api/complaints/${detail.id}/run-matching`),
                      )
                    }
                  >
                    <GitBranch className="h-4 w-4" /> Run overlap matching
                  </Button>
                )}
              </div>
            )}

            {tab === 'action' && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Action type">
                    <Input
                      value={actionForm.action_type}
                      onChange={(event) =>
                        setActionForm({ ...actionForm, action_type: event.target.value })
                      }
                    />
                  </Field>
                  <Field label="New status">
                    <Select
                      value={actionForm.new_status}
                      onChange={(event) =>
                        setActionForm({ ...actionForm, new_status: event.target.value })
                      }
                    >
                      {statuses.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Remarks" required className="sm:col-span-2">
                    <Textarea
                      value={actionForm.remarks}
                      onChange={(event) =>
                        setActionForm({ ...actionForm, remarks: event.target.value })
                      }
                      placeholder="What was done on this case?"
                    />
                  </Field>
                  <Field label="Next action" className="sm:col-span-2">
                    <Input
                      value={actionForm.next_action}
                      onChange={(event) =>
                        setActionForm({ ...actionForm, next_action: event.target.value })
                      }
                      placeholder="Set the next step (optional)"
                    />
                  </Field>
                </div>
                <Button
                  loading={busy}
                  onClick={() =>
                    void perform(
                      'Action recorded',
                      () =>
                        api.post(`/api/complaints/${detail.id}/actions`, {
                          action_type: actionForm.action_type || 'Case Update',
                          remarks: actionForm.remarks,
                          new_status: actionForm.new_status || null,
                          next_action: actionForm.next_action || null,
                        }),
                      () => setActionForm({ ...actionForm, remarks: '' }),
                    )
                  }
                >
                  <CheckCircle2 className="h-4 w-4" /> Record action
                </Button>
              </div>
            )}

            {tab === 'assign' && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Bureau">
                    <Select
                      value={assignForm.bureau_id}
                      onChange={(event) =>
                        setAssignForm({ ...assignForm, bureau_id: event.target.value, officer_id: '' })
                      }
                    >
                      <option value="">Select a bureau…</option>
                      {bureaus.map((bureau) => (
                        <option key={bureau.id} value={bureau.id}>
                          {bureau.bureau_code} — {bureau.bureau_name}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Officer">
                    <Select
                      value={assignForm.officer_id}
                      onChange={(event) =>
                        setAssignForm({ ...assignForm, officer_id: event.target.value })
                      }
                    >
                      <option value="">Select an officer…</option>
                      {officersForBureau.map((officer) => (
                        <option key={officer.id} value={officer.id}>
                          {officer.full_name} ({officer.role})
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Remarks" className="sm:col-span-2">
                    <Input
                      value={assignForm.remarks}
                      onChange={(event) =>
                        setAssignForm({ ...assignForm, remarks: event.target.value })
                      }
                      placeholder="Assignment note (optional)"
                    />
                  </Field>
                </div>
                <Button
                  loading={busy}
                  onClick={() =>
                    void perform('Complaint assigned', () =>
                      api.post(`/api/complaints/${detail.id}/assign`, {
                        bureau_id: assignForm.bureau_id || null,
                        officer_id: assignForm.officer_id || null,
                        remarks: assignForm.remarks || null,
                      }),
                    )
                  }
                >
                  <UserCheck className="h-4 w-4" /> Assign complaint
                </Button>
              </div>
            )}

            {tab === 'transfer' && (
              <div className="space-y-5">
                <div className="rounded-md border border-slate-200 p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    <ArrowRightLeft className="h-4 w-4" /> Request transfer
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    A transfer request is created for the destination bureau to review.
                  </p>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">
                    <Field label="Destination bureau" required>
                      <Select
                        value={transferForm.to_bureau_id}
                        onChange={(event) =>
                          setTransferForm({ ...transferForm, to_bureau_id: event.target.value })
                        }
                      >
                        <option value="">Select bureau…</option>
                        {bureaus
                          .filter((bureau) => bureau.id !== detail.assigned_bureau_id)
                          .map((bureau) => (
                            <option key={bureau.id} value={bureau.id}>
                              {bureau.bureau_code} — {bureau.bureau_name}
                            </option>
                          ))}
                      </Select>
                    </Field>
                    <Field label="Reason" required>
                      <Input
                        value={transferForm.reason}
                        onChange={(event) =>
                          setTransferForm({ ...transferForm, reason: event.target.value })
                        }
                        placeholder="Why should this case move?"
                      />
                    </Field>
                  </div>
                  <Button
                    className="mt-3"
                    loading={busy}
                    onClick={() =>
                      void perform(
                        'Transfer requested',
                        () =>
                          api.post(`/api/complaints/${detail.id}/transfer`, {
                            to_bureau_id: transferForm.to_bureau_id,
                            reason: transferForm.reason,
                          }),
                        () => setTransferForm({ to_bureau_id: '', reason: '' }),
                      )
                    }
                  >
                    Request transfer
                  </Button>
                </div>

                <div className="rounded-md border border-red-200 bg-red-50/40 p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-red-800">
                    <AlertTriangle className="h-4 w-4" /> Escalate complaint
                  </h3>
                  <p className="mt-1 text-xs text-red-700">
                    Escalation notifies all super administrators and bureau administrators.
                  </p>
                  <div className="mt-3">
                    <Field label="Escalation reason" required>
                      <Input
                        value={transferForm.reason}
                        onChange={(event) =>
                          setTransferForm({ ...transferForm, reason: event.target.value })
                        }
                        placeholder="Reason for escalation"
                      />
                    </Field>
                  </div>
                  <Button
                    variant="danger"
                    className="mt-3"
                    loading={busy}
                    onClick={() =>
                      void perform(
                        'Complaint escalated',
                        () =>
                          api.post(`/api/complaints/${detail.id}/escalate`, {
                            reason: transferForm.reason,
                          }),
                        () => setTransferForm({ ...transferForm, reason: '' }),
                      )
                    }
                  >
                    <AlertTriangle className="h-4 w-4" /> Escalate
                  </Button>
                </div>
              </div>
            )}

            {tab === 'dispose' && (
              <div className="space-y-4">
                {detail.current_status === 'Disposed' || detail.current_status === 'Closed' ? (
                  <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-800">
                    This complaint was already disposed on {formatDateTime(detail.disposed_at)}.
                  </div>
                ) : (
                  <>
                    <Field label="Disposal outcome">
                      <Select
                        value={disposeForm.disposal_outcome}
                        onChange={(event) =>
                          setDisposeForm({ ...disposeForm, disposal_outcome: event.target.value })
                        }
                      >
                        {[
                          'Resolved',
                          'Partially Resolved',
                          'No Action Required',
                          'Referred',
                          'Closed',
                        ].map((outcome) => (
                          <option key={outcome}>{outcome}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Disposal remarks" required>
                      <Textarea
                        value={disposeForm.remarks}
                        onChange={(event) =>
                          setDisposeForm({ ...disposeForm, remarks: event.target.value })
                        }
                        placeholder="Describe the resolution and evidence considered…"
                      />
                    </Field>
                    <Button
                      variant="success"
                      loading={busy}
                      onClick={() =>
                        void perform('Complaint disposed', () =>
                          api.post(`/api/complaints/${detail.id}/dispose`, {
                            remarks: disposeForm.remarks,
                            disposal_outcome: disposeForm.disposal_outcome,
                          }),
                        )
                      }
                    >
                      <CheckCircle2 className="h-4 w-4" /> Dispose complaint
                    </Button>
                  </>
                )}
              </div>
            )}
          </div>
        ) : null}
      </Modal>
      {/* Break-Glass Emergency Override Modal */}
      {breakGlassOpen && (
        <div className="fixed inset-0 z-70 flex items-center justify-center bg-black/60 p-4 backdrop-blur-2xs">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl border border-red-300">
            <div className="flex items-center gap-2 text-red-700 font-bold mb-2">
              <ShieldAlert className="h-5 w-5" />
              Emergency Need-to-Know Break-Glass Protocol
            </div>
            <p className="text-xs text-slate-600 mb-3">
              Section 3 ABAC Security: Emergency access requires an explicit written regulatory justification.
              This access is cryptographically recorded with your IP address and flagged for immediate Auditor review.
            </p>
            <div className="mb-4">
              <label className="text-xs font-semibold text-slate-800">Regulatory Exigency Reason *</label>
              <textarea
                rows={3}
                placeholder="e.g. Emergency regulatory inspection ordered by Central Vigilance Commission / High Court summon..."
                value={breakGlassReason}
                onChange={(e) => setBreakGlassReason(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 p-2 text-xs focus:outline-red-500"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setBreakGlassOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-red-700 hover:bg-red-800 text-white font-bold"
                onClick={handleBreakGlass}
                loading={breakGlassLoading}
              >
                Confirm Break-Glass Access
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
