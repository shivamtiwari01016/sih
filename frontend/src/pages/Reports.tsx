import { useCallback, useEffect, useState } from 'react'
import { Download, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  LoadingBlock,
  PageHeader,
  Select,
} from '../components/ui'

interface ReportSummary {
  total: number
  open: number
  disposed: number
  overdue: number
  disposal_rate: number
  average_open_age_days: number
  status_counts: Record<string, number>
  priority_counts: Record<string, number>
  category_counts: Record<string, number>
  institutions: number
  overlap_suggestions: number
}

interface DisposalPoint {
  month: string
  received: number
  disposed: number
}

interface AgeingBucket {
  bucket: string
  count: number
}

interface BureauReport {
  bureau_id: string
  bureau_name: string
  bureau_code: string
  total: number
  open: number
  disposed: number
  overdue: number
  disposal_rate: number
}

const palette = ['#1d4ed8', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2', '#64748b', '#db2777']

export default function Reports() {
  const { isAdmin } = useAuth()
  const [summary, setSummary] = useState<ReportSummary | null>(null)
  const [disposal, setDisposal] = useState<DisposalPoint[]>([])
  const [ageing, setAgeing] = useState<AgeingBucket[]>([])
  const [bureaus, setBureaus] = useState<BureauReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [summaryResponse, disposalResponse, ageingResponse, bureauResponse] =
        await Promise.all([
          api.get<ReportSummary>('/api/reports/summary'),
          api.get<DisposalPoint[]>('/api/reports/disposal'),
          api.get<{ total_open: number; buckets: AgeingBucket[] }>('/api/reports/ageing'),
          api.get<BureauReport[]>('/api/reports/bureaus'),
        ])
      setSummary(summaryResponse.data)
      setDisposal(disposalResponse.data)
      setAgeing(ageingResponse.data.buckets)
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

  const exportCsv = async () => {
    setExporting(true)
    try {
      const response = await api.get('/api/reports/export', {
        params: statusFilter ? { status: statusFilter } : {},
        responseType: 'blob',
      })
      const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `civicresolve-complaints-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      toast.success('CSV report downloaded')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  if (loading && !summary) {
    return <LoadingBlock label="Loading reports…" />
  }

  const statusData = Object.entries(summary?.status_counts || {})
    .filter(([, count]) => count > 0)
    .map(([name, count]) => ({ name, count }))
  const categoryData = Object.entries(summary?.category_counts || {})
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({ name, count }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports & Analytics"
        subtitle="SLA performance, case ageing, disposal trends and bureau comparisons"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            <Select
              className="w-40"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="">All statuses</option>
              {Object.keys(summary?.status_counts || {}).map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
            <Button loading={exporting} onClick={() => void exportCsv()}>
              <Download className="h-4 w-4" /> Export CSV
            </Button>
          </>
        }
      />

      <ErrorBanner message={error} />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {[
          { label: 'Total complaints', value: summary?.total ?? 0 },
          { label: 'Open cases', value: summary?.open ?? 0 },
          { label: 'Disposed / closed', value: summary?.disposed ?? 0 },
          { label: 'Overdue', value: summary?.overdue ?? 0 },
          { label: 'Disposal rate', value: `${summary?.disposal_rate ?? 0}%` },
          { label: 'Avg open age', value: `${summary?.average_open_age_days ?? 0}d` },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {card.label}
            </p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
          <h2 className="text-base font-semibold text-slate-900">Received vs disposed</h2>
          <p className="text-xs text-slate-500">Rolling six months</p>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={disposal} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="received" name="Received" fill="#1d4ed8" radius={[3, 3, 0, 0]} />
                <Bar dataKey="disposed" name="Disposed" fill="#16a34a" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Case status mix</h2>
          <p className="text-xs text-slate-500">Current distribution</p>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="count"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={85}
                  paddingAngle={2}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={entry.name} fill={palette[index % palette.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Ageing of open cases</h2>
          <p className="text-xs text-slate-500">Days since receipt</p>
          <div className="mt-4 space-y-3">
            {ageing.map((bucket, index) => {
              const max = Math.max(...ageing.map((item) => item.count), 1)
              return (
                <div key={bucket.bucket}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{bucket.bucket}</span>
                    <span className="text-slate-500">{bucket.count} case(s)</span>
                  </div>
                  <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.round((bucket.count / max) * 100)}%`,
                        backgroundColor: palette[index % palette.length],
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Complaints by category</h2>
          <p className="text-xs text-slate-500">All registered complaints</p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={categoryData}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                  width={110}
                />
                <Tooltip />
                <Bar dataKey="count" name="Complaints" fill="#7c3aed" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-5 py-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Bureau performance</h2>
            <p className="text-xs text-slate-500">
              Case load, disposal rate and overdue exposure
            </p>
          </div>
          {isAdmin && <Badge className="bg-slate-100 text-slate-600">Admin view</Badge>}
        </div>
        {bureaus.length === 0 ? (
          <EmptyState title="No bureau data" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {['Bureau', 'Total', 'Open', 'Disposed', 'Overdue', 'Disposal rate'].map(
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
                {bureaus.map((bureau) => (
                  <tr key={bureau.bureau_id} className="hover:bg-slate-50">
                    <td className="px-5 py-3">
                      <p className="font-medium text-slate-900">{bureau.bureau_name}</p>
                      <p className="text-xs text-slate-500">{bureau.bureau_code}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-700">{bureau.total}</td>
                    <td className="px-5 py-3 text-slate-700">{bureau.open}</td>
                    <td className="px-5 py-3 text-slate-700">{bureau.disposed}</td>
                    <td className="px-5 py-3">
                      <span
                        className={
                          bureau.overdue > 0 ? 'font-semibold text-red-600' : 'text-slate-700'
                        }
                      >
                        {bureau.overdue}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-green-500"
                            style={{ width: `${Math.min(bureau.disposal_rate, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-600">{bureau.disposal_rate}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
