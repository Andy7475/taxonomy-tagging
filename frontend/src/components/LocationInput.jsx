import { useState, useRef, useEffect, useCallback } from 'react'
import { X, ChevronRight } from 'lucide-react'
import { api } from '../api/client'

const DEBOUNCE_MS = 180

function useDebounce(fn, delay) {
  const timer = useRef(null)
  return useCallback((...args) => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => fn(...args), delay)
  }, [fn, delay])
}

const MATCHED_VIA_COLORS = {
  synonym: 'text-amber-600 bg-amber-50',
  label: 'text-blue-600 bg-blue-50',
  path: 'text-slate-500 bg-slate-50',
  issue: 'text-violet-600 bg-violet-50',
}

const TYPE_COLORS = {
  Site: 'text-emerald-700 bg-emerald-50',
  Building: 'text-blue-700 bg-blue-50',
  Storey: 'text-amber-700 bg-amber-50',
  Zone: 'text-rose-700 bg-rose-50',
}

function ancestorOf(path) {
  return path.split('/').slice(0, -1).join('/')
}

// Single-select, uri-keyed location picker. Unlike TagInput (multi-select
// chips keyed on `path`), a maintenance issue has exactly one location and
// the value that matters is `uri` — `path` is only ever a display/disambiguation
// aid. Suggestion rows are keyed on (uri, path), not uri alone, so a facility
// reachable via more than one hierarchy chain (see the Plant Room example in
// ontology/facility_instances.ttl) renders as multiple distinct rows the user
// can pick between; every row for the same uri writes back the same value.
export default function LocationInput({
  value = null,
  onChange,
  placeholder = 'Type to search locations…',
  chipColor = 'bg-blue-100 text-blue-800 border-blue-200',
}) {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null) // { uri, path, label, facility_type }
  const containerRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (!value) {
      setSelected(null)
      return
    }
    if (selected?.uri === value) return
    api.resolveLocation(value)
      .then(rows => { if (rows?.length) setSelected(rows[0]) })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  const fetchSuggestions = useCallback(async (q) => {
    if (!q.trim()) { setSuggestions([]); return }
    setLoading(true)
    try {
      const results = await api.suggestLocations(q, value ? [value] : [])
      setSuggestions(results)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [value])

  const fetchBrowse = useCallback(async () => {
    setLoading(true)
    try {
      const results = await api.browseLocations(value ? [value] : [])
      setSuggestions(results)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [value])

  const debouncedFetch = useDebounce(fetchSuggestions, DEBOUNCE_MS)

  useEffect(() => {
    debouncedFetch(input)
  }, [input, debouncedFetch])

  useEffect(() => {
    function onClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function handleSelect(s) {
    setSelected(s)
    onChange(s.uri)
    setInput('')
    setSuggestions([])
    setOpen(false)
  }

  function handleClear() {
    setSelected(null)
    onChange(null)
    inputRef.current?.focus()
  }

  return (
    <div className="relative" ref={containerRef}>
      <div
        className="flex flex-wrap gap-1 p-2 border border-slate-200 rounded-lg min-h-[42px] bg-white cursor-text"
        onClick={() => inputRef.current?.focus()}
      >
        {selected && (
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border ${chipColor}`}
          >
            {ancestorOf(selected.path) && (
              <span className="font-mono text-[10px] opacity-60">{ancestorOf(selected.path)}/</span>
            )}
            <span>{selected.label}</span>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleClear() }}
              className="ml-0.5 opacity-60 hover:opacity-100"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        )}
        {!selected && (
          <input
            ref={inputRef}
            type="text"
            className="flex-1 min-w-[120px] outline-none text-sm bg-transparent"
            placeholder={placeholder}
            value={input}
            onChange={(e) => {
              const val = e.target.value
              setInput(val)
              setOpen(true)
              if (!val.trim()) setSuggestions([])
            }}
            onFocus={() => {
              if (input) {
                setOpen(true)
              } else {
                fetchBrowse()
                setOpen(true)
              }
            }}
          />
        )}
        {loading && (
          <span className="text-[10px] text-slate-400 self-center pr-1">…</span>
        )}
      </div>

      {open && !selected && suggestions.length > 0 && (
        <div className="absolute z-50 left-0 top-full mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-64">
          <div className="px-3 py-1.5 bg-slate-50 border-b text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            {input.trim() ? 'Matching Locations' : 'Available Locations'}
          </div>
          <div className="overflow-y-auto">
            {suggestions.map(s => (
              <button
                key={`${s.uri}::${s.path}`}
                type="button"
                onClick={() => handleSelect(s)}
                className="w-full text-left px-3 py-2.5 hover:bg-yellow-50 border-b last:border-0 flex items-center justify-between group"
              >
                <div>
                  <div className="font-semibold text-slate-800 text-sm group-hover:text-yellow-700">
                    {s.label}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] font-mono text-slate-400">
                      {ancestorOf(s.path) || s.path}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${TYPE_COLORS[s.facility_type] || 'text-slate-500 bg-slate-100'}`}>
                      {s.facility_type}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${MATCHED_VIA_COLORS[s.matched_via]}`}>
                      {s.matched_via}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-yellow-500 shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
