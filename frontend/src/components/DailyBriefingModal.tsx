import { useEffect, useState } from 'react'
import { CheckCircle2, ChevronRight, Sparkles, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { Button } from './ui'

interface DailyBriefingData {
  generated_at: string
  officer_name: string
  officer_bureau: string
  read_time_seconds: number
  headline: string
  items: Array<{
    type: string
    title: string
    description: string
    urgency: string
    case_id: string | null
    deep_link: string
    action_label: string
  }>
}

interface DailyBriefingModalProps {
  open: boolean
  onClose: () => void
}

export default function DailyBriefingModal({ open, onClose }: DailyBriefingModalProps) {
  const navigate = useNavigate()
  const [data, setData] = useState<DailyBriefingData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (open) {
      setLoading(true)
      api.get<DailyBriefingData>('/api/dashboard/daily-briefing')
        .then((res) => setData(res.data))
        .catch((err) => toast.error(errorMessage(err)))
        .finally(() => setLoading(false))
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
      <div className="w-full max-w-xl rounded-xl bg-white p-6 shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between border-b pb-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-purple-100 p-1.5 text-purple-700">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Daily 60-Second Officer Briefing
              </h3>
              <p className="text-[11px] text-slate-500">
                Exception-focused intelligence digest for {data?.officer_name || 'Officer'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading || !data ? (
          <div className="py-12 text-center text-xs text-slate-500">
            Generating your 60-second operational briefing...
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg bg-purple-50/60 p-3 border border-purple-100">
              <p className="text-xs font-semibold text-purple-950">{data.headline}</p>
            </div>

            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {data.items.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 flex flex-col items-center">
                  <CheckCircle2 className="h-8 w-8 text-emerald-500 mb-2" />
                  All clear! No urgent exceptions requiring attention today.
                </div>
              ) : (
                data.items.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-lg border border-slate-200 p-3 hover:border-slate-300 transition-colors bg-white shadow-2xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          item.urgency === 'High' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {item.type}
                        </span>
                        <p className="text-xs font-bold text-slate-900">{item.title}</p>
                      </div>
                      <p className="text-[11px] text-slate-600 mt-1">{item.description}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="ml-3 shrink-0 text-xs text-blue-600 border-blue-200 hover:bg-blue-50"
                      onClick={() => {
                        onClose()
                        navigate(item.deep_link)
                      }}
                    >
                      {item.action_label} <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        <div className="mt-5 flex items-center justify-between border-t pt-3">
          <span className="text-[11px] text-slate-400">Target read time: ≤60 seconds</span>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
