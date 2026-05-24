import { useState, useRef } from 'react'
import { X, GripVertical } from 'lucide-react'
import TagInput from './TagInput'

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

function getLeaf(path) {
  return path.split('/').pop()
}

export default function SearchBuilder({ andFilters, orFilters, notFilters, onAdd, onRemove, onMove }) {
  const [dragOver, setDragOver] = useState(null)
  const dragRef = useRef(null)

  const tagsByLane = { and: andFilters, or: orFilters, not: notFilters }
  const allTags = [...andFilters, ...orFilters, ...notFilters]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {LANES.map(lane => {
        const tags = tagsByLane[lane.id]
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
                onMove(drag.tag, drag.fromLane, lane.id)
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
              {tags.length > 0 && (
                <span className={`text-[10px] font-bold ${lane.labelCls} opacity-60`}>
                  {tags.length}
                </span>
              )}
            </div>

            <div className="p-2 space-y-2 bg-white">
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-1 min-h-[24px]">
                  {tags.map(tag => (
                    <span
                      key={tag}
                      draggable
                      onDragStart={(e) => {
                        dragRef.current = { tag, fromLane: lane.id }
                        e.dataTransfer.effectAllowed = 'move'
                      }}
                      onDragEnd={() => { dragRef.current = null }}
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border cursor-grab active:cursor-grabbing select-none ${lane.chipCls}`}
                    >
                      <GripVertical className="w-2.5 h-2.5 opacity-30" />
                      <span className="font-mono text-[9px] opacity-50">
                        {tag.split('/').slice(0, -1).join('/')}/
                      </span>
                      {getLeaf(tag)}
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); onRemove(tag, lane.id) }}
                        className="ml-0.5 opacity-50 hover:opacity-100"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <TagInput
                selectedTags={[]}
                additionalExclude={allTags}
                onAdd={(tag) => onAdd(tag, lane.id)}
                onRemove={() => {}}
                placeholder={`＋ Add ${lane.label} tag…`}
                chipColor={lane.chipCls}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
