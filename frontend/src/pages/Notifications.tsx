import { useCallback, useEffect, useState } from 'react'
import { Bell, BellOff, CheckCheck, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { api, errorMessage } from '../lib/api'
import { formatDateTime, severityClass } from '../lib/utils'
import {
  Badge,
  Button,
  EmptyState,
  ErrorBanner,
  LoadingBlock,
  PageHeader,
} from '../components/ui'

interface Notification {
  id: string
  type: string | null
  title: string
  message: string
  severity: string | null
  complaint_id: string | null
  complaint_number: string | null
  read: boolean
  created_at: string | null
  read_at: string | null
}

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get<Notification[]>('/api/notifications', {
        params: { limit: 200, ...(unreadOnly ? { unread_only: true } : {}) },
      })
      setNotifications(response.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [unreadOnly])

  useEffect(() => {
    void load()
  }, [load])

  const markRead = async (notification: Notification) => {
    if (notification.read) return
    try {
      await api.post(`/api/notifications/${notification.id}/read`)
      setNotifications((current) =>
        current.map((item) =>
          item.id === notification.id
            ? { ...item, read: true, read_at: new Date().toISOString() }
            : item,
        ),
      )
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const markAllRead = async () => {
    setBusy(true)
    try {
      const response = await api.post('/api/notifications/read-all')
      toast.success(response.data.message || 'All notifications marked as read')
      await load()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const unread = notifications.filter((notification) => !notification.read).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Alerts & Notifications"
        subtitle="Assignments, escalations, transfers and deadline alerts"
        actions={
          <>
            <Button variant="outline" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
            <Button variant="secondary" loading={busy} onClick={() => void markAllRead()}>
              <CheckCheck className="h-4 w-4" /> Mark all read
            </Button>
          </>
        }
      />

      <ErrorBanner message={error} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300"
            checked={unreadOnly}
            onChange={(event) => setUnreadOnly(event.target.checked)}
          />
          Show unread only
        </label>
        <p className="text-sm text-slate-500">
          {unread} unread of {notifications.length} notification(s)
        </p>
      </div>

      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <LoadingBlock label="Loading notifications…" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <EmptyState
            title={unreadOnly ? 'No unread notifications' : 'No notifications yet'}
            description="Notifications appear when cases are assigned, escalated, transferred or approaching deadlines."
          />
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`flex gap-3 rounded-lg border bg-white p-4 shadow-sm transition ${
                notification.read ? 'border-slate-200' : 'border-blue-200 ring-1 ring-blue-50'
              }`}
            >
              <span
                className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                  notification.read ? 'bg-slate-100 text-slate-400' : 'bg-blue-50 text-blue-600'
                }`}
              >
                {notification.read ? (
                  <BellOff className="h-4 w-4" />
                ) : (
                  <Bell className="h-4 w-4" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-slate-900">{notification.title}</p>
                  {notification.severity && (
                    <Badge className={severityClass(notification.severity)}>
                      {notification.severity}
                    </Badge>
                  )}
                  {notification.type && (
                    <span className="text-[11px] uppercase tracking-wide text-slate-400">
                      {notification.type}
                    </span>
                  )}
                  {!notification.read && (
                    <span className="h-2 w-2 rounded-full bg-blue-500" aria-label="Unread" />
                  )}
                </div>
                <p className="mt-1 text-sm text-slate-700">{notification.message}</p>
                <p className="mt-1 text-[11px] text-slate-400">
                  {formatDateTime(notification.created_at)}
                  {notification.complaint_number ? ` · ${notification.complaint_number}` : ''}
                  {notification.read_at
                    ? ` · read ${formatDateTime(notification.read_at)}`
                    : ''}
                </p>
              </div>
              {!notification.read && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => void markRead(notification)}
                >
                  Mark read
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
