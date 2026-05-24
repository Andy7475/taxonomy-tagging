import { ArrowLeft, Trash2, Tag, Calendar, FileText, Hash } from 'lucide-react'

function getLeaf(path) {
  return path.split('/').pop()
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function DocumentDetail({ doc, onBack, onDelete }) {
  async function handleDelete() {
    if (!confirm(`Delete "${doc.name}"?`)) return
    await onDelete(doc.id)
    onBack()
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to search
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-500 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
          Delete
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Hero */}
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col items-center py-10 border-b border-slate-200">
          <span className="text-8xl mb-4">{doc.icon || '📄'}</span>
          <h1 className="text-2xl font-bold text-slate-800">{doc.name}</h1>
        </div>

        {/* Fields */}
        <div className="divide-y divide-slate-100">
          <Field icon={<FileText className="w-4 h-4" />} label="name">
            <span className="text-slate-800 font-medium">{doc.name}</span>
          </Field>

          <Field icon={<span className="text-base leading-none">🖼</span>} label="icon">
            <span className="text-2xl">{doc.icon || <span className="text-slate-400 text-sm">—</span>}</span>
          </Field>

          <Field icon={<FileText className="w-4 h-4" />} label="description">
            {doc.description
              ? <p className="text-slate-700 text-sm leading-relaxed">{doc.description}</p>
              : <span className="text-slate-400 text-sm italic">No description</span>
            }
          </Field>

          <Field icon={<Tag className="w-4 h-4" />} label="tags">
            {doc.tags.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {doc.tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium border border-slate-200"
                    title={tag}
                  >
                    <span className="font-mono text-[9px] text-slate-400">{tag.split('/').slice(0, -1).join('/')}/</span>
                    {getLeaf(tag)}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-slate-400 text-sm italic">No tags</span>
            )}
          </Field>

          <Field icon={<Hash className="w-4 h-4" />} label="metadata">
            {doc.metadata && Object.keys(doc.metadata).length > 0 ? (
              <pre className="text-xs font-mono bg-slate-50 border border-slate-200 rounded-lg p-3 text-slate-700 whitespace-pre-wrap break-all">
                {JSON.stringify(doc.metadata, null, 2)}
              </pre>
            ) : (
              <span className="text-slate-400 text-sm italic">No metadata</span>
            )}
          </Field>

          <Field icon={<Calendar className="w-4 h-4" />} label="created_at">
            <span className="text-slate-600 text-sm font-mono">{formatDate(doc.created_at)}</span>
          </Field>
        </div>
      </div>
    </div>
  )
}

function Field({ icon, label, children }) {
  return (
    <div className="px-6 py-4 flex gap-4">
      <div className="flex items-start gap-2 w-32 shrink-0 pt-0.5">
        <span className="text-slate-400">{icon}</span>
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
      </div>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}
