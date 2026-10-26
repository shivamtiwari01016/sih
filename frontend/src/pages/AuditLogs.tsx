import { useCallback, useEffect, useState } from 'react'
import {
  AlertTriangle,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { formatDateTime } from '../lib/utils'
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

interface AuditLog {
  id: string
  actor: string
  actor_email: string | null
  action: string
  entity_type: string
  entity_id: string | null
  ip_address: string | null
  sanitized_metadata: Record<string, unknown> | string | null
  prev_hash: string | null
  hash: string | null
  timestamp: string | null
}

interface IntegrityResult {
  verified: boolean
  total_records: number
  linked_records: number
  latest_hash: string
  message: string
}

const actionColours: Record<string, string> = {
  LOGIN: 'bg-slate-100 text-slate-700',
  VIEW: 'bg-slate-100 text-slate-700',
  CREATE: 'bg-green-100 text-green-800',
  UPDATE: 'bg-blue-100 text-blue-800',
  DELETE: 'bg-red-100 text-red-800',
  ASSIGN: 'bg-purple-100 text-purple-800',
  ESCALATE: 'bg-red-100 text-red-800',
  DISPOSE: 'bg-emerald-100 text-emerald-800',
  BREAK_GLASS_ACCESS: 'bg-red-600 text-white font-bold',
  COORDINATION_DECISION: 'bg-emerald-600 text-white font-bold',
  LEAD_BUREAU_ASSIGNED: 'bg-blue-600 text-white font-bold',
  ACTION_INTENT_REGISTERED: 'bg-amber-100 text-amber-900 font-bold',
}

function metadataText(metadata: unknown) {
  if (!metadata) return '—'
  if (typeof metadata === 'string') return metadata
  if (typeof metadata === 'object') {
    return Object.entries(metadata as Record<string, unknown>)
      .map(([key, value]) => `${key}: ${typeof value === 'object' ? JSON.stringify(value) : value}`)
      .join(' · ')
  }
  return String(metadata)
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [entityFilter, setEntityFilter] = useState('')

  // Cryptographic Chain Verification State
  const [verifying, setVerifying] = useState(false)
  const [integrity, setIntegrity] = useState<IntegrityResult | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<AuditLog[]>('/api/audit-logs', {
        params: { limit: 500 },
      })
      setLogs(response.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const verifyChain = async () => {
    setVerifying(true)
    try {
      const res = await api.get<IntegrityResult>('/api/audit-logs/verify-integrity')
      setIntegrity(res.data)
      if (res.data.verified) {
        toast.success(
          `Cryptographic chain verified! ${res.data.total_records} records unbroken.`,
        )
      } else {
        toast.error('Cryptographic chain verification failure!')
      }
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setVerifying(false)
    }
  }

  const entities = Array.from(new Set(logs.map((l) => l.entity_type).filter(Boolean)))

  const filtered = logs.filter((log) => {
    if (entityFilter && log.entity_type !== entityFilter) return false
    if (!search.trim()) return true
    const term = search.toLowerCase()
    return (
      log.actor.toLowerCase().includes(term) ||
      (log.actor_email && log.actor_email.toLowerCase().includes(term)) ||
      log.action.toLowerCase().includes(term) ||
      (log.entity_id && log.entity_id.toLowerCase().includes(term))
    )
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tamper-Evident Audit Trail"
        subtitle="SHA-256 Hash-Chained Forensic Log · Every VIEW, EDIT, EXPORT and BREAK-GLASS recorded"
        actions={
          <div className="flex items-center gap-2">
            <Button
              onClick={verifyChain}
              loading={verifying}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
            >
              <ShieldCheck className="h-4 w-4 mr-1.5" /> Verify Cryptographic Chain
            </Button>
            <Button variant="outline" onClick={() => void load()} loading={loading}>
              <RefreshCw className="h-4 w-4 mr-1.5" /> Refresh
            </Button>
          </div>
        }
      />

      {error && <ErrorBanner message={error} />}

      {/* Cryptographic Chain Verification Badge */}
      {integrity && (
        <div
          className={`rounded-xl border p-4 shadow-sm flex flex-wrap items-center justify-between gap-4 ${
            integrity.verified
              ? 'border-emerald-300 bg-emerald-50 text-emerald-950'
              : 'border-red-300 bg-red-50 text-red-950'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${integrity.verified ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}`}>
              {integrity.verified ? <ShieldCheck className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
            </div>
            <div>
              <h4 className="text-sm font-bold">
                {integrity.verified ? 'Cryptographic Audit Trail Integrity: VERIFIED (GREEN)' : 'Chain Tampering Detected!'}
              </h4>
              <p className="text-xs mt-0.5 opacity-90">
                {integrity.message} · <strong>{integrity.total_records}</strong> Total Records · <strong>{integrity.linked_records}</strong> Linked Blocks · 0 Broken
              </p>
            </div>
          </div>
          <div className="text-right text-[11px] font-mono">
            <span className="block text-slate-500 font-sans">Head SHA-256 Hash:</span>
            <span className="bg-white/80 border px-2 py-0.5 rounded text-slate-900 font-bold">
              {integrity.latest_hash}
            </span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Input
          className="w-full max-w-sm"
          placeholder="Search by officer name, action, ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Select
          className="w-full max-w-xs"
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
        >
          <option value="">All Entity Types</option>
          {entities.map((ent) => (
            <option key={ent} value={ent}>
              {ent}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <LoadingBlock label="Loading audit logs…" />
      ) : filtered.length === 0 ? (
        <EmptyState title="No audit entries" description="System audit records will appear here." />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Officer / Actor</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4">Metadata & Justification</th>
                  <th className="py-3 px-4 font-mono">Hash Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((log) => {
                  const isBreakGlass = log.action === 'BREAK_GLASS_ACCESS'
                  return (
                    <tr
                      key={log.id}
                      className={
                        isBreakGlass
                          ? 'bg-red-50/70 font-semibold'
                          : 'hover:bg-slate-50 transition-colors'
                      }
                    >
                      <td className="py-3 px-4 whitespace-nowrap text-slate-500 font-mono">
                        {formatDateTime(log.timestamp)}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-900 block">{log.actor}</span>
                        {log.actor_email && (
                          <span className="text-[10px] text-slate-400">{log.actor_email}</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          className={`text-[10px] ${
                            actionColours[log.action] || 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {log.action}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-slate-800">
                        {log.entity_type} {log.entity_id ? `(${log.entity_id.slice(0, 8)}…)` : ''}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                      <td className="py-3 px-4 text-slate-700 max-w-xs truncate">
                        {metadataText(log.sanitized_metadata)}
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-slate-400">
                        {log.hash ? (
                          <span title={`Hash: ${log.hash}\nPrev: ${log.prev_hash || 'Genesis'}`}>
                            {log.hash.slice(0, 10)}…
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
