import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  GitBranch,
  Inbox,
  Lightbulb,
  MapPin,
  Sparkles,
} from 'lucide-react'
import { api } from '../lib/api'
import { formatDate, percent } from '../lib/utils'
import { Badge, Button, LoadingBlock, StatCard } from '../components/ui'
import { useLanguage } from '../context/LanguageContext'
import CopMap, { CopInstitution } from '../components/CopMap'
import DailyBriefingModal from '../components/DailyBriefingModal'
import RiskScoreModal from '../components/RiskScoreModal'
import CoordinationRoomModal from '../components/CoordinationRoomModal'

interface MyDeskData {
  all_clear: boolean
  officer_name: string
  officer_role: string
  officer_bureau: string
  overlaps_awaiting_count: number
  overlaps_awaiting: Array<{
    id: string
    case_1: string
    case_2: string
    institution: string
    similarity_score: number
    status: string
    lead_bureau: string | null
  }>
  urgent_cases_count: number
  prioritised_queue: Array<{
    case_id: string
    complaint_number: string
    institution_name: string
    category: string
    priority: string
    expected_disposal_date: string
    urgency_score: number
    ranking_reasons: string[]
    current_status: string
  }>
  action_intent_conflicts: Array<{
    id: string
    case_id: string
    intent_type: string
    planned_date: string
    institution: string
    conflicts: string[]
  }>
}

interface CoordinationHealthData {
  open_overlaps: number
  decided_overlaps: number
  total_cross_bureau_overlaps: number
  avg_ack_hours: number
  avg_decision_days: number
  escalations_count: number
  conflicts_prevented: number
  health_score: number
}

interface ManagementInsight {
  title: string
  headline: string
  why: string
  suggested_action: string
  type: string
}

interface Summary {
  total_complaints: number
  pending_complaints: number
  under_process_cases: number
  disposed_cases: number
  overdue_cases: number
  escalated_cases: number
  potential_overlaps: number
  pending_coordination: number
  total_institutions: number
  disposal_rate: number
}

export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useLanguage()

  // Tab State: 'my-desk' | 'cop' | 'workload'
  const [activeTab, setActiveTab] = useState<'my-desk' | 'cop' | 'workload'>('my-desk')

  // Data States
  const [deskData, setDeskData] = useState<MyDeskData | null>(null)
  const [copInstitutions, setCopInstitutions] = useState<CopInstitution[]>([])
  const [coordHealth, setCoordHealth] = useState<CoordinationHealthData | null>(null)
  const [insights, setInsights] = useState<ManagementInsight[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)

  // Modals
  const [briefingOpen, setBriefingOpen] = useState(false)
  const [selectedInstForRisk, setSelectedInstForRisk] = useState<{ id: string; name: string } | null>(null)
  const [selectedOverlapId, setSelectedOverlapId] = useState<string | null>(null)

  // Sync tab with query params
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const tabParam = params.get('tab')
    if (tabParam === 'my-desk') setActiveTab('my-desk')
    else if (tabParam === 'cop') setActiveTab('cop')
    else if (tabParam === 'workload') setActiveTab('workload')
  }, [location.search])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [deskRes, copRes, healthRes, insightsRes, sumRes] = await Promise.all([
        api.get<MyDeskData>('/api/dashboard/my-desk'),
        api.get<{ institutions: CopInstitution[] }>('/api/dashboard/cop-map'),
        api.get<CoordinationHealthData>('/api/dashboard/coordination-health'),
        api.get<{ insights: ManagementInsight[] }>('/api/dashboard/insights'),
        api.get<Summary>('/api/dashboard/summary'),
      ])
      setDeskData(deskRes.data)
      setCopInstitutions(copRes.data.institutions || [])
      setCoordHealth(healthRes.data)
      setInsights(insightsRes.data.insights || [])
      setSummary(sumRes.data)
    } catch {
      // Graceful fallback for non-blocking UI
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  return (
    <div className="space-y-6">
      {/* Top Header & Fast Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {activeTab === 'my-desk'
              ? t('nav.my_desk')
              : activeTab === 'cop'
              ? t('nav.cop_map')
              : t('nav.dashboard')}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Command & Control Dashboard for AICTE Regulatory Grievance Monitoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setBriefingOpen(true)}
            className="border-purple-200 text-purple-700 hover:bg-purple-50"
          >
            <Sparkles className="h-4 w-4 mr-1.5 text-purple-600" />
            {t('desk.briefing_btn')}
          </Button>
          <Button
            size="sm"
            className="bg-navy hover:bg-slate-800 text-white"
            onClick={() => navigate('/complaints?action=new')}
          >
            + Fast Case Entry (≤30s)
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-200 text-sm font-semibold">
        <button
          onClick={() => {
            setActiveTab('my-desk')
            navigate('/dashboard?tab=my-desk')
          }}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'my-desk'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Inbox className="h-4 w-4" />
          {t('nav.my_desk')}
          {deskData && (deskData.overlaps_awaiting_count > 0 || deskData.urgent_cases_count > 0) && (
            <span className="rounded-full bg-red-100 px-1.5 py-0.2 text-[10px] font-bold text-red-700">
              {deskData.overlaps_awaiting_count + deskData.urgent_cases_count}
            </span>
          )}
        </button>

        <button
          onClick={() => {
            setActiveTab('cop')
            navigate('/dashboard?tab=cop')
          }}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'cop'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <MapPin className="h-4 w-4" />
          {t('nav.cop_map')} & Management Health
        </button>

        <button
          onClick={() => {
            setActiveTab('workload')
            navigate('/dashboard?tab=workload')
          }}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'workload'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          Workload & Analytics
        </button>
      </div>

      {loading ? (
        <LoadingBlock label="Loading command intelligence..." />
      ) : activeTab === 'my-desk' ? (
        /* TAB 1: MY DESK (Exception-Only View) */
        <div className="space-y-6">
          {/* Desk Summary Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold text-slate-500">Authenticated AICTE Officer</p>
              <h3 className="text-base font-bold text-slate-900">
                {deskData?.officer_name} ({deskData?.officer_bureau})
              </h3>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-1.5 text-center">
                <span className="block text-base font-bold text-red-700">
                  {deskData?.urgent_cases_count ?? 0}
                </span>
                <span className="text-red-900 text-[11px] font-medium">Urgent Deadlines</span>
              </div>
              <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-1.5 text-center">
                <span className="block text-base font-bold text-amber-700">
                  {deskData?.overlaps_awaiting_count ?? 0}
                </span>
                <span className="text-amber-900 text-[11px] font-medium">Overlaps Awaiting Reply</span>
              </div>
              <div className="rounded-lg bg-blue-50 border border-blue-200 px-3 py-1.5 text-center">
                <span className="block text-base font-bold text-blue-700">
                  {deskData?.action_intent_conflicts?.length ?? 0}
                </span>
                <span className="text-blue-900 text-[11px] font-medium">Intent Conflicts</span>
              </div>
            </div>
          </div>

          {/* Action Intent Conflict Warnings */}
          {deskData?.action_intent_conflicts && deskData.action_intent_conflicts.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                Cross-Bureau Action Intent Conflicts Requiring Attention:
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                {deskData.action_intent_conflicts.map((item) => (
                  <div key={item.id} className="rounded-lg bg-white border border-amber-200 p-3 text-xs shadow-2xs">
                    <div className="flex justify-between items-center font-bold text-slate-900">
                      <span>{item.intent_type} on {formatDate(item.planned_date)}</span>
                      <span className="text-slate-500 font-normal">{item.institution}</span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {item.conflicts.map((c, i) => (
                        <p key={i} className="text-amber-800 text-[11px]">• {c}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Overlaps Awaiting Reply */}
          {deskData?.overlaps_awaiting && deskData.overlaps_awaiting.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-purple-600" />
                  {t('desk.overlaps_awaiting')}
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/overlaps')}
                  className="text-xs text-blue-600 hover:text-blue-800 p-0 h-auto font-semibold"
                >
                  View all ({deskData.overlaps_awaiting_count}) &rarr;
                </Button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {deskData.overlaps_awaiting.slice(0, 3).map((o) => (
                  <div key={o.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-mono font-bold text-blue-700">
                          {o.case_1} ↔ {o.case_2}
                        </span>
                        <Badge className="bg-purple-100 text-purple-800 text-[10px]">
                          Conf: {Math.round(o.similarity_score * 100)}%
                        </Badge>
                      </div>
                      <p className="text-xs font-bold text-slate-900">{o.institution}</p>
                      <p className="text-[11px] text-slate-500 mt-1">Lead: {o.lead_bureau || 'Pending proposal'}</p>
                    </div>
                    <div className="mt-3 flex items-center justify-end gap-2 border-t pt-2.5">
                      <Button
                        size="sm"
                        className="bg-navy hover:bg-slate-800 text-white text-xs"
                        onClick={() => setSelectedOverlapId(o.id)}
                      >
                        {t('btn.coord_room')}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Prioritized Queue */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                <Clock className="h-4 w-4 text-blue-600" />
                {t('desk.urgent_queue')} (Ranked by Deadline, Severity & Overlap)
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/complaints')}
                className="text-xs text-blue-600 hover:text-blue-800 p-0 h-auto font-semibold"
              >
                View all ({deskData?.urgent_cases_count ?? 0}) &rarr;
              </Button>
            </div>
            {deskData?.prioritised_queue && deskData.prioritised_queue.length > 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs divide-y divide-slate-100">
                {deskData.prioritised_queue.slice(0, 5).map((c) => (
                  <div key={c.case_id} className="p-3.5 flex flex-wrap items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-blue-700">{c.complaint_number}</span>
                        <span className="text-xs font-bold text-slate-900">{c.institution_name}</span>
                        <Badge className="bg-slate-100 text-slate-700 text-[10px]">{c.category}</Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                        <span>Due: <strong className="text-slate-800">{formatDate(c.expected_disposal_date)}</strong></span>
                        <span>·</span>
                        <span>Status: {c.current_status}</span>
                        <span>·</span>
                        <span className="text-amber-700 font-semibold">{c.ranking_reasons.join(', ')}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-800">
                        Score: {c.urgency_score}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => navigate(`/complaints?id=${c.case_id}`)}
                        className="text-xs"
                      >
                        Open Case
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-8 text-center">
                <CheckCircle2 className="h-10 w-10 text-emerald-600 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-emerald-950">{t('desk.all_clear')}</h4>
                <p className="text-xs text-emerald-700 mt-1">All SLA deadlines and coordination requests are up to date.</p>
              </div>
            )}
          </div>
        </div>
      ) : activeTab === 'cop' ? (
        /* TAB 2: COMMON OPERATING PICTURE (COP) & HEALTH */
        <div className="space-y-6">
          {/* Management Health Metrics */}
          {coordHealth && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Open Overlaps"
                value={coordHealth.open_overlaps}
                tone="amber"
              />
              <StatCard
                label="Avg Ack Time"
                value={`${coordHealth.avg_ack_hours}h`}
                tone="blue"
              />
              <StatCard
                label="Avg Decision Days"
                value={`${coordHealth.avg_decision_days}d`}
                tone="green"
              />
              <StatCard
                label="Coordination Health"
                value={`${coordHealth.health_score}%`}
                tone="purple"
              />
            </div>
          )}

          {/* Interactive Leaflet COP India Map */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Common Operating Picture (COP) – India Complaint Density & Overlaps
                </h3>
                <p className="text-xs text-slate-500">
                  Real-time geographic distribution of 305+ AICTE approved technical institutions
                </p>
              </div>
              <Badge className="bg-blue-100 text-blue-800 font-semibold">
                {copInstitutions.length} Institutions Mapped
              </Badge>
            </div>
            <CopMap
              institutions={copInstitutions}
              onSelectInstitution={(inst) => setSelectedInstForRisk({ id: inst.id, name: inst.name })}
            />
          </div>

          {/* 5 Management Insight Cards (Section 5.E) */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              Executive Decision Support Insights (Max 5 Management Priority Cards)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {insights.map((ins, idx) => (
                <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 uppercase">
                      {ins.type}
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 mt-2">{ins.title}</h4>
                    <p className="text-xs font-semibold text-slate-800 mt-1">{ins.headline}</p>
                    <p className="text-[11px] text-slate-600 mt-1.5"><strong className="text-slate-700">Why:</strong> {ins.why}</p>
                  </div>
                  <div className="mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-blue-700 font-medium">
                    → Next Step: {ins.suggested_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* TAB 3: WORKLOAD & TRENDS */
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Complaints" value={summary?.total_complaints ?? 0} tone="blue" />
            <StatCard label="Under Process" value={summary?.under_process_cases ?? 0} tone="amber" />
            <StatCard label="Disposed" value={summary?.disposed_cases ?? 0} tone="green" />
            <StatCard label="Disposal Rate" value={percent(summary?.disposal_rate ?? 0.75)} tone="purple" />
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Bureau Workload Distribution</h3>
            <div className="h-64 flex items-center justify-center text-xs text-slate-500">
              Workload metrics aggregated across Regulation Bureau, PGRC, Approval, and Regional offices.
            </div>
          </div>
        </div>
      )}

      {/* Daily Briefing Modal */}
      <DailyBriefingModal open={briefingOpen} onClose={() => setBriefingOpen(false)} />

      {/* Explainable Risk Score Modal */}
      {selectedInstForRisk && (
        <RiskScoreModal
          institutionId={selectedInstForRisk.id}
          institutionName={selectedInstForRisk.name}
          open={Boolean(selectedInstForRisk)}
          onClose={() => setSelectedInstForRisk(null)}
        />
      )}

      {/* Coordination Room Modal */}
      {selectedOverlapId && (
        <CoordinationRoomModal
          overlapId={selectedOverlapId}
          open={Boolean(selectedOverlapId)}
          onClose={() => setSelectedOverlapId(null)}
          onUpdated={loadAll}
        />
      )}
    </div>
  )
}
