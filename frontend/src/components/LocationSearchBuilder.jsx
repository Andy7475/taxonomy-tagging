import { useState, useRef } from 'react'
import { X, GripVertical } from 'lucide-react'
import LocationFilterInput from './LocationFilterInput'

const LANES = [
  {
    id: 'and',
    label: 'AND',
    desc: 'Must match all',
    chipCls: 'bg-blue-100 text-blue-800 border-blue-200',
    headerCls: 'bg-blue-50 border-blue-200',
    labelCls: 'text-blue-700',
    dropCls: 'border-blue-400 bg-blue-50/40',
  },
  {
    id: 'or',
    label: 'OR',
    desc: 'Match any one',
    chipCls: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    headerCls: 'bg-emerald-50 border-emerald-200',
    labelCls: 'text-emerald-700',
    dropCls: 'border-emerald-400 bg-emerald-50/40',
  },
  {
    id: 'not',
    label: 'NOT',
    desc: 'Exclude these',
    chipCls: 'bg-red-100 text-red-800 border-red-200',
    headerCls: 'bg-red-50 border-red-200',
    labelCls: 'text-red-700',
    dropCls: 'border-red-400 bg-red-50/40',
  },
]

function ancestorOf(path) {
  return path.split('/').slice(0, -1).join('/')
}

// AND/OR/NOT lanes over locations, mirroring SearchBuilder.jsx's exact
// drag-and-drop UX but keyed on `uri` (with label/path carried alongside
// for display, since — unlike a taxonomy path — a location's identifier
// alone isn't human-readable).
export default function LocationSearchBuilder({ andLocations, orLocations, notLocations, onAdd, onRemove, onMove }) {
  const [dragOver, setDragOver] = useState(null)
  const dragRef = useRef(null)

  const locationsByLane = { and: andLocations, or: orLocations, not: notLocations }
  const allUris = [...andLocations, ...orLocations, ...notLocations].map(l => l.uri)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {LANES.map(lane => {
        const locations = locationsByLane[lane.id]
        const isOver = dragOver === lane.id

        return (
          <div
            key={lane.id}
            className={`rounded-xl border-2 transition-all duration-150 relative z-10 focus-within:z-20 ${
              isOver ? `border-dashed ${lane.dropCls}` : 'border-slate-200'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(lane.id) }}
            onDragLeave={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) setDragOver(null)
            }}
            onDrop={(e) => {
              e.preventDefault()
              setDragOver(null)
              const drag = dragRef.current
              if (drag && drag.fromLane !== lane.id) {
                onMove(drag.item, drag.fromLane, lane.id)
              }
              dragRef.current = null
            }}
          >
            <div className={`px-3 py-2 border-b rounded-t-[10px] ${lane.headerCls} flex items-center justify-between`}>
              <div className="flex items-baseline gap-2">
                <span className={`text-xs font-extrabold uppercase tracking-widest ${lane.labelCls}`}>
                  {lane.label}
                </span>
                <span className="text-[10px] text-slate-400">{lane.desc}</span>
              </div>
              {locations.length > 0 && (
                <span className={`text-[10px] font-bold ${lane.labelCls} opacity-60`}>
                  {locations.length}
                </span>
              )}
            </div>

            <div className="p-2 space-y-2 bg-white">
              {locations.length > 0 && (
                <div className="flex flex-wrap gap-1 min-h-[24px]">
                  {locations.map(loc => (
                    <span
                      key={loc.uri}
                      draggable
                      onDragStart={(e) => {
                        dragRef.current = { item: loc, fromLane: lane.id }
                        e.dataTransfer.effectAllowed = 'move'
                      }}
                      onDragEnd={() => { dragRef.current = null }}
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border cursor-grab active:cursor-grabbing select-none ${lane.chipCls}`}
                    >
                      <GripVertical className="w-2.5 h-2.5 opacity-30" />
                      {ancestorOf(loc.path) && (
                        <span className="font-mono text-[9px] opacity-50">
                          {ancestorOf(loc.path)}/
                        </span>
                      )}
                      {loc.label}
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); onRemove(loc.uri, lane.id) }}
                        className="ml-0.5 opacity-50 hover:opacity-100"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <LocationFilterInput
                excludeUris={allUris}
                onAdd={(item) => onAdd(item, lane.id)}
                placeholder={`＋ Add ${lane.label} location…`}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
