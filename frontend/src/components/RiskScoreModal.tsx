import { useEffect, useState } from 'react'
import { ShieldAlert, X } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { Badge, Button } from './ui'

interface RiskScoreData {
  risk_score: number
  risk_level: string
  total_complaints: number
  factor_breakdown: Array<{
    factor: string
    points: number
    description: string
  }>
}

interface RiskScoreModalProps {
  institutionId: string
  institutionName: string
  open: boolean
  onClose: () => void
}

export default function RiskScoreModal({
  institutionId,
  institutionName,
  open,
  onClose,
}: RiskScoreModalProps) {
  const [data, setData] = useState<RiskScoreData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (open && institutionId) {
      setLoading(true)
      api.get<RiskScoreData>(`/api/institutions/${institutionId}/risk-score`)
        .then((res) => setData(res.data))
        .catch((err) => toast.error(errorMessage(err)))
        .finally(() => setLoading(false))
    }
  }, [open, institutionId])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between border-b pb-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-amber-600" />
            <h3 className="text-base font-bold text-slate-900">
              Explainable Institution Risk Score
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-xs font-semibold text-slate-600 mb-4">{institutionName}</p>

        {loading || !data ? (
          <div className="py-8 text-center text-xs text-slate-500">
            Computing explainable risk factor breakdown...
          </div>
        ) : (
          <div className="space-y-4">
            {/* Score Ring / Badge */}
            <div className="flex items-center justify-between rounded-xl bg-slate-50 p-4 border border-slate-200">
              <div>
                <span className="text-3xl font-extrabold text-slate-900">
                  {data.risk_score}
                </span>
                <span className="text-sm font-semibold text-slate-500"> / 100</span>
                <p className="text-xs text-slate-500 mt-0.5">Calculated Regulatory Risk</p>
              </div>
              <Badge
                className={`text-xs px-3 py-1 font-bold ${
                  data.risk_level === 'High'
                    ? 'bg-red-100 text-red-800'
                    : data.risk_level === 'Medium'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {data.risk_level} Risk Level
              </Badge>
            </div>

            {/* Factor Breakdown */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Factor Breakdown (Explainable Model)
              </h4>
              <div className="space-y-2">
                {data.factor_breakdown.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No adverse risk factors detected.</p>
                ) : (
                  data.factor_breakdown.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-slate-200 p-2.5 text-xs bg-white"
                    >
                      <div>
                        <p className="font-semibold text-slate-800">{item.factor}</p>
                        <p className="text-[11px] text-slate-500">{item.description}</p>
                      </div>
                      <span className="rounded bg-amber-50 px-2 py-0.5 font-bold text-amber-700">
                        +{item.points} pts
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="text-[11px] text-slate-400 border-t pt-2">
              Based on {data.total_complaints} complaint records across Regulation, PGRC, and Regional bureaus.
            </div>
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
