import { X } from 'lucide-react'

function getLeaf(path) {
  return path.split('/').pop()
}

export default function DocumentCard({ doc, activeFilters = [], onDelete }) {
  return (
    <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 hover:border-yellow-400 hover:shadow-md transition-all group relative">
      {onDelete && (
        <button
          onClick={() => onDelete(doc.id)}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-slate-300 hover:text-red-500"
          title="Delete"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
      <div className="flex flex-col items-center">
        <span className="text-5xl mb-3 transition-transform group-hover:scale-125 duration-300">
          {doc.icon || '📄'}
        </span>
        <h3 className="font-bold text-slate-800 text-[11px] truncate w-full text-center mb-2">
          {doc.name}
        </h3>
        {doc.description && (
          <p className="text-[9px] text-slate-400 text-center mb-1 line-clamp-2">{doc.description}</p>
        )}
        <div className="flex flex-wrap justify-center gap-1">
          {doc.tags.map(tag => {
            const isActive = activeFilters.some(f => tag.startsWith(f) || tag === f)
            return (
              <span
                key={tag}
                className={`text-[8px] px-1.5 py-0.5 rounded-md font-bold uppercase tracking-tighter ${
                  isActive ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-400'
                }`}
                title={tag}
              >
                {getLeaf(tag)}
              </span>
            )
          })}
        </div>
      </div>
    </div>
  )
}
