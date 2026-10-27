import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Filter, RotateCcw, Search } from 'lucide-react'

// Fix Leaflet's default marker icon issue with bundlers
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

export interface CopInstitution {
  id: string
  name: string
  aicte_id: string
  city: string
  state: string
  region: string
  lat: number
  lng: number
  open_cases: number
  risk_score: number
  has_overlap: boolean
}

interface CopMapProps {
  institutions: CopInstitution[]
  onSelectInstitution?: (inst: CopInstitution) => void
  height?: string
}

export default function CopMap({ institutions, onSelectInstitution, height = '520px' }: CopMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const layerGroupRef = useRef<L.LayerGroup | null>(null)

  const [activeFilter, setActiveFilter] = useState<'all' | 'overlap' | 'high_risk'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Initialize Leaflet Map with free OpenStreetMap tile layer
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      // Center of India: Lat 22.0, Lng 78.9629, Zoom: 5
      const map = L.map(mapContainerRef.current, {
        center: [22.0, 78.9629],
        zoom: 5,
        minZoom: 4,
        maxZoom: 18,
        scrollWheelZoom: true,
      })

      // 100% Free OpenStreetMap Standard Tiles (No API key required)
      const osmStandard = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors | AICTE Samanvay',
        maxZoom: 19,
        crossOrigin: true,
      })

      // Free OpenTopoMap Layer
      const openTopo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | Topo: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
        maxZoom: 17,
        crossOrigin: true,
      })

      // Free Humanitarian OSM Layer
      const osmHot = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | Tiles style by <a href="https://www.hotosm.org/">HOT</a>',
        maxZoom: 19,
        crossOrigin: true,
      })

      // Add default free OSM layer
      osmStandard.addTo(map)

      // Add free layer switcher control (standard Leaflet feature)
      L.control.layers(
        {
          'OpenStreetMap (Free)': osmStandard,
          'Humanitarian OSM (Free)': osmHot,
          'OpenTopoMap (Free)': openTopo,
        },
        {},
        { position: 'topright' }
      ).addTo(map)

      // Add scale control
      L.control.scale({ imperial: false, metric: true, position: 'bottomleft' }).addTo(map)

      layerGroupRef.current = L.layerGroup().addTo(map)
      mapInstanceRef.current = map

      // Force recalculation of container dimensions
      const timer = setTimeout(() => {
        map.invalidateSize()
      }, 250)

      return () => {
        clearTimeout(timer)
      }
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // Auto-resize handler for tab switching and viewport resizing
  useEffect(() => {
    if (!mapContainerRef.current) return
    const resizeObserver = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize()
      }
    })
    resizeObserver.observe(mapContainerRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  // Plot markers whenever institutions, filter, or search change
  useEffect(() => {
    const map = mapInstanceRef.current
    const layerGroup = layerGroupRef.current
    if (!map || !layerGroup) return

    layerGroup.clearLayers()

    const filtered = institutions.filter((inst) => {
      if (!inst.lat || !inst.lng) return false
      if (activeFilter === 'overlap' && !inst.has_overlap) return false
      if (activeFilter === 'high_risk' && inst.risk_score < 70) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        return (
          inst.name?.toLowerCase().includes(q) ||
          inst.aicte_id?.toLowerCase().includes(q) ||
          inst.city?.toLowerCase().includes(q) ||
          inst.state?.toLowerCase().includes(q)
        )
      }
      return true
    })

    filtered.forEach((inst) => {
      // Marker color logic: Red for overlap, Amber for high risk, Blue for standard
      let color = '#2563eb' // Blue
      let fillColor = '#60a5fa'
      if (inst.has_overlap) {
        color = '#b91c1c' // Crimson / Red
        fillColor = '#ef4444'
      } else if (inst.risk_score >= 70) {
        color = '#d97706' // Amber / Orange
        fillColor = '#fbbf24'
      }

      const radius = inst.has_overlap ? 9 : Math.max(5, Math.min(inst.open_cases * 2 + 5, 12))

      const marker = L.circleMarker([inst.lat, inst.lng], {
        radius,
        fillColor,
        color,
        weight: inst.has_overlap ? 3 : 1.5,
        opacity: 0.95,
        fillOpacity: 0.8,
      })

      const popupContent = document.createElement('div')
      popupContent.className = 'p-1 font-sans text-xs max-w-xs'
      popupContent.innerHTML = `
        <div class="font-bold text-slate-900 text-sm mb-1">${inst.name}</div>
        <div class="text-slate-600 mb-1">AICTE ID: <span class="font-mono text-slate-800 font-bold">${inst.aicte_id || 'N/A'}</span></div>
        <div class="text-slate-600 mb-2">${inst.city}, ${inst.state} (${inst.region} Region)</div>
        <div class="flex items-center gap-2 mb-2.5">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
            inst.has_overlap ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-blue-100 text-blue-800'
          }">
            ${inst.has_overlap ? '⚠️ Cross-Bureau Overlap' : `${inst.open_cases} Active Cases`}
          </span>
          <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${
            inst.risk_score >= 70 ? 'bg-amber-100 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-700'
          }">
            Risk: ${inst.risk_score}/100
          </span>
        </div>
        <button id="btn-inspect-${inst.id}" class="w-full text-center bg-blue-900 hover:bg-blue-950 text-white rounded px-2.5 py-1.5 text-xs font-semibold cursor-pointer shadow-xs transition-colors">
          View Institution Profile & Risk &rarr;
        </button>
      `

      marker.bindPopup(popupContent, { minWidth: 240 })

      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-inspect-${inst.id}`)
        if (btn && onSelectInstitution) {
          btn.onclick = () => onSelectInstitution(inst)
        }
      })

      layerGroup.addLayer(marker)
    })
  }, [institutions, activeFilter, searchQuery, onSelectInstitution])

  // Center back to full India view
  const resetView = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([22.0, 78.9629], 5, { animate: true })
      mapInstanceRef.current.invalidateSize()
    }
  }

  const overlapCount = institutions.filter((i) => i.has_overlap).length
  const highRiskCount = institutions.filter((i) => i.risk_score >= 70).length

  return (
    <div className="space-y-2">
      {/* Map Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-bold text-slate-600 flex items-center gap-1 mr-1">
            <Filter className="h-3.5 w-3.5 text-slate-500" /> Filter:
          </span>
          <button
            onClick={() => setActiveFilter('all')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeFilter === 'all'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            All Institutions ({institutions.length})
          </button>
          <button
            onClick={() => setActiveFilter('overlap')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeFilter === 'overlap'
                ? 'bg-red-600 text-white shadow-xs'
                : 'bg-white border border-red-200 text-red-700 hover:bg-red-50'
            }`}
          >
            ⚠️ Overlaps Only ({overlapCount})
          </button>
          <button
            onClick={() => setActiveFilter('high_risk')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeFilter === 'high_risk'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'bg-white border border-amber-200 text-amber-800 hover:bg-amber-50'
            }`}
          >
            High Risk ≥70 ({highRiskCount})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search college on map…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-2.5 py-1 text-xs rounded-lg border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 w-48"
            />
          </div>
          <button
            onClick={resetView}
            title="Reset to Full India View"
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs"
          >
            <RotateCcw className="h-3 w-3 text-slate-500" /> Reset View
          </button>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div
        className="relative w-full rounded-xl overflow-hidden border border-slate-200 shadow-sm"
        style={{ height }}
      >
        <div ref={mapContainerRef} className="h-full w-full z-0" />

        {/* Free Leaflet Attribution & OpenStreetMap Badge */}
        <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-xs px-2.5 py-1 rounded-md border border-slate-200 shadow-xs text-[11px] font-semibold text-slate-700 z-[1000] flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
          Free Leaflet JS + OpenStreetMap
        </div>

        {/* Map Legend */}
        <div className="absolute bottom-3 right-3 bg-white/95 backdrop-blur-xs p-2.5 rounded-lg border border-slate-200 shadow-md text-[11px] space-y-1.5 z-[1000]">
          <div className="font-bold text-slate-800 mb-1 border-b border-slate-100 pb-1">Map Legend</div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500 border border-red-700"></span>
            <span className="text-slate-700 font-medium">Cross-Bureau Overlap</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-amber-400 border border-amber-600"></span>
            <span className="text-slate-700 font-medium">High Risk (Score ≥ 70)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-blue-400 border border-blue-600"></span>
            <span className="text-slate-700 font-medium">Standard Active Cases</span>
          </div>
        </div>
      </div>
    </div>
  )
}
