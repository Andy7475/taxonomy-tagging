import { useState, useEffect, useCallback } from 'react'
import { Search, BookOpen, Smile, Loader, Database } from 'lucide-react'
import { api } from './api/client'
import DocumentForm from './components/DocumentForm'
import DocumentCard from './components/DocumentCard'
import DocumentDetail from './components/DocumentDetail'
import SearchBuilder from './components/SearchBuilder'

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export default function App() {
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [andFilters, setAndFilters] = useState([])
  const [orFilters, setOrFilters] = useState([])
  const [notFilters, setNotFilters] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [seeding, setSeeding] = useState(false)
  const [seedDone, setSeedDone] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)

  const debouncedAnd = useDebounce(andFilters, 150)
  const debouncedOr = useDebounce(orFilters, 150)
  const debouncedNot = useDebounce(notFilters, 150)
  const debouncedQuery = useDebounce(searchQuery, 250)

  const fetchDocs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api.search({
        andFilters: debouncedAnd,
        orFilters: debouncedOr,
        notFilters: debouncedNot,
        q: debouncedQuery,
      })
      setDocuments(result.documents)
      setTotal(result.total)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [debouncedAnd, debouncedOr, debouncedNot, debouncedQuery])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  function handleDocCreated() { fetchDocs() }

  async function handleDelete(id) {
    try {
      await api.deleteDocument(id)
      fetchDocs()
    } catch (err) {
      alert(err.message)
    }
  }

  if (selectedDoc) {
    return (
      <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-900">
        <div className="max-w-7xl mx-auto">
          <DocumentDetail
            doc={selectedDoc}
            onBack={() => setSelectedDoc(null)}
            onDelete={async (id) => { await api.deleteDocument(id); fetchDocs() }}
          />
        </div>
      </div>
    )
  }

  async function handleSeed() {
    setSeeding(true)
    try {
      const res = await fetch('/api/seed', { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      setSeedDone(true)
      setTimeout(fetchDocs, 500)
    } catch (err) {
      alert('Seed failed: ' + err.message)
    } finally {
      setSeeding(false)
    }
  }

  function handleAddTag(tag, lane) {
    const setter = lane === 'and' ? setAndFilters : lane === 'or' ? setOrFilters : setNotFilters
    setter(prev => prev.includes(tag) ? prev : [...prev, tag])
  }

  function handleRemoveTag(tag, lane) {
    const setter = lane === 'and' ? setAndFilters : lane === 'or' ? setOrFilters : setNotFilters
    setter(prev => prev.filter(t => t !== tag))
  }

  function handleMoveTag(tag, fromLane, toLane) {
    handleRemoveTag(tag, fromLane)
    handleAddTag(tag, toLane)
  }

  const hasFilters = andFilters.length > 0 || orFilters.length > 0 || notFilters.length > 0 || searchQuery

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-900">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex justify-between items-end flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
              <Smile className="text-yellow-500 w-8 h-8" />
              Taxonomy Tagging
            </h1>
            <p className="text-slate-500 mt-1 text-sm">
              Elasticsearch-powered hierarchical tagging · path_hierarchy tokenizer · synonym resolution
            </p>
          </div>
          <div className="flex items-center gap-3">
            {!seedDone && (
              <button
                onClick={handleSeed}
                disabled={seeding}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                <Database className="w-4 h-4" />
                {seeding ? 'Seeding…' : 'Seed Demo Data'}
              </button>
            )}
            {seedDone && <span className="text-emerald-600 text-sm font-medium">✓ Seeded</span>}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* LEFT: Add Document */}
          <div className="space-y-6 lg:col-span-1">
            <section className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
              <h2 className="text-xs font-bold mb-4 flex items-center gap-2 uppercase tracking-wider text-slate-400">
                Index Item
              </h2>
              <DocumentForm onCreated={handleDocCreated} />
            </section>

            <section className="bg-slate-900 text-slate-300 p-5 rounded-2xl border border-slate-700">
              <h3 className="text-[10px] font-bold text-yellow-500 uppercase mb-3 flex items-center gap-2">
                <BookOpen className="w-3 h-3" /> How it works
              </h3>
              <div className="text-[11px] space-y-3 leading-relaxed">
                <p><strong className="text-white">Hierarchy:</strong> Tags like <code className="text-yellow-400">type/face/emotion/positive</code> use path_hierarchy analysis, so filtering on <code className="text-yellow-400">type/face</code> matches everything underneath.</p>
                <p><strong className="text-blue-400">AND lane:</strong> Results must match every tag — most restrictive.</p>
                <p><strong className="text-emerald-400">OR lane:</strong> Results must match at least one tag — most permissive.</p>
                <p><strong className="text-red-400">NOT lane:</strong> Results must not match any of these tags.</p>
                <p><strong className="text-white">Drag tags</strong> between lanes to change their logic. Free text searches name, description, and tags.</p>
                <p><strong className="text-white">Synonyms:</strong> Type <code className="text-white">smile</code> or <code className="text-white">happy</code> to find <code className="text-yellow-400">positive</code> emotion tags.</p>
              </div>
            </section>
          </div>

          {/* RIGHT: Search + Results */}
          <div className="lg:col-span-3 space-y-5">
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <SearchBuilder
                andFilters={andFilters}
                orFilters={orFilters}
                notFilters={notFilters}
                onAdd={handleAddTag}
                onRemove={handleRemoveTag}
                onMove={handleMoveTag}
              />
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5 group-focus-within:text-yellow-500 transition-colors" />
                <input
                  type="text"
                  placeholder="Free text search — name, description, tags…"
                  className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-yellow-400 focus:outline-none transition-all text-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between px-1">
              <p className="text-sm text-slate-500">
                {loading ? 'Searching…' : `${total} result${total !== 1 ? 's' : ''}`}
              </p>
              {hasFilters && (
                <button
                  onClick={() => { setAndFilters([]); setOrFilters([]); setNotFilters([]); setSearchQuery('') }}
                  className="text-sm text-blue-500 hover:underline font-medium"
                >
                  Clear all
                </button>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{error}</div>
            )}

            {loading ? (
              <div className="flex justify-center py-20">
                <Loader className="w-8 h-8 text-slate-300 animate-spin" />
              </div>
            ) : documents.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200">
                <p className="text-slate-400 font-medium text-lg">No matches.</p>
                {total === 0 && (
                  <p className="text-slate-400 text-sm mt-2">
                    Click <strong>Seed Demo Data</strong> to load 50 emoji examples.
                  </p>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {documents.map(doc => (
                  <DocumentCard
                    key={doc.id}
                    doc={doc}
                    andFilters={andFilters}
                    orFilters={orFilters}
                    onDelete={handleDelete}
                    onClick={() => setSelectedDoc(doc)}
                    onTagClick={(tag) => handleAddTag(tag, 'or')}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
