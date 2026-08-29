import { useState } from 'react'
import { Play, Terminal } from 'lucide-react'
import { api } from '../api/client'

const EXAMPLE_QUERY = `PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?wkt WHERE {
  ?facility geo:hasGeometry/geo:asWKT ?wkt ;
            rdfs:label ?label .
}`

// A restricted (SELECT-only), read-only window onto the same in-process
// rdflib graph geo.py queries server-side — the point being that this graph
// is a real, directly-queryable store, not just an internal implementation
// detail behind the /map endpoint.
export default function SparqlPlayground() {
  const [query, setQuery] = useState(EXAMPLE_QUERY)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)

  async function handleRun() {
    setRunning(true)
    setError('')
    setResult(null)
    try {
      const res = await api.runSparql(query)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <section className="bg-slate-900 text-slate-300 p-5 rounded-2xl border border-slate-700">
      <h3 className="text-[10px] font-bold text-yellow-500 uppercase mb-3 flex items-center gap-2">
        <Terminal className="w-3.5 h-3.5" /> SPARQL Playground
      </h3>
      <p className="text-[11px] leading-relaxed mb-3">
        Query the live facility graph directly — this is the same in-process store
        the map's <code className="text-yellow-400">/api/geo/map</code> endpoint queries.
        SELECT only.
      </p>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={7}
        spellCheck={false}
        className="w-full bg-slate-950 text-emerald-300 text-[11px] font-mono p-3 rounded-lg border border-slate-700 outline-none focus:border-yellow-400 resize-y"
      />
      <button
        onClick={handleRun}
        disabled={running}
        className="mt-3 flex items-center gap-2 px-3 py-1.5 bg-yellow-500 text-slate-900 rounded-lg text-xs font-bold hover:bg-yellow-400 disabled:opacity-50 transition-colors"
      >
        <Play className="w-3.5 h-3.5" />
        {running ? 'Running…' : 'Run query'}
      </button>

      {error && (
        <div className="mt-3 text-[11px] text-red-400 bg-red-950/40 border border-red-900 rounded-lg p-2">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-[11px] border-collapse">
            <thead>
              <tr>
                {result.columns.map(col => (
                  <th key={col} className="text-left text-yellow-500 font-bold uppercase px-2 py-1 border-b border-slate-700">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.length === 0 ? (
                <tr><td className="px-2 py-2 text-slate-500" colSpan={result.columns.length}>No rows</td></tr>
              ) : (
                result.rows.map((row, i) => (
                  <tr key={i} className="border-b border-slate-800">
                    {row.map((cell, j) => (
                      <td key={j} className="px-2 py-1 font-mono text-slate-300">{cell ?? '—'}</td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
