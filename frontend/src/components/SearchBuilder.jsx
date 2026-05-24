import { Filter, Plus, X } from 'lucide-react'
import TagInput from './TagInput'

function getLeaf(path) {
  return path.split('/').pop()
}

export default function SearchBuilder({ filters, onAddFilter, onRemoveFilter }) {
  return (
    <div className="flex flex-wrap items-start gap-2">
      <div className="flex items-center gap-1.5 pt-1.5">
        <div className="p-1.5 bg-slate-100 rounded-lg">
          <Filter className="w-4 h-4 text-slate-500" />
        </div>
        {filters.length === 0 && (
          <span className="text-sm text-slate-400 italic">No active filters</span>
        )}
      </div>

      {filters.map(f => (
        <button
          key={f}
          onClick={() => onRemoveFilter(f)}
          className="flex items-center gap-1.5 bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded-full text-sm font-bold border border-yellow-200 hover:bg-red-50 hover:text-red-700 hover:border-red-200 transition-colors group"
          title={f}
        >
          <span className="font-mono text-[10px] opacity-60">{f.split('/').slice(0,-1).join('/')}/</span>
          {getLeaf(f)}
          <X className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100" />
        </button>
      ))}

      <div className="flex-1 min-w-[200px]">
        <TagInput
          selectedTags={filters}
          onAdd={onAddFilter}
          onRemove={onRemoveFilter}
          placeholder="＋ Add filter tag…"
          chipColor="bg-yellow-100 text-yellow-800 border-yellow-200"
        />
      </div>
    </div>
  )
}
