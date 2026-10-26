import { useCallback, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  GitBranch,
  RefreshCw,
  Target,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { formatDate, percent, reviewStatusClass } from '../lib/utils'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  Input,
  LoadingBlock,
  PageHeader,
  Select,
} from '../components/ui'
import CoordinationRoomModal from '../components/CoordinationRoomModal'

interface Overlap {
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
  lead_bureau_code?: string | null
  matching_reasons: string[]
  reviewed_by: string | null
  reviewed_at: string | null
  review_remarks: string | null
  created_at: string | null
}

interface AccuracyRow {
  method: string
  precision: number
  recall: number
  f1_score: number
  tp: number
  fp: number
  fn: number
}

interface AccuracyResponse {
  results: AccuracyRow[]
  total_labelled_pairs: number
  summary: string
}

const reviewStatuses = [
  'Suggested',
  'Confirmed Related',
  'Coordinating',
  'Decided',
  'Requires Further Review',
  'Rejected',
]

export default function Overlaps() {
  const location = useLocation()
  const { canWrite } = useAuth()

  const [activeTab, setActiveTab] = useState<'overlaps' | 'accuracy'>('overlaps')

  const [overlaps, setOverlaps] = useState<Overlap[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [scanning, setScanning] = useState(false)

  // Coordination Room Modal
  const [coordinationOverlapId, setCoordinationOverlapId] = useState<string | null>(null)

  // Accuracy state
  const [accuracyData, setAccuracyData] = useState<AccuracyResponse | null>(null)
  const [accuracyLoading, setAccuracyLoading] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if (params.get('tab') === 'accuracy') {
      setActiveTab('accuracy')
    }
  }, [location.search])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const overlapResponse = await api.get<Overlap[]>('/api/overlaps', {
        params: { ...(statusFilter ? { status: statusFilter } : {}), limit: 500 },
      })
      setOverlaps(overlapResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  const loadAccuracy = async () => {
    setAccuracyLoading(true)
    try {
      const res = await api.get<AccuracyResponse>('/api/overlaps/accuracy')
      setAccuracyData(res.data)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setAccuracyLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'accuracy' && !accuracyData) {
      void loadAccuracy()
    }
  }, [activeTab, accuracyData])

  const scan = async () => {
    setScanning(true)
    try {
      const response = await api.post<{ matches_found?: number; scanned?: number }>(
        '/api/overlaps/scan',
        {},
      )
      toast.success(
        `Overlap scan complete · ${response.data.matches_found ?? 0} overlap suggestions generated`,
      )
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setScanning(false)
    }
  }

  const filtered = overlaps.filter((overlap) => {
    if (!search.trim()) return true
    const term = search.toLowerCase()
    return (
      overlap.complaint_1?.toLowerCase().includes(term) ||
      overlap.complaint_2?.toLowerCase().includes(term) ||
      overlap.complaint_1_subject?.toLowerCase().includes(term) ||
      overlap.complaint_2_subject?.toLowerCase().includes(term) ||
      overlap.complaint_1_institution?.toLowerCase().includes(term) ||
      overlap.complaint_2_institution?.toLowerCase().includes(term)
    )
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Overlap Intelligence & Coordination Engine"
        subtitle="3-Layer AICTE Detection Engine: Exact AICTE ID + Fuzzy Name Normalization + Multilingual MiniLM Cosine Similarity"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab(activeTab === 'overlaps' ? 'accuracy' : 'overlaps')}
            >
              <Target className="h-4 w-4 mr-1 text-blue-600" />
              {activeTab === 'overlaps' ? 'Engine Accuracy Benchmark' : 'Back to Overlaps'}
            </Button>
            {canWrite && (
              <Button size="sm" onClick={() => void scan()} loading={scanning} className="bg-navy text-white">
                <RefreshCw className="h-4 w-4 mr-1" /> Re-scan All Complaints
              </Button>
            )}
          </div>
        }
      />

      {error && <ErrorBanner message={error} />}

      {/* Tabs */}
      <div className="flex border-b border-slate-200 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('overlaps')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'overlaps'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <GitBranch className="h-4 w-4" />
          Active Cross-Bureau Overlaps ({overlaps.length})
        </button>
        <button
          onClick={() => setActiveTab('accuracy')}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 transition-all ${
            activeTab === 'accuracy'
              ? 'border-blue-600 text-blue-700 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Target className="h-4 w-4" />
          Engine Accuracy Evaluation (Benchmark Harness)
        </button>
      </div>

      {activeTab === 'accuracy' ? (
        /* ACCURACY BENCHMARK PAGE (Section 5.B Evaluation Harness) */
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="flex items-center justify-between border-b pb-4 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Overlap Engine Comparative Accuracy (Labelled Evaluation Dataset)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Performance across (Rules Only) vs (Rules + Fuzzy) vs (Rules + Fuzzy + Multilingual Semantic)
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={loadAccuracy}
                loading={accuracyLoading}
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1" /> Re-run Harness
              </Button>
            </div>

            {accuracyLoading || !accuracyData ? (
              <LoadingBlock label="Evaluating precision, recall, and F1 across 3 layers..." />
            ) : (
              <div className="space-y-6">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-y border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                        <th className="py-3 px-4">Engine Pipeline Configuration</th>
                        <th className="py-3 px-3 text-center">Precision</th>
                        <th className="py-3 px-3 text-center">Recall</th>
                        <th className="py-3 px-3 text-center font-bold text-blue-900">F1 Score</th>
                        <th className="py-3 px-3 text-center">True Positives</th>
                        <th className="py-3 px-3 text-center">False Positives</th>
                        <th className="py-3 px-3 text-center">False Negatives</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {accuracyData.results.map((row, i) => (
                        <tr
                          key={i}
                          className={
                            i === accuracyData.results.length - 1
                              ? 'bg-blue-50/50 font-semibold'
                              : 'hover:bg-slate-50'
                          }
                        >
                          <td className="py-3 px-4">
                            <span className="font-bold text-slate-900">{row.method}</span>
                          </td>
                          <td className="py-3 px-3 text-center">
                            {(row.precision * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-3 text-center">
                            {(row.recall * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-3 text-center font-extrabold text-blue-700">
                            {(row.f1_score * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-3 text-center text-emerald-700">{row.tp}</td>
                          <td className="py-3 px-3 text-center text-red-600">{row.fp}</td>
                          <td className="py-3 px-3 text-center text-amber-600">{row.fn}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="rounded-lg bg-slate-50 p-4 border border-slate-200 text-xs text-slate-700 space-y-1">
                  <p className="font-bold text-slate-900">Evaluation Insight:</p>
                  <p>{accuracyData.summary}</p>
                  <p className="text-[11px] text-slate-500 pt-1">
                    Dataset: {accuracyData.total_labelled_pairs} labelled ground-truth pairs spanning exact AICTE IDs, institution aliases/misspellings, and multilingual complaint texts.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ACTIVE OVERLAPS VIEW */
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Input
              className="w-full max-w-sm"
              placeholder="Search overlaps by college, case no, subject..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Select
              className="w-full max-w-xs"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Review Statuses</option>
              {reviewStatuses.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </Select>
          </div>

          {loading ? (
            <LoadingBlock label="Loading overlap intelligence..." />
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No overlaps matching filters"
              description="Click 'Re-scan All Complaints' to evaluate matches across the entire 650-complaint database."
            />
          ) : (
            <div className="space-y-3">
              {filtered.map((overlap) => (
                <div
                  key={overlap.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs hover:border-slate-300 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-purple-50 p-1.5 text-purple-600">
                        <GitBranch className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="text-sm font-bold text-slate-900 font-mono">
                          {overlap.complaint_1} ↔ {overlap.complaint_2}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {overlap.relationship_type} · Created {formatDate(overlap.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-bold text-white">
                        {percent(overlap.similarity_score)} Match
                      </span>
                      <Badge className={reviewStatusClass(overlap.review_status)}>
                        {overlap.review_status}
                      </Badge>
                      <Button
                        size="sm"
                        className="bg-navy hover:bg-slate-800 text-white font-semibold text-xs ml-2 shadow-2xs"
                        onClick={() => setCoordinationOverlapId(overlap.id)}
                      >
                        <Users className="h-3.5 w-3.5 mr-1 text-amber-400" />
                        Open Coordination Room
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <span className="text-xs font-mono font-bold text-blue-700">{overlap.complaint_1}</span>
                      <p className="text-xs font-bold text-slate-900 mt-0.5">{overlap.complaint_1_institution}</p>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2">{overlap.complaint_1_subject}</p>
                      <p className="text-[10px] text-slate-400 mt-2 font-medium">Bureau: {overlap.complaint_1_bureau}</p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-3">
                      <span className="text-xs font-mono font-bold text-blue-700">{overlap.complaint_2}</span>
                      <p className="text-xs font-bold text-slate-900 mt-0.5">{overlap.complaint_2_institution}</p>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2">{overlap.complaint_2_subject}</p>
                      <p className="text-[10px] text-slate-400 mt-2 font-medium">Bureau: {overlap.complaint_2_bureau}</p>
                    </div>
                  </div>

                  {overlap.matching_reasons && overlap.matching_reasons.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
                      <span className="text-[10px] font-bold text-slate-500 uppercase mr-1">Plain-Language Reasons:</span>
                      {overlap.matching_reasons.map((r, i) => (
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

      {/* Coordination Room Modal */}
      {coordinationOverlapId && (
        <CoordinationRoomModal
          overlapId={coordinationOverlapId}
          open={Boolean(coordinationOverlapId)}
          onClose={() => setCoordinationOverlapId(null)}
          onUpdated={load}
        />
      )}
    </div>
  )
}
