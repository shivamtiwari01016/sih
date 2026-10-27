import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Eye, MapPin, Plus, Search, Table } from 'lucide-react'
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
  Select,
  Textarea,
} from '../components/ui'
import CopMap from '../components/CopMap'

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
  lat?: number | null
  lng?: number | null
  created_at: string | null
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
  const navigate = useNavigate()
  const { canWrite } = useAuth()
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [viewMode, setViewMode] = useState<'table' | 'map'>('table')

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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Institution Registry"
        subtitle="Curated catalog of all 23 IITs and 133 major Maharashtra institutions, with full contact and affiliation details"
        actions={
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 border border-slate-200 rounded-lg p-0.5 bg-slate-100">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  viewMode === 'table' ? 'bg-white shadow-xs text-slate-900 font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Table className="h-3.5 w-3.5" /> Table
              </button>
              <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  viewMode === 'map' ? 'bg-white shadow-xs text-blue-700 font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <MapPin className="h-3.5 w-3.5 text-blue-600" /> Free Leaflet Map
              </button>
            </div>
            {canWrite && (
              <Button onClick={() => setAddOpen(true)}>
                <Plus className="h-4 w-4" /> Add Institution
              </Button>
            )}
          </div>
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

      {viewMode === 'map' ? (
        <div className="space-y-3">
          <CopMap
            institutions={institutions.map((i) => ({
              id: i.id,
              name: i.institution_name,
              aicte_id: i.aicte_permanent_id || '',
              city: i.city || '',
              state: i.state || '',
              region: i.region || '',
              lat: i.lat || (18.5204 + (Math.abs(i.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 1000) * 0.01),
              lng: i.lng || (73.8567 + (Math.abs(i.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 800) * 0.01),
              open_cases: i.complaint_count || 0,
              risk_score: Math.min((i.complaint_count || 0) * 12, 100),
              has_overlap: false,
            }))}
            onSelectInstitution={(inst) => {
              navigate(`/institutions/${inst.id}`)
            }}
            height="620px"
          />
        </div>
      ) : (
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
                  <tr
                    key={institution.id}
                    onClick={() => navigate(`/institutions/${institution.id}`)}
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                  >
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
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/institutions/${institution.id}`)
                        }}
                      >
                        <Eye className="h-3.5 w-3.5" /> View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

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
    </div>
  )
}
