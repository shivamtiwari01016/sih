import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  Eye,
  EyeOff,
  GitBranch,
  History,
  Info,
  Lightbulb,
  Plus,
  ShieldAlert,
  Users,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { formatDate, percent, reviewStatusClass } from '../lib/utils'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  Input,
  LoadingBlock,
  Select,
} from '../components/ui'
import RiskScoreModal from '../components/RiskScoreModal'
import CoordinationRoomModal from '../components/CoordinationRoomModal'

interface InstitutionData {
  id: string
  institution_name: string
  aicte_permanent_id: string | null
  institution_type: string | null
  address: string | null
  city: string | null
  state: string | null
  region: string | null
  district: string | null
  contact_email: string | null
  website: string | null
  established_year: number | null
  ownership: string | null
  affiliation: string | null
  institution_status: string | null
  complaint_count: number
  risk?: {
    risk_score: number
    risk_level: string
    factor_breakdown: Array<{ factor: string; points: number; description: string }>
  }
}

interface EdaResponse {
  institution_id: string
  institution_name: string
  insufficient_data: boolean
  stats: {
    total: number
    open: number
    overdue: number
    disposed: number
    active_overlaps: number
    avg_open_age_days: number
  }
  monthly: Array<{
    month: string
    received: number
    disposed: number
  }>
  by_category: Array<{
    category: string
    count: number
  }>
  by_bureau: Array<{
    bureau: string
    count: number
  }>
  by_status: Array<{
    status: string
    count: number
  }>
  ageing: {
    '0-30': number
    '31-60': number
    '61-90': number
    '90+': number
  }
  sla: {
    within_sla_pct: number
    all_institutions_avg_pct: number
  }
  peer: {
    institution_count: number
    state_avg_count: number
    state_avg_risk: number
  }
  insights: string[]
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
  is_sensitive?: boolean
}

interface OverlapItem {
  id: string
  complaint_1: string | null
  complaint_1_id: string
  complaint_1_subject: string | null
  complaint_1_institution: string | null
  complaint_1_bureau: string | null
  complaint_2: string | null
  complaint_2_id: string
  complaint_2_subject: string | null
  complaint_2_institution: string | null
  complaint_2_bureau: string | null
  similarity_score: number | null
  relationship_type: string | null
  review_status: string | null
  matching_reasons: string[]
  created_at: string | null
}

interface TimelineAction {
  id: string
  complaint_id: string
  complaint_number: string
  action_type: string
  remarks: string
  bureau: string | null
  officer: string | null
  timestamp: string | null
  previous_status: string | null
  new_status: string | null
}

const CATEGORY_COLORS = [
  '#2563eb', // Blue
  '#7c3aed', // Purple
  '#059669', // Emerald
  '#d97706', // Amber
  '#dc2626', // Red
  '#0891b2', // Cyan
  '#4f46e5', // Indigo
  '#64748b', // Slate
]

export default function InstitutionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { canWrite } = useAuth()
  const { t } = useLanguage()

  const [activeTab, setActiveTab] = useState<'overview' | 'cases' | 'overlaps' | 'timeline'>('overview')

  const [inst, setInst] = useState<InstitutionData | null>(null)
  const [eda, setEda] = useState<EdaResponse | null>(null)
  const [complaints, setComplaints] = useState<InstitutionComplaint[]>([])
  const [overlaps, setOverlaps] = useState<OverlapItem[]>([])
  const [timeline, setTimeline] = useState<TimelineAction[]>([])
  const [isWatched, setIsWatched] = useState(false)
  const [watchLoading, setWatchLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Modals
  const [riskModalOpen, setRiskModalOpen] = useState(false)
  const [coordinationOverlapId, setCoordinationOverlapId] = useState<string | null>(null)

  // Cases filter state
  const [caseSearch, setCaseSearch] = useState('')
  const [caseBureauFilter, setCaseBureauFilter] = useState('')
  const [caseCategoryFilter, setCaseCategoryFilter] = useState('')
  const [caseStatusFilter, setCaseStatusFilter] = useState('')

  const loadData = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError('')
    try {
      const [instRes, edaRes, compRes, overlapRes, timelineRes, watchRes] = await Promise.all([
        api.get<InstitutionData>(`/api/institutions/${id}`),
        api.get<EdaResponse>(`/api/institutions/${id}/eda`),
        api.get<InstitutionComplaint[]>(`/api/institutions/${id}/complaints`),
        api.get<OverlapItem[]>(`/api/institutions/${id}/overlaps`),
        api.get<TimelineAction[]>(`/api/institutions/${id}/timeline`),
        api.get<{ watching: boolean }>(`/api/institutions/${id}/is-watched`).catch(() => ({ data: { watching: false } })),
      ])
      setInst(instRes.data)
      setEda(edaRes.data)
      setComplaints(compRes.data)
      setOverlaps(overlapRes.data)
      setTimeline(timelineRes.data)
      setIsWatched(watchRes.data?.watching || false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const toggleWatch = async () => {
    if (!id) return
    setWatchLoading(true)
    try {
      if (isWatched) {
        await api.delete(`/api/institutions/${id}/watch`)
        setIsWatched(false)
        toast.success(`Removed ${inst?.institution_name || 'institution'} from watchlist`)
      } else {
        await api.post(`/api/institutions/${id}/watch`)
        setIsWatched(true)
        toast.success(`Added ${inst?.institution_name || 'institution'} to watchlist`)
      }
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setWatchLoading(false)
    }
  }

  // Filter complaints in Cases tab
  const filteredComplaints = complaints.filter((c) => {
    if (caseBureauFilter && c.assigned_bureau !== caseBureauFilter) return false
    if (caseCategoryFilter && c.category !== caseCategoryFilter) return false
    if (caseStatusFilter && c.current_status !== caseStatusFilter) return false
    if (caseSearch.trim()) {
      const q = caseSearch.toLowerCase()
      return (
        c.complaint_number.toLowerCase().includes(q) ||
        c.subject.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Distinct options for filters
  const bureauOptions = Array.from(new Set(complaints.map((c) => c.assigned_bureau).filter(Boolean))) as string[]
  const categoryOptions = Array.from(new Set(complaints.map((c) => c.category).filter(Boolean)))
  const statusOptions = Array.from(new Set(complaints.map((c) => c.current_status).filter(Boolean)))

  if (loading) {
    return (
      <div className="py-12">
        <LoadingBlock label="Loading institution analytics and EDA..." />
      </div>
    )
  }

  if (error || !inst) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/institutions')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Institutions
        </Button>
        <ErrorBanner message={error || 'Institution not found'} />
      </div>
    )
  }

  const riskScore = inst.risk?.risk_score ?? Math.min(inst.complaint_count * 12, 100)
  const riskBadgeClass =
    riskScore >= 70
      ? 'bg-red-100 text-red-800 border-red-200 hover:bg-red-200'
      : riskScore >= 35
      ? 'bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-200'
      : 'bg-emerald-100 text-emerald-800 border-emerald-200 hover:bg-emerald-200'

  const ageingData = eda?.ageing
    ? [
        { bucket: '0–30 Days', count: eda.ageing['0-30'] || 0, fill: '#3b82f6' },
        { bucket: '31–60 Days', count: eda.ageing['31-60'] || 0, fill: '#eab308' },
        { bucket: '61–90 Days', count: eda.ageing['61-90'] || 0, fill: '#f97316' },
        { bucket: '90+ Days', count: eda.ageing['90+'] || 0, fill: '#ef4444' },
      ]
    : []

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/institutions')}
        className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Institutions Registry
      </button>

      {/* Header Profile */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="rounded-lg bg-blue-50 p-2 text-blue-600">
                <Building2 className="h-6 w-6" />
              </span>
              <div>
                <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
                  {inst.institution_name}
                </h1>
                <p className="text-xs text-slate-500">
                  AICTE Permanent ID:{' '}
                  <span className="font-mono font-bold text-slate-700">
                    {inst.aicte_permanent_id || 'Not Assigned'}
                  </span>{' '}
                  · Established: {inst.established_year || '—'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                {inst.institution_type || 'Technical Institute'}
              </span>
              <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                {inst.city ? `${inst.city}, ` : ''}{inst.state || 'India'}
              </span>
              <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                {inst.region || 'Regional'} Bureau
              </span>
              <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                {inst.ownership || 'Private'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap md:self-start">
            {/* Explainable Risk Badge Button */}
            <button
              onClick={() => setRiskModalOpen(true)}
              title="Click to view explainable risk score breakdown"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors shadow-2xs ${riskBadgeClass}`}
            >
              <ShieldAlert className="h-4 w-4" />
              Risk Score: {riskScore}/100
            </button>

            {/* Watch Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={toggleWatch}
              loading={watchLoading}
              className={isWatched ? 'border-amber-300 bg-amber-50 text-amber-800' : ''}
            >
              {isWatched ? (
                <>
                  <EyeOff className="h-3.5 w-3.5 mr-1 text-amber-600" />
                  {t('inst.watching')}
                </>
              ) : (
                <>
                  <Eye className="h-3.5 w-3.5 mr-1 text-slate-500" />
                  {t('inst.watch')}
                </>
              )}
            </Button>

            {/* Fast Case Entry */}
            {canWrite && (
              <Button
                size="sm"
                className="bg-navy hover:bg-slate-800 text-white font-semibold shadow-xs"
                onClick={() =>
                  navigate(
                    `/complaints?action=new&institution_id=${inst.id}&institution_name=${encodeURIComponent(
                      inst.institution_name,
                    )}`,
                  )
                }
              >
                <Plus className="h-4 w-4 mr-1" /> {t('inst.add_complaint')}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Stat Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Complaints</p>
          <p className="text-xl font-extrabold text-slate-900 mt-1">{eda?.stats.total ?? inst.complaint_count}</p>
        </div>
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider">Open Files</p>
          <p className="text-xl font-extrabold text-blue-900 mt-1">{eda?.stats.open ?? 0}</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50/60 p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-red-700 uppercase tracking-wider">Overdue SLA</p>
          <p className="text-xl font-extrabold text-red-900 mt-1">{eda?.stats.overdue ?? 0}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Disposed</p>
          <p className="text-xl font-extrabold text-emerald-900 mt-1">{eda?.stats.disposed ?? 0}</p>
        </div>
        <div className="rounded-xl border border-purple-200 bg-purple-50/50 p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-purple-700 uppercase tracking-wider">Active Overlaps</p>
          <p className="text-xl font-extrabold text-purple-900 mt-1">{eda?.stats.active_overlaps ?? 0}</p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3.5 shadow-2xs">
          <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">Avg Open Age</p>
          <p className="text-xl font-extrabold text-amber-900 mt-1">{eda?.stats.avg_open_age_days ?? 0}d</p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'overview'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Lightbulb className="h-4 w-4" />
          {t('inst.overview_eda')}
        </button>
        <button
          onClick={() => setActiveTab('cases')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'cases'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Clock className="h-4 w-4" />
          {t('inst.cases')} ({complaints.length})
        </button>
        <button
          onClick={() => setActiveTab('overlaps')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'overlaps'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <GitBranch className="h-4 w-4" />
          {t('inst.overlaps')} ({overlaps.length})
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'timeline'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <History className="h-4 w-4" />
          {t('inst.timeline')} ({timeline.length})
        </button>
      </div>

      {/* TAB 1: OVERVIEW & EDA */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Dynamic Insight Lines */}
          {eda?.insights && eda.insights.length > 0 && (
            <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-4 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-blue-900 uppercase tracking-wide">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                Exploratory Data Intelligence & Key Insights
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {eda.insights.map((ins, i) => (
                  <div key={i} className="flex items-start gap-2 bg-white/90 p-2.5 rounded-lg border border-blue-100 text-xs text-slate-700 shadow-2xs">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                    <span>{ins}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insufficient Data Banner (< 5 complaints) */}
          {eda?.insufficient_data ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-6 text-center space-y-2">
              <Info className="h-8 w-8 text-amber-600 mx-auto" />
              <h3 className="text-sm font-bold text-amber-950">
                {t('inst.insufficient_data')}
              </h3>
              <p className="text-xs text-amber-800 max-w-md mx-auto">
                This institution has recorded {eda.stats.total} complaint{eda.stats.total === 1 ? '' : 's'}. Longitudinal trend charts, category distributions, and ageing analytics automatically unlock once 5 complaints are registered.
              </p>
            </div>
          ) : (
            <>
              {/* Row 1: Monthly Trends (12 months) + Category Donut */}
              <div className="grid gap-6 lg:grid-cols-3">
                {/* 12-Month Longitudinal Trend */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs lg:col-span-2">
                  <div className="mb-4">
                    <h3 className="text-sm font-bold text-slate-900">
                      12-Month Case Inflow vs Disposal Trend
                    </h3>
                    <p className="text-xs text-slate-500">
                      Monthly incoming complaints vs cases disposed over the trailing 12 months
                    </p>
                  </div>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={eda?.monthly || []} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            color: '#fff',
                            borderRadius: '8px',
                            fontSize: '11px',
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                        <Line
                          type="monotone"
                          dataKey="received"
                          name="Received"
                          stroke="#2563eb"
                          strokeWidth={2.5}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="disposed"
                          name="Disposed"
                          stroke="#059669"
                          strokeWidth={2.5}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Category Donut Breakdown */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Complaint Category Distribution
                    </h3>
                    <p className="text-xs text-slate-500">
                      Share by regulatory grievance category
                    </p>
                  </div>
                  <div className="h-56 w-full my-auto">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={eda?.by_category || []}
                          dataKey="count"
                          nameKey="category"
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={80}
                          paddingAngle={3}
                        >
                          {(eda?.by_category || []).map((_, index) => (
                            <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            color: '#fff',
                            borderRadius: '8px',
                            fontSize: '11px',
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex flex-wrap gap-2 text-[10px] text-slate-600 pt-2 border-t border-slate-100">
                    {(eda?.by_category || []).slice(0, 4).map((c, idx) => (
                      <span key={idx} className="flex items-center gap-1">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                        />
                        {c.category} ({c.count})
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Row 2: Bureau Split + Ageing Bar */}
              <div className="grid gap-6 md:grid-cols-2">
                {/* Bureau Split Bar */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <h3 className="text-sm font-bold text-slate-900">
                      Bureau Distribution
                    </h3>
                    <p className="text-xs text-slate-500">
                      Complaint volume allocated across regulatory bureaus
                    </p>
                  </div>
                  <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={eda?.by_bureau || []} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="bureau" tick={{ fontSize: 10, fill: '#64748b' }} interval={0} />
                        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            color: '#fff',
                            borderRadius: '8px',
                            fontSize: '11px',
                          }}
                        />
                        <Bar dataKey="count" name="Complaints" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Ageing Bar */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <h3 className="text-sm font-bold text-slate-900">
                      Open Cases Ageing Profile
                    </h3>
                    <p className="text-xs text-slate-500">
                      Age distribution of active complaints waiting for regulatory resolution
                    </p>
                  </div>
                  <div className="h-52 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={ageingData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="bucket" tick={{ fontSize: 11, fill: '#64748b' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            color: '#fff',
                            borderRadius: '8px',
                            fontSize: '11px',
                          }}
                        />
                        <Bar dataKey="count" name="Open Cases" radius={[4, 4, 0, 0]}>
                          {ageingData.map((entry, index) => (
                            <Cell key={`age-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Row 3: SLA Performance & State Peer Benchmarks */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* SLA Card */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
              <h3 className="text-sm font-bold text-slate-900">
                SLA Compliance Benchmark
              </h3>
              <p className="text-xs text-slate-500">
                Performance against AICTE 30-day regulatory mandate
              </p>
              <div className="space-y-3 pt-1">
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-700">This Institution SLA Adherence</span>
                    <span className="text-blue-700">{eda?.sla.within_sla_pct ?? 100}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{ width: `${eda?.sla.within_sla_pct ?? 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-700">All-Institutions AICTE National Average</span>
                    <span className="text-slate-600">{eda?.sla.all_institutions_avg_pct ?? 85}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-400 rounded-full"
                      style={{ width: `${eda?.sla.all_institutions_avg_pct ?? 85}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Peer Benchmark Card */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
              <h3 className="text-sm font-bold text-slate-900">
                State Peer Group Comparison ({inst.state || 'National'})
              </h3>
              <p className="text-xs text-slate-500">
                Comparison against technical institutions in the same state
              </p>
              <div className="grid grid-cols-3 gap-2 pt-1 text-center">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-base font-bold text-slate-900">{eda?.peer.institution_count ?? 0}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Institution Cases</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-base font-bold text-slate-900">{eda?.peer.state_avg_count ?? 0}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">State Average</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-base font-bold text-amber-700">{eda?.peer.state_avg_risk ?? 0}/100</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Peer Avg Risk</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CASES */}
      {activeTab === 'cases' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <Input
              placeholder="Search cases by subject or ID…"
              value={caseSearch}
              onChange={(e) => setCaseSearch(e.target.value)}
              className="text-xs"
            />
            <Select
              value={caseBureauFilter}
              onChange={(e) => setCaseBureauFilter(e.target.value)}
              className="text-xs"
            >
              <option value="">All Bureaus</option>
              {bureauOptions.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </Select>
            <Select
              value={caseCategoryFilter}
              onChange={(e) => setCaseCategoryFilter(e.target.value)}
              className="text-xs"
            >
              <option value="">All Categories</option>
              {categoryOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
            <Select
              value={caseStatusFilter}
              onChange={(e) => setCaseStatusFilter(e.target.value)}
              className="text-xs"
            >
              <option value="">All Statuses</option>
              {statusOptions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>

          {/* Cases Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs">
            {filteredComplaints.length === 0 ? (
              <EmptyState
                title="No complaints matching filters"
                description="Try clearing search or filter options to view registered complaints."
              />
            ) : (
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 text-left">Case Number</th>
                    <th className="py-3 px-4 text-left">Category</th>
                    <th className="py-3 px-4 text-left">Subject</th>
                    <th className="py-3 px-3 text-center">Status</th>
                    <th className="py-3 px-3 text-center">Priority</th>
                    <th className="py-3 px-4 text-left">Assigned Bureau</th>
                    <th className="py-3 px-4 text-left">Received Date</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredComplaints.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/complaints?id=${c.id}`)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-blue-700">
                        {c.complaint_number}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-800">
                        {c.category}
                      </td>
                      <td className="py-3 px-4 text-slate-600 max-w-xs truncate">
                        {c.subject}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <Badge className="bg-slate-100 text-slate-800 text-[10px]">
                          {c.current_status}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            c.priority === 'Urgent'
                              ? 'bg-red-100 text-red-800'
                              : c.priority === 'High'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {c.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {c.assigned_bureau || 'Unassigned'}
                      </td>
                      <td className="py-3 px-4 text-slate-500">
                        {formatDate(c.received_date)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs text-blue-600 hover:text-blue-800"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/complaints?id=${c.id}`)
                          }}
                        >
                          Open &rarr;
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: OVERLAPS */}
      {activeTab === 'overlaps' && (
        <div className="space-y-4">
          {overlaps.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
              <GitBranch className="h-8 w-8 text-slate-400 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-900">No Overlaps Detected</h3>
              <p className="text-xs text-slate-500 mt-1">
                AICTE 3-layer detection engine has not identified cross-bureau overlap pairs for this institution.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {overlaps.map((o) => (
                <div
                  key={o.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs hover:border-slate-300 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-purple-50 p-1.5 text-purple-600">
                        <GitBranch className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="text-sm font-bold text-slate-900 font-mono">
                          {o.complaint_1} ↔ {o.complaint_2}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {o.relationship_type} · Created {formatDate(o.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-bold text-white">
                        {percent(o.similarity_score)} Match
                      </span>
                      <Badge className={reviewStatusClass(o.review_status)}>
                        {o.review_status}
                      </Badge>
                      <Button
                        size="sm"
                        className="bg-navy hover:bg-slate-800 text-white font-semibold text-xs ml-2 shadow-2xs"
                        onClick={() => setCoordinationOverlapId(o.id)}
                      >
                        <Users className="h-3.5 w-3.5 mr-1 text-amber-400" />
                        {t('btn.coord_room')}
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <span className="text-xs font-mono font-bold text-blue-700">{o.complaint_1}</span>
                      <p className="text-xs font-bold text-slate-900 mt-0.5">{o.complaint_1_institution}</p>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2">{o.complaint_1_subject}</p>
                      <p className="text-[10px] text-slate-400 mt-2 font-medium">Bureau: {o.complaint_1_bureau}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-3">
                      <span className="text-xs font-mono font-bold text-blue-700">{o.complaint_2}</span>
                      <p className="text-xs font-bold text-slate-900 mt-0.5">{o.complaint_2_institution}</p>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2">{o.complaint_2_subject}</p>
                      <p className="text-[10px] text-slate-400 mt-2 font-medium">Bureau: {o.complaint_2_bureau}</p>
                    </div>
                  </div>

                  {o.matching_reasons && o.matching_reasons.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
                      <span className="text-[10px] font-bold text-slate-500 uppercase mr-1">Matching Reasons:</span>
                      {o.matching_reasons.map((r, i) => (
                        <span key={i} className="text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: TIMELINE */}
      {activeTab === 'timeline' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="border-b pb-3 mb-4">
            <h3 className="text-sm font-bold text-slate-900">
              Merged Chronological Regulatory Actions
            </h3>
            <p className="text-xs text-slate-500">
              Cross-bureau audit trail of notices, hearings, inspections, and status transitions for this institution
            </p>
          </div>

          {timeline.length === 0 ? (
            <EmptyState
              title="No recorded case actions"
              description="Case actions recorded by officers across bureaus will appear here chronologically."
            />
          ) : (
            <div className="relative border-l border-slate-200 ml-4 space-y-6 py-2">
              {timeline.map((act) => (
                <div key={act.id} className="relative pl-6">
                  <span className="absolute -left-2 top-1.5 h-4 w-4 rounded-full border-2 border-white bg-blue-600 shadow-xs" />
                  <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200 text-xs space-y-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{act.action_type}</span>
                        <span className="font-mono text-blue-700 font-semibold">{act.complaint_number}</span>
                        {act.bureau && (
                          <Badge className="bg-purple-100 text-purple-800 text-[10px] font-semibold">
                            {act.bureau}
                          </Badge>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(act.timestamp)}
                      </span>
                    </div>

                    <p className="text-slate-700 pt-1">{act.remarks}</p>

                    <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                      <span>Officer: {act.officer}</span>
                      {act.new_status && (
                        <span>
                          Status: <strong className="text-slate-600">{act.new_status}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reusable Risk Score Breakdown Modal */}
      {riskModalOpen && (
        <RiskScoreModal
          institutionId={inst.id}
          institutionName={inst.institution_name}
          open={riskModalOpen}
          onClose={() => setRiskModalOpen(false)}
        />
      )}

      {/* Reusable Coordination Room Modal */}
      {coordinationOverlapId && (
        <CoordinationRoomModal
          overlapId={coordinationOverlapId}
          open={Boolean(coordinationOverlapId)}
          onClose={() => setCoordinationOverlapId(null)}
          onUpdated={loadData}
        />
      )}
    </div>
  )
}
