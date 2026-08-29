import { Database, Trash2 } from 'lucide-react'
import LocationInput from './LocationInput'

const PRIORITY_COLORS = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-red-100 text-red-700',
}

function ancestorOf(path) {
  return path ? path.split('/').slice(0, -1).join('/') : ''
}

export default function MaintenanceIssueList({
  issues,
  loading,
  underUri,
  onUnderChange,
  onDelete,
  onIngest,
  ingesting,
  ingestDone,
}) {
  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-end justify-between flex-wrap gap-3">
          <div className="flex-1 min-w-[240px]">
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              filter: everything under…
            </label>
            <LocationInput
              value={underUri}
              onChange={onUnderChange}
              placeholder="Filter by a Site, Building, Storey or Zone…"
              chipColor="bg-emerald-100 text-emerald-800 border-emerald-200"
            />
          </div>
          {!ingestDone && (
            <button
              onClick={onIngest}
              disabled={ingesting}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              <Database className="w-4 h-4" />
              {ingesting ? 'Ingesting…' : 'Ingest Ontology'}
            </button>
          )}
          {ingestDone && <span className="text-emerald-600 text-sm font-medium">✓ Ingested</span>}
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">Loading…</div>
      ) : issues.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200">
          <p className="text-slate-400 font-medium">No maintenance issues yet.</p>
          <p className="text-slate-400 text-sm mt-2">
            Click <strong>Ingest Ontology</strong>, then report an issue.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {issues.map(issue => (
            <div
              key={issue.id}
              className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 flex items-start justify-between gap-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-slate-800 text-sm">{issue.title}</h3>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${PRIORITY_COLORS[issue.priority] || PRIORITY_COLORS.medium}`}>
                    {issue.priority}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase bg-slate-100 text-slate-600">
                    {issue.status}
                  </span>
                </div>
                {issue.description && (
                  <p className="text-xs text-slate-500 mt-1">{issue.description}</p>
                )}
                <div className="mt-1.5 space-y-0.5">
                  {(issue.location_path || []).map(path => (
                    <div key={path} className="text-[11px] font-mono">
                      {ancestorOf(path) && (
                        <span className="text-slate-400">{ancestorOf(path)}/</span>
                      )}
                      <span className="text-slate-700 font-bold">{path.split('/').pop()}</span>
                    </div>
                  ))}
                </div>
              </div>
              {onDelete && (
                <button
                  onClick={() => onDelete(issue.id)}
                  className="text-slate-300 hover:text-red-500 transition-colors shrink-0"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
