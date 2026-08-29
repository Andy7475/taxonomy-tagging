import { useState } from 'react'

const ZONE_COLORS = ['#1d4ed8', '#b45309', '#047857', '#be123c', '#7c3aed']

function polygonPoints(points) {
  return points.map(([x, y]) => `${x},${y}`).join(' ')
}

function centroidOf(points) {
  const n = points.length
  return points.reduce((acc, [x, y]) => [acc[0] + x / n, acc[1] + y / n], [0, 0])
}

// Presentational: page owns the fetch (see LocationsDemo), this just draws
// the SVG floor plan for whatever `data` (FloorplanResponse from
// GET /api/geo/floorplan) it's given. Zone regions come from
// facility_floorplans.ttl — a third independent ABox over the same
// Storey/Zone URIs used everywhere else, alongside facility_instances.ttl
// (containment) and facility_geo.ttl (lat/lon) — see
// backend/app/graph_store.py's floorplan().
export default function FloorPlan({ data }) {
  const [hoveredUri, setHoveredUri] = useState(null)

  if (!data) return null
  const { width, height, zones } = data

  return (
    <div className="rounded-2xl border border-slate-200 shadow-sm bg-white p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 420 }}>
        <rect x={0} y={0} width={width} height={height} fill="#f8fafc" stroke="#cbd5e1" strokeWidth={0.5} />
        {zones.map((zone, i) => {
          const isHovered = hoveredUri === zone.uri
          const color = ZONE_COLORS[i % ZONE_COLORS.length]
          const [cx, cy] = centroidOf(zone.points)
          return (
            <g
              key={zone.uri}
              onMouseEnter={() => setHoveredUri(zone.uri)}
              onMouseLeave={() => setHoveredUri(null)}
              style={{ cursor: 'pointer' }}
            >
              <polygon
                points={polygonPoints(zone.points)}
                fill={color}
                fillOpacity={isHovered ? 0.55 : 0.28}
                stroke={color}
                strokeWidth={isHovered ? 1 : 0.5}
              />
              <text
                x={cx}
                y={cy}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={Math.max(width, height) / 22}
                fill="#1e293b"
                fontWeight={isHovered ? 700 : 500}
                style={{ pointerEvents: 'none' }}
              >
                {zone.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
