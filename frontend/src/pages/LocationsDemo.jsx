import { useState, useEffect, useCallback } from 'react'
import { MapPin } from 'lucide-react'
import { api } from '../api/client'
import MaintenanceIssueForm from '../components/MaintenanceIssueForm'
import MaintenanceIssueList from '../components/MaintenanceIssueList'

export default function LocationsDemo() {
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [underUri, setUnderUri] = useState(null)
  const [ingesting, setIngesting] = useState(false)
  const [ingestDone, setIngestDone] = useState(false)

  const fetchIssues = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api.listMaintenanceIssues({ under: underUri || '' })
      setIssues(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [underUri])

  useEffect(() => { fetchIssues() }, [fetchIssues])

  async function handleIngest() {
    setIngesting(true)
    try {
      await api.ingestLocations()
      setIngestDone(true)
      setTimeout(fetchIssues, 300)
    } catch (err) {
      alert('Ingest failed: ' + err.message)
    } finally {
      setIngesting(false)
    }
  }

  async function handleDelete(id) {
    try {
      await api.deleteMaintenanceIssue(id)
      fetchIssues()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      <div className="space-y-6 lg:col-span-1">
        <section className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-xs font-bold mb-4 flex items-center gap-2 uppercase tracking-wider text-slate-400">
            <MapPin className="w-3.5 h-3.5" /> Report Issue
          </h2>
          <MaintenanceIssueForm onCreated={fetchIssues} />
        </section>

        <section className="bg-slate-900 text-slate-300 p-5 rounded-2xl border border-slate-700">
          <h3 className="text-[10px] font-bold text-yellow-500 uppercase mb-3">How it works</h3>
          <div className="text-[11px] space-y-3 leading-relaxed">
            <p>
              <strong className="text-white">Ontology-driven:</strong> locations come from an RDF graph
              (<code className="text-yellow-400">ontology/facility.ttl</code> + <code className="text-yellow-400">facility_instances.ttl</code>),
              flattened into Elasticsearch at ingest time — not hand-authored path strings.
            </p>
            <p>
              <strong className="text-white">Disambiguation:</strong> two different "Zone A"s? Both show up
              with distinct ancestor paths so you pick the right one.
            </p>
            <p>
              <strong className="text-white">Multiple frames of reference:</strong> a facility with two
              isPartOf parents (e.g. an owner's vs. a contractor's site codes) shows up as two rows — pick
              whichever you recognize, both write back the same URI.
            </p>
            <p>
              <strong className="text-white">Containment queries:</strong> the filter above uses a
              <code className="text-yellow-400"> prefix</code> query on a denormalized path — no SPARQL
              needed for "everything under Site Orange."
            </p>
          </div>
        </section>
      </div>

      <div className="lg:col-span-3">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm mb-4">{error}</div>
        )}
        <MaintenanceIssueList
          issues={issues}
          loading={loading}
          underUri={underUri}
          onUnderChange={setUnderUri}
          onDelete={handleDelete}
          onIngest={handleIngest}
          ingesting={ingesting}
          ingestDone={ingestDone}
        />
      </div>
    </div>
  )
}
