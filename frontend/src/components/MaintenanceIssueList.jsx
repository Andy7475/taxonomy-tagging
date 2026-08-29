import { Database, ClipboardList, Trash2 } from 'lucide-react'

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
  onDelete,
  onIngest,
  ingesting,
  ingestResult,
  onSeedIssues,
  seedingIssues,
  seedIssuesResult,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end gap-3 flex-wrap">
        {ingestResult && (
          <span className="text-emerald-600 text-xs font-medium">
            ✓ {ingestResult.facilities} facilities → {ingestResult.documents} docs
          </span>
        )}
        <button
          onClick={onIngest}
          disabled={ingesting}
          title="Re-parses ontology/*.ttl from disk — safe to click again after editing the TTL"
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          <Database className="w-4 h-4" />
          {ingesting ? 'Ingesting…' : ingestResult ? 'Re-ingest Ontology' : 'Ingest Ontology'}
        </button>
        {seedIssuesResult && (
          <span className="text-blue-600 text-xs font-medium">
            ✓ {seedIssuesResult.created} demo issues
            {seedIssuesResult.skipped.length > 0 && ` (${seedIssuesResult.skipped.length} skipped — ingest ontology first)`}
          </span>
        )}
        <button
          onClick={onSeedIssues}
          disabled={seedingIssues}
          title="Creates a handful of demo maintenance issues — requires the ontology to be ingested first"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <ClipboardList className="w-4 h-4" />
          {seedingIssues ? 'Seeding…' : 'Seed Demo Issues'}
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">Loading…</div>
      ) : issues.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200">
          <p className="text-slate-400 font-medium">No maintenance issues yet.</p>
          <p className="text-slate-400 text-sm mt-2">
            Click <strong>Ingest Ontology</strong>, then <strong>Seed Demo Issues</strong> (or report one yourself).
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
