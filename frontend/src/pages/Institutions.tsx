import { useCallback, useEffect, useState } from 'react'
import { Building2, Eye, Plus, Search } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { formatDate } from '../lib/utils'
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

interface Institution {
  id: string
  institution_name: string
  aicte_permanent_id: string | null
  institution_type: string | null
  region: string | null
  state: string | null
  city: string | null
  district: string | null
  address: string | null
  contact_email: string | null
  website: string | null
  established_year: number | null
  ownership: string | null
  affiliation: string | null
  institution_status: string | null
  complaint_count: number
  created_at: string | null
}

interface InstitutionComplaint {
  id: string
  complaint_number: string
  subject: string
  category: string
  current_status: string
  priority: string
  received_date: string
  assigned_bureau: string | null
}

const emptyForm = {
  institution_name: '',
  aicte_permanent_id: '',
  institution_type: 'Engineering',
  region: 'West',
  state: '',
  city: '',
  district: '',
  address: '',
  contact_email: '',
  website: '',
  established_year: '',
  ownership: 'Private',
  affiliation: '',
}

const types = [
  'Engineering',
  'Polytechnic',
  'Management',
  'University',
  'Deemed University',
  'Other',
]
const ownerships = ['Government', 'Government-aided', 'Private', 'Private-aided', 'Deemed University']
const regions = ['West', 'South', 'North', 'East', 'Central', 'Northeast']

export default function Institutions() {
  const { canWrite } = useAuth()
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [detail, setDetail] = useState<Institution | null>(null)
  const [detailComplaints, setDetailComplaints] = useState<InstitutionComplaint[]>([])
  const [detailLoading, setDetailLoading] = useState(false)

  const load = useCallback(async (term = '') => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<Institution[]>('/api/institutions', {
        params: { limit: 500, ...(term ? { search: term } : {}) },
      })
      setInstitutions(response.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(search.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [search, load])

  const submit = async () => {
    if (!form.institution_name.trim()) {
      toast.error('Institution name is required')
      return
    }
    setSaving(true)
    try {
      await api.post('/api/institutions', {
        ...form,
        aicte_permanent_id: form.aicte_permanent_id.trim() || null,
        state: form.state.trim() || null,
        city: form.city.trim() || null,
        district: form.district.trim() || null,
        address: form.address.trim() || null,
        contact_email: form.contact_email.trim() || null,
        website: form.website.trim() || null,
        affiliation: form.affiliation.trim() || null,
        established_year: form.established_year ? Number(form.established_year) : null,
      })
      toast.success('Institution registered successfully')
      setAddOpen(false)
      setForm(emptyForm)
      await load(search.trim())
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const openDetail = async (institution: Institution) => {
    setDetail(institution)
    setDetailComplaints([])
    setDetailLoading(true)
    try {
      const [detailResponse, complaintsResponse] = await Promise.all([
        api.get<Institution>(`/api/institutions/${institution.id}`),
        api.get<InstitutionComplaint[]>(`/api/institutions/${institution.id}/complaints`),
      ])
      setDetail(detailResponse.data)
      setDetailComplaints(complaintsResponse.data)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Institution Registry"
        subtitle="Curated catalog of all 23 IITs and 133 major Maharashtra institutions, with full contact and affiliation details"
        actions={
          canWrite ? (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Add Institution
            </Button>
          ) : null
        }
      />

      <ErrorBanner message={error} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            placeholder="Search by name, AICTE ID or city…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <p className="text-sm text-slate-500">
          {institutions.length} institution{institutions.length === 1 ? '' : 's'} found
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <LoadingBlock label="Loading institutions…" />
        ) : institutions.length === 0 ? (
          <EmptyState
            title="No institutions found"
            description="Add an institution to begin registering complaints."
            action={
              canWrite ? (
                <Button onClick={() => setAddOpen(true)}>
                  <Plus className="h-4 w-4" /> Add Institution
                </Button>
              ) : undefined
            }
          />
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                {['Institution Name', 'AICTE ID', 'Type', 'Region', 'State', 'Complaints', ''].map(
                  (heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                    >
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {institutions.map((institution) => (
                <tr key={institution.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-blue-50 p-1.5 text-blue-600">
                        <Building2 className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="font-medium text-slate-900">{institution.institution_name}</p>
                        <p className="text-xs text-slate-500">
                          {institution.city || '—'}
                          {institution.contact_email ? ` · ${institution.contact_email}` : ''}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {institution.aicte_permanent_id || '—'}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    <p>{institution.institution_type || '—'}</p>
                    <p className="text-xs text-slate-400">{institution.ownership || ''}</p>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{institution.region || '—'}</td>
                  <td className="px-5 py-3 text-slate-600">{institution.state || '—'}</td>
                  <td className="px-5 py-3">
                    <Badge className="bg-slate-100 text-slate-700">
                      {institution.complaint_count}
                    </Badge>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <Button variant="ghost" size="sm" onClick={() => void openDetail(institution)}>
                      <Eye className="h-3.5 w-3.5" /> View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Register institution"
        description="Add an institution to the central registry."
        footer={
          <>
            <Button variant="outline" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => void submit()} loading={saving}>
              Save institution
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Institution name" required className="sm:col-span-2">
            <Input
              value={form.institution_name}
              onChange={(event) => setForm({ ...form, institution_name: event.target.value })}
              placeholder="e.g. Western Valley Institute of Technology"
            />
          </Field>
          <Field label="AICTE permanent ID">
            <Input
              value={form.aicte_permanent_id}
              onChange={(event) => setForm({ ...form, aicte_permanent_id: event.target.value })}
              placeholder="e.g. AICTE-100123"
            />
          </Field>
          <Field label="Institution type">
            <Select
              value={form.institution_type}
              onChange={(event) => setForm({ ...form, institution_type: event.target.value })}
            >
              {types.map((type) => (
                <option key={type}>{type}</option>
              ))}
            </Select>
          </Field>
          <Field label="Region">
            <Select
              value={form.region}
              onChange={(event) => setForm({ ...form, region: event.target.value })}
            >
              {regions.map((region) => (
                <option key={region}>{region}</option>
              ))}
            </Select>
          </Field>
          <Field label="State">
            <Input
              value={form.state}
              onChange={(event) => setForm({ ...form, state: event.target.value })}
              placeholder="e.g. Maharashtra"
            />
          </Field>
          <Field label="City">
            <Input
              value={form.city}
              onChange={(event) => setForm({ ...form, city: event.target.value })}
              placeholder="e.g. Pune"
            />
          </Field>
          <Field label="District">
            <Input
              value={form.district}
              onChange={(event) => setForm({ ...form, district: event.target.value })}
              placeholder="e.g. Pune"
            />
          </Field>
          <Field label="Contact email">
            <Input
              type="email"
              value={form.contact_email}
              onChange={(event) => setForm({ ...form, contact_email: event.target.value })}
              placeholder="office@example.edu.in"
            />
          </Field>
          <Field label="Website">
            <Input
              type="url"
              value={form.website}
              onChange={(event) => setForm({ ...form, website: event.target.value })}
              placeholder="https://www.example.edu.in"
            />
          </Field>
          <Field label="Established year">
            <Input
              type="number"
              min={1800}
              max={2100}
              value={form.established_year}
              onChange={(event) => setForm({ ...form, established_year: event.target.value })}
              placeholder="e.g. 1983"
            />
          </Field>
          <Field label="Ownership">
            <Select
              value={form.ownership}
              onChange={(event) => setForm({ ...form, ownership: event.target.value })}
            >
              {ownerships.map((ownership) => (
                <option key={ownership}>{ownership}</option>
              ))}
            </Select>
          </Field>
          <Field label="Affiliation / approval" className="sm:col-span-2">
            <Input
              value={form.affiliation}
              onChange={(event) => setForm({ ...form, affiliation: event.target.value })}
              placeholder="e.g. University of Mumbai / AICTE approved"
            />
          </Field>
          <Field label="Address" className="sm:col-span-2">
            <Textarea
              value={form.address}
              onChange={(event) => setForm({ ...form, address: event.target.value })}
              placeholder="Full postal address"
            />
          </Field>
        </div>
      </Modal>

      <Modal
        open={Boolean(detail)}
        onClose={() => setDetail(null)}
        title={detail?.institution_name || 'Institution'}
        description="Institution profile and complaint history"
        size="lg"
      >
        {detail && (
          <div className="space-y-6">
            <dl className="grid gap-4 sm:grid-cols-3">
              <DetailRow label="AICTE ID" value={detail.aicte_permanent_id || '—'} />
              <DetailRow label="Type" value={detail.institution_type || '—'} />
              <DetailRow label="Status" value={detail.institution_status || 'Active'} />
              <DetailRow label="Region" value={detail.region || '—'} />
              <DetailRow label="State / City" value={[detail.state, detail.city].filter(Boolean).join(' / ') || '—'} />
              <DetailRow label="District" value={detail.district || '—'} />
              <DetailRow label="Ownership" value={detail.ownership || '—'} />
              <DetailRow label="Established" value={detail.established_year || '—'} />
              <DetailRow
                label="Affiliation"
                value={detail.affiliation || '—'}
              />
              <DetailRow label="Contact" value={detail.contact_email || '—'} />
              <DetailRow
                label="Website"
                value={
                  detail.website ? (
                    <a
                      href={detail.website}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-700 hover:underline"
                    >
                      {detail.website.replace(/^https?:\/\//, '')}
                    </a>
                  ) : (
                    '—'
                  )
                }
              />
              <DetailRow label="Address" value={detail.address || '—'} />
              <DetailRow label="Registered" value={formatDate(detail.created_at)} />
              <DetailRow label="Total complaints" value={detail.complaint_count} />
            </dl>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Complaint history</h3>
                <span className="text-xs text-slate-500">
                  {detailComplaints.length} record{detailComplaints.length === 1 ? '' : 's'}
                </span>
              </div>
              {detailLoading ? (
                <LoadingBlock label="Loading complaints…" />
              ) : detailComplaints.length === 0 ? (
                <p className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
                  No complaints have been registered for this institution.
                </p>
              ) : (
                <div className="max-h-72 overflow-y-auto rounded-md border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="sticky top-0 bg-slate-50">
                      <tr>
                        {['Complaint', 'Subject', 'Status', 'Priority', 'Received'].map((heading) => (
                          <th
                            key={heading}
                            className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500"
                          >
                            {heading}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {detailComplaints.map((complaint) => (
                        <tr key={complaint.id}>
                          <td className="px-3 py-2 font-medium text-blue-700">
                            {complaint.complaint_number}
                          </td>
                          <td className="px-3 py-2 text-slate-700">{complaint.subject}</td>
                          <td className="px-3 py-2 text-slate-600">{complaint.current_status}</td>
                          <td className="px-3 py-2 text-slate-600">{complaint.priority}</td>
                          <td className="px-3 py-2 text-slate-500">
                            {formatDate(complaint.received_date)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
