import { useState } from 'react'
import { X, Copy, Check } from 'lucide-react'

function getLeaf(path) {
  return path.split('/').pop()
}

export default function DocumentCard({ doc, andFilters = [], orFilters = [], onDelete, onClick }) {
  const [copied, setCopied] = useState(false)

  function handleCopy(e) {
    e.stopPropagation()
    navigator.clipboard.writeText(doc.icon || '').then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div
      className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 hover:border-yellow-400 hover:shadow-md transition-all group relative cursor-pointer"
      onClick={onClick}
    >
      {onDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(doc.id) }}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-slate-300 hover:text-red-500"
          title="Delete"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
      <button
        onClick={handleCopy}
        className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-slate-300 hover:text-slate-600"
        title="Copy emoji"
      >
        {copied
          ? <Check className="w-3 h-3 text-emerald-500" />
          : <Copy className="w-3 h-3" />
        }
      </button>
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
            const isAnd = andFilters.some(f => tag === f || tag.startsWith(f + '/'))
            const isOr = orFilters.some(f => tag === f || tag.startsWith(f + '/'))
            return (
              <span
                key={tag}
                className={`text-[8px] px-1.5 py-0.5 rounded-md font-bold uppercase tracking-tighter ${
                  isAnd ? 'bg-blue-100 text-blue-700' :
                  isOr  ? 'bg-emerald-100 text-emerald-700' :
                  'bg-slate-100 text-slate-400'
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
