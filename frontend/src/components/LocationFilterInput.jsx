import { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronRight } from 'lucide-react'
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

// Multi-add location autocomplete for use inside AND/OR/NOT filter lanes
// (see LocationSearchBuilder). Unlike LocationInput (single-select, keeps
// one persistent chip), this always resets to empty after a pick — each
// selection is immediately handed to the parent via onAdd({uri,label,path}),
// mirroring TagInput's "always-empty, parent owns the chip list" shape.
export default function LocationFilterInput({
  excludeUris = [],
  onAdd,
  placeholder = 'Type to search locations…',
}) {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const containerRef = useRef(null)
  const inputRef = useRef(null)

  const fetchSuggestions = useCallback(async (q) => {
    if (!q.trim()) { setSuggestions([]); return }
    setLoading(true)
    try {
      const results = await api.suggestLocations(q, excludeUris)
      setSuggestions(results)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [excludeUris])

  const fetchBrowse = useCallback(async () => {
    setLoading(true)
    try {
      const results = await api.browseLocations(excludeUris)
      setSuggestions(results)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [excludeUris])

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
    onAdd({ uri: s.uri, label: s.label, path: s.path })
    setInput('')
    setSuggestions([])
    setOpen(false)
    inputRef.current?.focus()
  }

  return (
    <div className="relative" ref={containerRef}>
      <input
        ref={inputRef}
        type="text"
        className="w-full p-1.5 border border-slate-200 rounded-md text-xs outline-none bg-white focus:border-yellow-400"
        placeholder={placeholder}
        value={input}
        onChange={(e) => {
          const val = e.target.value
          setInput(val)
          setOpen(true)
          if (!val.trim()) setSuggestions([])
        }}
        onFocus={() => {
          if (input) { setOpen(true) } else { fetchBrowse(); setOpen(true) }
        }}
      />
      {loading && (
        <span className="absolute right-2 top-1.5 text-[10px] text-slate-400">…</span>
      )}

      {open && suggestions.length > 0 && (
        <div className="absolute z-50 left-0 top-full mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-64">
          <div className="overflow-y-auto">
            {suggestions.map(s => (
              <button
                key={`${s.uri}::${s.path}`}
                type="button"
                onClick={() => handleSelect(s)}
                className="w-full text-left px-3 py-2 hover:bg-yellow-50 border-b last:border-0 flex items-center justify-between group"
              >
                <div>
                  <div className="font-semibold text-slate-800 text-xs group-hover:text-yellow-700">
                    {s.label}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[9px] font-mono text-slate-400">
                      {ancestorOf(s.path) || s.path}
                    </span>
                    <span className={`text-[8px] px-1 py-0.5 rounded-full font-bold uppercase ${TYPE_COLORS[s.facility_type] || 'text-slate-500 bg-slate-100'}`}>
                      {s.facility_type}
                    </span>
                    <span className={`text-[8px] px-1 py-0.5 rounded-full font-bold uppercase ${MATCHED_VIA_COLORS[s.matched_via]}`}>
                      {s.matched_via}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-yellow-500 shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
