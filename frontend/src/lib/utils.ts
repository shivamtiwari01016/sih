import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value.length <= 10 ? `${value}T00:00:00` : value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export function addDaysISO(days: number) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

export function statusClass(status?: string | null) {
  const map: Record<string, string> = {
    Received: 'bg-amber-100 text-amber-800',
    'Under Scrutiny': 'bg-orange-100 text-orange-800',
    'Under Process': 'bg-blue-100 text-blue-800',
    'Awaiting Information': 'bg-purple-100 text-purple-800',
    Transferred: 'bg-indigo-100 text-indigo-800',
    Escalated: 'bg-red-100 text-red-800',
    Disposed: 'bg-green-100 text-green-800',
    Closed: 'bg-gray-200 text-gray-700',
  }
  return map[status || ''] || 'bg-gray-100 text-gray-700'
}

export function priorityClass(priority?: string | null) {
  const map: Record<string, string> = {
    Low: 'bg-slate-100 text-slate-700',
    Medium: 'bg-blue-100 text-blue-800',
    High: 'bg-orange-100 text-orange-800',
    Urgent: 'bg-red-100 text-red-800',
  }
  return map[priority || ''] || 'bg-gray-100 text-gray-700'
}

export function severityClass(severity?: string | null) {
  const map: Record<string, string> = {
    Info: 'bg-blue-100 text-blue-800',
    Warning: 'bg-amber-100 text-amber-800',
    Critical: 'bg-red-100 text-red-800',
  }
  return map[severity || ''] || 'bg-gray-100 text-gray-700'
}

export function reviewStatusClass(status?: string | null) {
  const map: Record<string, string> = {
    Suggested: 'bg-amber-100 text-amber-800',
    'Confirmed Related': 'bg-green-100 text-green-800',
    Rejected: 'bg-gray-200 text-gray-700',
    'Requires Further Review': 'bg-purple-100 text-purple-800',
    Pending: 'bg-amber-100 text-amber-800',
    Approved: 'bg-blue-100 text-blue-800',
    Completed: 'bg-green-100 text-green-800',
  }
  return map[status || ''] || 'bg-gray-100 text-gray-700'
}

export function percent(value?: number | null) {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value * 100)}%`
}
