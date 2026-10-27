import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import Layout from './layouts/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Institutions from './pages/Institutions'
import InstitutionDetail from './pages/InstitutionDetail'
import Complaints from './pages/Complaints'
import Overlaps from './pages/Overlaps'
import Coordination from './pages/Coordination'
import Notifications from './pages/Notifications'
import Reports from './pages/Reports'
import Bureaus from './pages/Bureaus'
import Users from './pages/Users'
import AuditLogs from './pages/AuditLogs'
import Settings from './pages/Settings'
import { useAuth } from './context/AuthContext'

function RequireAuth() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading Samanvay…
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

function RequireAdmin() {
  const { isAdmin } = useAuth()
  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard?tab=my-desk" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="my-desk" element={<Navigate to="/dashboard?tab=my-desk" replace />} />
          <Route path="institutions" element={<Institutions />} />
          <Route path="institutions/:id" element={<InstitutionDetail />} />
          <Route path="complaints" element={<Complaints />} />
          <Route path="overlaps" element={<Overlaps />} />
          <Route path="coordination" element={<Coordination />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="reports" element={<Reports />} />
          <Route path="audit-logs" element={<AuditLogs />} />
          <Route element={<RequireAdmin />}>
            <Route path="bureaus" element={<Bureaus />} />
            <Route path="users" element={<Users />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard?tab=my-desk" replace />} />
    </Routes>
  )
}

export default App
