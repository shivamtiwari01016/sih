import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

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
}

export default function CopMap({ institutions, onSelectInstitution }: CopMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const layerGroupRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      // Center of India: ~21.5, 78.5, zoom: 5
      const map = L.map(mapContainerRef.current, {
        center: [21.5, 78.5],
        zoom: 5,
        minZoom: 4,
        maxZoom: 12,
      })

      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> | AICTE Samanvay',
        maxZoom: 19,
      }).addTo(map)

      layerGroupRef.current = L.layerGroup().addTo(map)
      mapInstanceRef.current = map
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    const layerGroup = layerGroupRef.current
    if (!map || !layerGroup) return

    layerGroup.clearLayers()

    institutions.forEach((inst) => {
      if (!inst.lat || !inst.lng) return

      // Marker color depends on risk and overlap
      let color = '#2563eb' // Blue
      let fillColor = '#60a5fa'
      if (inst.has_overlap) {
        color = '#b91c1c' // Crimson / Red
        fillColor = '#f87171'
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
        opacity: 0.9,
        fillOpacity: 0.75,
      })

      const popupContent = document.createElement('div')
      popupContent.className = 'p-1 font-sans text-xs'
      popupContent.innerHTML = `
        <div class="font-bold text-slate-900 text-sm mb-1">${inst.name}</div>
        <div class="text-slate-600 mb-1">AICTE ID: <span class="font-mono text-slate-800">${inst.aicte_id}</span></div>
        <div class="text-slate-600 mb-2">${inst.city}, ${inst.state} (${inst.region} Region)</div>
        <div class="flex items-center gap-2 mb-2">
          <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${
            inst.has_overlap ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
          }">
            ${inst.has_overlap ? '⚠️ Cross-Bureau Overlap' : `${inst.open_cases} Active Cases`}
          </span>
          <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${
            inst.risk_score >= 70 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'
          }">
            Risk: ${inst.risk_score}/100
          </span>
        </div>
        <button id="btn-inspect-${inst.id}" class="w-full text-center bg-navy hover:bg-slate-800 text-white rounded px-2 py-1 text-xs font-medium cursor-pointer transition-colors">
          View Institution Profile & Risk
        </button>
      `

      marker.bindPopup(popupContent)

      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-inspect-${inst.id}`)
        if (btn && onSelectInstitution) {
          btn.onclick = () => onSelectInstitution(inst)
        }
      })

      layerGroup.addLayer(marker)
    })
  }, [institutions, onSelectInstitution])

  return (
    <div className="relative h-[480px] w-full rounded-xl overflow-hidden border border-slate-200 shadow-sm">
      <div ref={mapContainerRef} className="h-full w-full z-0" />
      <div className="absolute bottom-3 right-3 bg-white/95 backdrop-blur-sm p-2.5 rounded-lg border border-slate-200 shadow-md text-[11px] space-y-1.5 z-[1000]">
        <div className="font-semibold text-slate-800 mb-1">Map Legend</div>
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
  )
}
