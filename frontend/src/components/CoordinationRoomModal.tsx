import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  Calendar,
  CheckCircle,
  Clock,
  MessageSquare,
  PhoneCall,
  Send,
  Shield,
  UserCheck,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { formatDate } from '../lib/utils'
import { Badge, Button, Textarea } from './ui'

interface CoordinationRoomData {
  overlap_id: string
  similarity_score: number
  review_status: string
  matching_reasons: string[]
  lead_bureau_code: string | null
  playbook_suggestion: {
    suggested_lead: string
    reason: string
  }
  differences: Array<{
    field: string
    case_1_value: string
    case_2_value: string
    is_different: boolean
  }>
  case_1: {
    id: string
    complaint_number: string
    subject: string
    description: string
    summary: string | null
    category: string
    current_status: string
    priority: string
    assigned_bureau_name: string
    assigned_bureau_code: string
    assigned_officer_name: string
    received_date: string
    expected_disposal_date: string
    next_action: string | null
    institution_name: string
  }
  case_2: {
    id: string
    complaint_number: string
    subject: string
    description: string
    summary: string | null
    category: string
    current_status: string
    priority: string
    assigned_bureau_name: string
    assigned_bureau_code: string
    assigned_officer_name: string
    received_date: string
    expected_disposal_date: string
    next_action: string | null
    institution_name: string
  }
  merged_timeline: Array<{
    id: string
    action_type: string
    remarks: string
    timestamp: string
    officer: string
    bureau: string
    case_number: string
    hash: string | null
  }>
  messages: Array<{
    id: string
    author: string
    role: string
    bureau: string | null
    body: string
    created_at: string
  }>
}

interface CoordinationRoomModalProps {
  overlapId: string
  open: boolean
  onClose: () => void
  onUpdated?: () => void
}

export default function CoordinationRoomModal({
  overlapId,
  open,
  onClose,
  onUpdated,
}: CoordinationRoomModalProps) {
  const [data, setData] = useState<CoordinationRoomData | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatInput, setChatInput] = useState('')
  const [sendingMsg, setSendingMsg] = useState(false)

  // Intent Card State
  const [selectedCaseForIntent, setSelectedCaseForIntent] = useState<'case_1' | 'case_2'>('case_1')
  const [intentType, setIntentType] = useState<string>('Hearing')
  const [intentDate, setIntentDate] = useState<string>('')
  const [intentRemarks, setIntentRemarks] = useState<string>('')
  const [intentConflicts, setIntentConflicts] = useState<string[]>([])
  const [savingIntent, setSavingIntent] = useState(false)

  // Joint Decision State
  const [decisionModalOpen, setDecisionModalOpen] = useState(false)
  const [decisionText, setDecisionText] = useState('')
  const [decisionLeadBureau, setDecisionLeadBureau] = useState('REG')
  const [decisionPauseDate, setDecisionPauseDate] = useState('')
  const [recordingDecision, setRecordingDecision] = useState(false)

  const loadRoom = async () => {
    setLoading(true)
    try {
      const res = await api.get<CoordinationRoomData>(
        `/api/overlaps/${overlapId}/coordination-room`,
      )
      setData(res.data)
      setDecisionLeadBureau(res.data.lead_bureau_code || res.data.playbook_suggestion.suggested_lead || 'REG')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open && overlapId) {
      void loadRoom()
    }
  }, [open, overlapId])

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return
    setSendingMsg(true)
    try {
      await api.post(`/api/overlaps/${overlapId}/messages`, {
        body: chatInput.trim(),
        mentions: [],
      })
      setChatInput('')
      await loadRoom()
      toast.success('Message posted to Coordination Room')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSendingMsg(false)
    }
  }

  const handleProposeOrAcceptLead = async (action: 'PROPOSE' | 'ACCEPT') => {
    if (!data) return
    const leadCode = data.playbook_suggestion.suggested_lead || 'REG'
    try {
      await api.post(`/api/overlaps/${overlapId}/lead`, {
        lead_bureau_code: leadCode,
        reason: data.playbook_suggestion.reason,
      })
      toast.success(
        action === 'PROPOSE'
          ? `Proposed ${leadCode} as Lead Bureau`
          : `Accepted ${leadCode} as Lead Bureau`,
      )
      await loadRoom()
      onUpdated?.()
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const handleRequestCall = async () => {
    try {
      await api.post(`/api/overlaps/${overlapId}/request-call`)
      toast.success('Quick call request notified to counterpart case officer.')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const handlePostIntent = async () => {
    if (!data || !intentDate) {
      toast.error('Select a planned date')
      return
    }
    const targetCaseId =
      selectedCaseForIntent === 'case_1' ? data.case_1.id : data.case_2.id
    setSavingIntent(true)
    try {
      const res = await api.post<{ conflicts_detected: string[] }>(
        `/api/complaints/${targetCaseId}/intents`,
        {
          intent_type: intentType,
          planned_date: intentDate,
          remarks: intentRemarks,
        },
      )
      const detected = res.data.conflicts_detected || []
      setIntentConflicts(detected)
      if (detected.length > 0) {
        toast.warning(
          `Action intent registered with ${detected.length} conflict warning(s)`,
        )
      } else {
        toast.success(`Action intent '${intentType}' registered without conflict!`)
      }
      await loadRoom()
      onUpdated?.()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSavingIntent(false)
    }
  }

  const handleRecordJointDecision = async () => {
    if (!decisionText.trim()) {
      toast.error('Enter joint decision text')
      return
    }
    setRecordingDecision(true)
    try {
      await api.post(`/api/overlaps/${overlapId}/decide`, {
        decision_text: decisionText.trim(),
        lead_bureau_code: decisionLeadBureau,
        pause_until: decisionPauseDate || null,
      })
      toast.success('Joint decision synced to BOTH cases with SHA-256 hash chaining!')
      setDecisionModalOpen(false)
      await loadRoom()
      onUpdated?.()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setRecordingDecision(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col rounded-xl bg-white shadow-2xl border border-slate-200 overflow-hidden my-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b bg-navy px-6 py-4 text-white">
          <div className="flex items-center gap-3">
            <span className="rounded-lg bg-amber-400 p-2 text-navy font-bold">
              <Shield className="h-5 w-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold">Cross-Bureau Coordination Room</h3>
                <Badge className="bg-amber-400/20 text-amber-300 border-amber-400/40 text-[11px]">
                  Conf: {data ? `${Math.round(data.similarity_score * 100)}%` : '—'}
                </Badge>
                <Badge className="bg-blue-400/20 text-blue-200 border-blue-400/40 text-[11px]">
                  Status: {data?.review_status}
                </Badge>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                {data ? `${data.case_1.institution_name} · Need-to-Know Shared Workspace` : 'Loading...'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRequestCall}
              className="flex items-center gap-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-white border border-slate-700 transition-colors"
            >
              <PhoneCall className="h-3.5 w-3.5 text-emerald-400" />
              Request Quick Call
            </button>
            <button
              onClick={() => setDecisionModalOpen(true)}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3.5 py-1.5 text-xs font-bold text-white transition-colors shadow-sm"
            >
              <CheckCircle className="h-4 w-4" />
              Record Joint Decision
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {loading || !data ? (
          <div className="p-12 text-center text-slate-500">
            <Clock className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-2" />
            Loading Coordination Room details...
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Playbook Lead Recommendation Banner */}
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-blue-200 bg-blue-50/70 p-4">
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-blue-600 p-2 text-white">
                  <UserCheck className="h-4 w-4" />
                </span>
                <div>
                  <h4 className="text-sm font-bold text-blue-950">
                    Lead-Bureau Playbook Suggestion: {data.playbook_suggestion.suggested_lead}
                  </h4>
                  <p className="text-xs text-blue-800 mt-0.5">
                    {data.playbook_suggestion.reason}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleProposeOrAcceptLead('PROPOSE')}
                >
                  Propose Lead ({data.playbook_suggestion.suggested_lead})
                </Button>
                <Button
                  size="sm"
                  className="bg-blue-700 hover:bg-blue-800 text-white"
                  onClick={() => handleProposeOrAcceptLead('ACCEPT')}
                >
                  Accept Lead
                </Button>
              </div>
            </div>

            {/* Side-by-Side Comparison */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Side-by-Side Case Comparison (Differences Highlighted)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Case 1 */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between border-b pb-2 mb-3">
                    <span className="text-xs font-bold text-blue-700 font-mono">
                      {data.case_1.complaint_number}
                    </span>
                    <Badge className="bg-slate-100 text-slate-800 text-[10px]">
                      {data.case_1.assigned_bureau_name}
                    </Badge>
                  </div>
                  <h5 className="text-sm font-bold text-slate-900 mb-1">
                    {data.case_1.subject}
                  </h5>
                  <p className="text-xs text-slate-600 mb-3">
                    {data.case_1.summary || data.case_1.description}
                  </p>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Category:</span>
                      <span className="font-medium text-slate-900">{data.case_1.category}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Current Status:</span>
                      <span className="font-medium text-slate-900">{data.case_1.current_status}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Assigned Officer:</span>
                      <span className="font-medium text-slate-900">{data.case_1.assigned_officer_name}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">SLA Due Date:</span>
                      <span className="font-medium text-slate-900">{formatDate(data.case_1.expected_disposal_date)}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Next Action:</span>
                      <span className="font-medium text-slate-900">{data.case_1.next_action || 'Pending review'}</span>
                    </div>
                  </div>
                </div>

                {/* Case 2 */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between border-b pb-2 mb-3">
                    <span className="text-xs font-bold text-blue-700 font-mono">
                      {data.case_2.complaint_number}
                    </span>
                    <Badge className="bg-slate-100 text-slate-800 text-[10px]">
                      {data.case_2.assigned_bureau_name}
                    </Badge>
                  </div>
                  <h5 className="text-sm font-bold text-slate-900 mb-1">
                    {data.case_2.subject}
                  </h5>
                  <p className="text-xs text-slate-600 mb-3">
                    {data.case_2.summary || data.case_2.description}
                  </p>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Category:</span>
                      <span className="font-medium text-slate-900">{data.case_2.category}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Current Status:</span>
                      <span className="font-medium text-slate-900">{data.case_2.current_status}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">Assigned Officer:</span>
                      <span className="font-medium text-slate-900">{data.case_2.assigned_officer_name}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-100">
                      <span className="text-slate-500">SLA Due Date:</span>
                      <span className="font-medium text-slate-900">{formatDate(data.case_2.expected_disposal_date)}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Next Action:</span>
                      <span className="font-medium text-slate-900">{data.case_2.next_action || 'Pending review'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Intent Card (Section 5.C) */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  Action Intent Card: Register Regulatory Intent & Conflict Detection
                </h4>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500">Target:</span>
                  <select
                    value={selectedCaseForIntent}
                    onChange={(e) => setSelectedCaseForIntent(e.target.value as 'case_1' | 'case_2')}
                    className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs font-medium"
                  >
                    <option value="case_1">{data.case_1.complaint_number} ({data.case_1.assigned_bureau_code})</option>
                    <option value="case_2">{data.case_2.complaint_number} ({data.case_2.assigned_bureau_code})</option>
                  </select>
                </div>
              </div>

              {/* Chips */}
              <div className="flex flex-wrap items-center gap-2 mb-3">
                {['Notice', 'Inspection', 'Hearing', 'Penalty', 'Closure', 'Transfer'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setIntentType(type)}
                    className={`rounded-full px-3 py-1 text-xs font-semibold transition-all ${
                      intentType === type
                        ? 'bg-navy text-white shadow-sm'
                        : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {type}
                  </button>
                ))}
                <input
                  type="date"
                  value={intentDate}
                  onChange={(e) => setIntentDate(e.target.value)}
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-800"
                />
                <input
                  type="text"
                  placeholder="Optional remarks/details..."
                  value={intentRemarks}
                  onChange={(e) => setIntentRemarks(e.target.value)}
                  className="flex-1 min-w-[180px] rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs"
                />
                <Button
                  size="sm"
                  onClick={handlePostIntent}
                  loading={savingIntent}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Register Intent
                </Button>
              </div>

              {/* Soft Conflict Warning Banner */}
              {intentConflicts.length > 0 && (
                <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 mt-2 space-y-1">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    Conflict Warning Detected with Counterpart Bureau:
                  </div>
                  {intentConflicts.map((c, i) => (
                    <div key={i} className="text-xs text-amber-800 pl-6">
                      • {c}
                    </div>
                  ))}
                  <p className="text-[11px] text-amber-700 italic pl-6 mt-1">
                    (Soft warning only — officer retains statutory authority. Consider synchronizing dates.)
                  </p>
                </div>
              )}
            </div>

            {/* Bottom Row: Merged Hash-Chained Timeline & Threaded Chat */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Timeline */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-slate-400" />
                  Merged Case Actions Timeline (SHA-256 Chained)
                </h4>
                <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                  {data.merged_timeline.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-slate-200 bg-white p-2.5 text-xs shadow-xs"
                    >
                      <div className="flex items-center justify-between text-slate-500 mb-1">
                        <span className="font-semibold text-slate-800">
                          {item.action_type} · {item.case_number}
                        </span>
                        <span>{formatDate(item.timestamp)}</span>
                      </div>
                      <p className="text-slate-700">{item.remarks}</p>
                      <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                        <span>By {item.officer} ({item.bureau})</span>
                        {item.hash && <span>Hash: {item.hash.slice(0, 12)}…</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Threaded Chat */}
              <div className="flex flex-col h-[280px] rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                <div className="bg-slate-100 px-3 py-2 border-b text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5 text-blue-600" />
                  Coordination Discussion (@Mentions Enabled)
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-2 text-xs">
                  {data.messages.length === 0 ? (
                    <div className="text-center text-slate-400 py-8">
                      No coordination messages yet. Post a note or suggestion below.
                    </div>
                  ) : (
                    data.messages.map((m) => (
                      <div key={m.id} className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="font-semibold text-slate-800">
                            {m.author} {m.bureau ? `(${m.bureau})` : ''}
                          </span>
                          <span className="text-slate-400">{formatDate(m.created_at)}</span>
                        </div>
                        <p className="text-slate-700 whitespace-pre-wrap">{m.body}</p>
                      </div>
                    ))
                  )}
                </div>
                <div className="border-t p-2 flex gap-2 bg-slate-50">
                  <input
                    type="text"
                    placeholder="Write a message to counterpart officer... (@name to mention)"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && void handleSendMessage()}
                    className="flex-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs focus:outline-blue-500"
                  />
                  <Button
                    size="sm"
                    onClick={handleSendMessage}
                    loading={sendingMsg}
                    className="bg-navy hover:bg-slate-800 text-white"
                  >
                    <Send className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Joint Decision Modal */}
        {decisionModalOpen && (
          <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-base font-bold text-slate-900">
                  Record Joint Bureau Decision
                </h4>
                <button onClick={() => setDecisionModalOpen(false)}>
                  <X className="h-5 w-5 text-slate-400" />
                </button>
              </div>
              <p className="text-xs text-slate-600 mb-3">
                This decision will be cryptographically written to BOTH cases' timelines
                with SHA-256 hash chaining.
              </p>
              <div className="space-y-3 mb-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700">Lead Bureau</label>
                  <select
                    value={decisionLeadBureau}
                    onChange={(e) => setDecisionLeadBureau(e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-2 text-xs"
                  >
                    <option value="REG">Regulation Bureau (REG)</option>
                    <option value="PGRC">Public Grievance Redressal Cell (PGRC)</option>
                    <option value="APB">Approval Process Bureau (APB)</option>
                    <option value="RO">Regional Office (RO)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700">Decision Text</label>
                  <Textarea
                    rows={3}
                    placeholder="e.g. RB leads regulatory enquiry; PGRC conducts joint hearing on 15 Nov..."
                    value={decisionText}
                    onChange={(e) => setDecisionText(e.target.value)}
                    className="mt-1 text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700">Pause Counterpart Case Until (Optional)</label>
                  <input
                    type="date"
                    value={decisionPauseDate}
                    onChange={(e) => setDecisionPauseDate(e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-2 text-xs"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setDecisionModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                  onClick={handleRecordJointDecision}
                  loading={recordingDecision}
                >
                  Confirm & Sync Both Cases
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
