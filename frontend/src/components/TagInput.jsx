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
}

export default function TagInput({
  selectedTags = [],
  additionalExclude = [],
  onAdd,
  onRemove,
  placeholder = 'Type to search tags…',
  chipColor = 'bg-blue-100 text-blue-800 border-blue-200',
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
      const results = await api.suggestTags(q, [...selectedTags, ...additionalExclude])
      setSuggestions(results)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [selectedTags, additionalExclude])

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

  function handleSelect(path) {
    onAdd(path)
    setInput('')
    setSuggestions([])
    setOpen(false)
    inputRef.current?.focus()
  }

  function getLeaf(path) {
    return path.split('/').pop()
  }

  return (
    <div className="relative" ref={containerRef}>
      <div
        className="flex flex-wrap gap-1 p-2 border border-slate-200 rounded-lg min-h-[42px] bg-white cursor-text"
        onClick={() => inputRef.current?.focus()}
      >
        {selectedTags.map(tag => (
          <span
            key={tag}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border ${chipColor}`}
          >
            <span className="font-mono text-[10px] opacity-60">{tag.split('/').slice(0, -1).join('/')}/</span>
            <span>{getLeaf(tag)}</span>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onRemove(tag) }}
              className="ml-0.5 opacity-60 hover:opacity-100"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          className="flex-1 min-w-[120px] outline-none text-sm bg-transparent"
          placeholder={selectedTags.length === 0 ? placeholder : ''}
          value={input}
          onChange={(e) => { setInput(e.target.value); setOpen(true) }}
          onFocus={() => { if (input) setOpen(true) }}
        />
        {loading && (
          <span className="text-[10px] text-slate-400 self-center pr-1">…</span>
        )}
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute z-50 left-0 top-full mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden">
          <div className="px-3 py-1.5 bg-slate-50 border-b text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Matching Tags
          </div>
          {suggestions.map(s => (
            <button
              key={s.path}
              type="button"
              onClick={() => handleSelect(s.path)}
              className="w-full text-left px-3 py-2.5 hover:bg-yellow-50 border-b last:border-0 flex items-center justify-between group"
            >
              <div>
                <div className="font-semibold text-slate-800 text-sm group-hover:text-yellow-700">
                  {getLeaf(s.path)}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] font-mono text-slate-400">{s.path}</span>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase ${MATCHED_VIA_COLORS[s.matched_via]}`}>
                    {s.matched_via}
                  </span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-yellow-500 shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
