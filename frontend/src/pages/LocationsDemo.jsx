import { useState, useEffect, useCallback } from 'react'
import { MapPin, List, Map as MapIcon, LayoutGrid } from 'lucide-react'
import { api } from '../api/client'
import MaintenanceIssueForm from '../components/MaintenanceIssueForm'
import MaintenanceIssueList from '../components/MaintenanceIssueList'
import LocationSearchBuilder from '../components/LocationSearchBuilder'
import FacilityMap from '../components/FacilityMap'
import FloorPlan from '../components/FloorPlan'
import SparqlPlayground from '../components/SparqlPlayground'

// Storeys that carry a mock floor plan in ontology/facility_floorplans.ttl.
// Hardcoded here rather than discovered via SPARQL purely to keep this demo
// page small — a fuller build would list `?storey fp:hasFloorplan ?x` the
// same way geo_features() already queries facility_geo.ttl.
const FLOORPLAN_STOREYS = [
  { uri: 'https://example.org/facility/SiteOrange/MainBuilding/Storey1', label: 'Main Building — Storey 1' },
  { uri: 'https://example.org/facility/SiteOrange/MainBuilding/Storey2', label: 'Main Building — Storey 2' },
  { uri: 'https://example.org/facility/SiteBlue/Annex/GroundFloor', label: 'Annex — Ground Floor' },
]

export default function LocationsDemo() {
  const [issues, setIssues] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [andLocations, setAndLocations] = useState([])
  const [orLocations, setOrLocations] = useState([])
  const [notLocations, setNotLocations] = useState([])
  const [ingesting, setIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState(null) // { facilities, documents } from the last run
  const [seedingIssues, setSeedingIssues] = useState(false)
  const [seedIssuesResult, setSeedIssuesResult] = useState(null) // { created, skipped } from the last run
  const [view, setView] = useState('list') // 'list' | 'map' | 'floorplan'
  const [mapLocations, setMapLocations] = useState([])
  const [mapLoading, setMapLoading] = useState(false)
  const [mapError, setMapError] = useState('')
  const [selectedStorey, setSelectedStorey] = useState(FLOORPLAN_STOREYS[0].uri)
  const [floorplanData, setFloorplanData] = useState(null)
  const [floorplanLoading, setFloorplanLoading] = useState(false)
  const [floorplanError, setFloorplanError] = useState('')

  const fetchIssues = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api.listMaintenanceIssues({
        andUris: andLocations.map(l => l.uri),
        orUris: orLocations.map(l => l.uri),
        notUris: notLocations.map(l => l.uri),
      })
      setIssues(result.issues)
      setTotal(result.total)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [andLocations, orLocations, notLocations])

  useEffect(() => { fetchIssues() }, [fetchIssues])

  // Same AND/OR/NOT filter state drives both the issue list (via
  // Elasticsearch's location_path prefix match) and the map (via a live
  // SPARQL query joined with Elasticsearch's facility_locations by uri) —
  // only fetched when the map view is actually visible.
  useEffect(() => {
    if (view !== 'map') return
    let cancelled = false
    setMapLoading(true)
    setMapError('')
    api.getGeoMap({
      andUris: andLocations.map(l => l.uri),
      orUris: orLocations.map(l => l.uri),
      notUris: notLocations.map(l => l.uri),
    })
      .then(result => { if (!cancelled) setMapLocations(result) })
      .catch(err => { if (!cancelled) setMapError(err.message) })
      .finally(() => { if (!cancelled) setMapLoading(false) })
    return () => { cancelled = true }
  }, [view, andLocations, orLocations, notLocations])

  // Fetches on Floor Plan tab open / storey change — mirrors the map effect
  // above, hitting GET /api/geo/floorplan (facility_floorplans.ttl) instead
  // of GET /api/geo/map (facility_geo.ttl).
  useEffect(() => {
    if (view !== 'floorplan') return
    let cancelled = false
    setFloorplanLoading(true)
    setFloorplanError('')
    api.getFloorplan(selectedStorey)
      .then(result => { if (!cancelled) setFloorplanData(result) })
      .catch(err => { if (!cancelled) setFloorplanError(err.message) })
      .finally(() => { if (!cancelled) setFloorplanLoading(false) })
    return () => { cancelled = true }
  }, [view, selectedStorey])

  async function handleIngest() {
    setIngesting(true)
    try {
      // Re-runnable any time — re-parses the current ontology/*.ttl files
      // from disk, so editing the TTL and clicking this again is how you
      // push a location change live. Also reloads the in-process SPARQL
      // graph (facility_geo.ttl included) so both stores stay in sync.
      const [result] = await Promise.all([api.ingestLocations(), api.reloadGeoGraph()])
      setIngestResult(result)
      setTimeout(fetchIssues, 300)
    } catch (err) {
      alert('Ingest failed: ' + err.message)
    } finally {
      setIngesting(false)
    }
  }

  async function handleSeedIssues() {
    setSeedingIssues(true)
    try {
      const result = await api.seedMaintenanceIssues()
      setSeedIssuesResult(result)
      fetchIssues()
    } catch (err) {
      alert('Seeding demo issues failed: ' + err.message)
    } finally {
      setSeedingIssues(false)
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

  function handleAddLocation(item, lane) {
    const setter = lane === 'and' ? setAndLocations : lane === 'or' ? setOrLocations : setNotLocations
    setter(prev => prev.some(l => l.uri === item.uri) ? prev : [...prev, item])
  }

  function handleRemoveLocation(uri, lane) {
    const setter = lane === 'and' ? setAndLocations : lane === 'or' ? setOrLocations : setNotLocations
    setter(prev => prev.filter(l => l.uri !== uri))
  }

  function handleMoveLocation(item, fromLane, toLane) {
    handleRemoveLocation(item.uri, fromLane)
    handleAddLocation(item, toLane)
  }

  const hasFilters = andLocations.length > 0 || orLocations.length > 0 || notLocations.length > 0

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
              <strong className="text-white">Multiple frames of reference:</strong> a facility named
              independently by two organizations (e.g. an owner's vs. a contractor's site codes) and
              reconciled via <code className="text-yellow-400">owl:sameAs</code> shows up as two rows —
              pick whichever you recognize, both write back the same URI.
            </p>
            <p>
              <strong className="text-white">AND / OR / NOT:</strong> compose location filters exactly like
              the emoji demo's tag filters — each resolves to a
              <code className="text-yellow-400"> prefix</code> query on a denormalized path, so no SPARQL
              is needed even for "under Site Orange AND under Contractor Site 7."
            </p>
            <p>
              <strong className="text-white">Geo, live:</strong> facility coordinates live in a separate
              <code className="text-yellow-400"> facility_geo.ttl</code> ABox, queried directly via SPARQL
              from an in-process graph — not flattened into Elasticsearch. The Map view joins that SPARQL
              result with Elasticsearch's location data by the shared facility URI, so adding a new kind of
              fact never means touching an index mapping. A Site's geometry is a polygon footprint, a
              Building's is a point — same <code className="text-yellow-400">geo:asWKT</code> predicate,
              different shape, no schema to update either way.
            </p>
          </div>
        </section>

        <SparqlPlayground />
      </div>

      <div className="lg:col-span-3 space-y-5">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <LocationSearchBuilder
            andLocations={andLocations}
            orLocations={orLocations}
            notLocations={notLocations}
            onAdd={handleAddLocation}
            onRemove={handleRemoveLocation}
            onMove={handleMoveLocation}
          />
        </div>

        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-3">
            <p className="text-sm text-slate-500">
              {loading ? 'Searching…' : `${total} incident${total !== 1 ? 's' : ''}${hasFilters ? ' matching filters' : ' total'}`}
            </p>
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
              <button
                onClick={() => setView('list')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${view === 'list' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'}`}
              >
                <List className="w-3.5 h-3.5" /> List
              </button>
              <button
                onClick={() => setView('map')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${view === 'map' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'}`}
              >
                <MapIcon className="w-3.5 h-3.5" /> Map
              </button>
              <button
                onClick={() => setView('floorplan')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${view === 'floorplan' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500'}`}
              >
                <LayoutGrid className="w-3.5 h-3.5" /> Floor Plan
              </button>
            </div>
          </div>
          {hasFilters && (
            <button
              onClick={() => { setAndLocations([]); setOrLocations([]); setNotLocations([]) }}
              className="text-sm text-blue-500 hover:underline font-medium"
            >
              Clear all
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{error}</div>
        )}

        {view === 'map' ? (
          <>
            {mapError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{mapError}</div>
            )}
            {mapLoading ? (
              <div className="py-12 text-center text-slate-400 text-sm">Loading map…</div>
            ) : mapLocations.length === 0 ? (
              <div className="py-16 text-center bg-white rounded-3xl border-2 border-dashed border-slate-200">
                <p className="text-slate-400 font-medium">No locations match this filter.</p>
                <p className="text-slate-400 text-sm mt-2">
                  A Storey/Zone filter shows its enclosing Site/Building on the map — try clearing filters.
                </p>
              </div>
            ) : (
              <FacilityMap locations={mapLocations} />
            )}
          </>
        ) : view === 'floorplan' ? (
          <>
            <div className="flex items-center gap-2 px-1">
              <label className="text-xs font-medium text-slate-500">Storey:</label>
              <select
                value={selectedStorey}
                onChange={e => setSelectedStorey(e.target.value)}
                className="text-sm border border-slate-200 rounded-lg px-2 py-1 bg-white"
              >
                {FLOORPLAN_STOREYS.map(s => (
                  <option key={s.uri} value={s.uri}>{s.label}</option>
                ))}
              </select>
            </div>
            {floorplanError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{floorplanError}</div>
            )}
            {floorplanLoading ? (
              <div className="py-12 text-center text-slate-400 text-sm">Loading floor plan…</div>
            ) : (
              <FloorPlan data={floorplanData} />
            )}
          </>
        ) : (
          <MaintenanceIssueList
            issues={issues}
            loading={loading}
            onDelete={handleDelete}
            onIngest={handleIngest}
            ingesting={ingesting}
            ingestResult={ingestResult}
            onSeedIssues={handleSeedIssues}
            seedingIssues={seedingIssues}
            seedIssuesResult={seedIssuesResult}
          />
        )}
      </div>
    </div>
  )
}
