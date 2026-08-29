import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Same facility_type palette LocationFilterInput uses for its badges, just
// expressed as hex dots instead of tailwind classes (Leaflet divIcons render
// outside the app's normal DOM/CSS tree).
const TYPE_DOT_COLORS = {
  Site: '#047857',
  Building: '#1d4ed8',
  Storey: '#b45309',
  Zone: '#be123c',
}

function dotIcon(facilityType) {
  const color = TYPE_DOT_COLORS[facilityType] || '#475569'
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 0 1px ${color}"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -7],
  })
}

function ancestorOf(path) {
  return path.split('/').slice(0, -1).join('/')
}

function PopupBody({ loc }) {
  return (
    <div className="text-xs">
      <div className="font-bold text-slate-800">{loc.label}</div>
      <div className="font-mono text-[10px] text-slate-500 mt-0.5">
        {ancestorOf(loc.path) && `${ancestorOf(loc.path)}/`}
        <span className="text-slate-700">{loc.path.split('/').pop()}</span>
      </div>
      <div className="text-[10px] text-slate-400 mt-0.5 uppercase font-bold">{loc.facility_type}</div>
    </div>
  )
}

// Presentational: page owns the fetch (see LocationsDemo), this just renders
// each `locations` entry (MapLocation[] from GET /api/geo/map) according to
// its geometry_type — a Site's facility_geo.ttl geometry is a Polygon (its
// footprint), a Building's is a Point (a dot) — both sourced from the same
// live SPARQL query, joined with Elasticsearch's label/path/facility_type by
// the shared facility uri. See backend/app/routers/geo.py / graph_store.py.
export default function FacilityMap({ locations }) {
  const firstPoint = locations.find(loc => loc.geometry_type === 'Point')
  const firstPolygon = locations.find(loc => loc.geometry_type === 'Polygon')
  const center = firstPoint
    ? [firstPoint.lat, firstPoint.lon]
    : firstPolygon
    ? firstPolygon.polygon[0]
    : [51.505, -0.09]

  return (
    <div className="rounded-2xl overflow-hidden border border-slate-200 shadow-sm" style={{ height: 420 }}>
      <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {locations.map(loc => loc.geometry_type === 'Polygon' ? (
          <Polygon
            key={loc.uri}
            positions={loc.polygon}
            pathOptions={{ color: TYPE_DOT_COLORS[loc.facility_type] || '#475569', weight: 2, fillOpacity: 0.12 }}
          >
            <Popup><PopupBody loc={loc} /></Popup>
          </Polygon>
        ) : (
          <Marker key={loc.uri} position={[loc.lat, loc.lon]} icon={dotIcon(loc.facility_type)}>
            <Popup><PopupBody loc={loc} /></Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
