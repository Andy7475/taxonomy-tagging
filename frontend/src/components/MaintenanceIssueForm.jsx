import { useState } from 'react'
import LocationInput from './LocationInput'
import { api } from '../api/client'

const PRIORITIES = ['low', 'medium', 'high']

export default function MaintenanceIssueForm({ onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [locationUri, setLocationUri] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim() || !locationUri) return

    setSaving(true)
    setError('')
    try {
      const issue = await api.createMaintenanceIssue({
        title: title.trim(),
        description: description.trim() || null,
        priority,
        location_uri: locationUri,
      })
      onCreated(issue)
      setTitle('')
      setDescription('')
      setPriority('medium')
      setLocationUri(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
          title <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          placeholder="e.g. Flickering light"
          className="w-full p-2 border border-slate-200 rounded-lg text-sm focus:border-yellow-400 focus:outline-none"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">description</label>
        <input
          type="text"
          placeholder="Optional description"
          className="w-full p-2 border border-slate-200 rounded-lg text-sm focus:border-yellow-400 focus:outline-none"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">priority</label>
        <select
          className="w-full p-2 border border-slate-200 rounded-lg text-sm bg-white focus:border-yellow-400 focus:outline-none"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
          location <span className="text-red-400">*</span>
        </label>
        <LocationInput
          value={locationUri}
          onChange={setLocationUri}
          placeholder="Search facility locations…"
          chipColor="bg-blue-100 text-blue-800 border-blue-200"
        />
      </div>

      {error && <p className="text-red-500 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={!title.trim() || !locationUri || saving}
        className="w-full bg-slate-900 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-30 hover:bg-slate-700 transition-colors"
      >
        {saving ? 'Reporting…' : 'Report Issue'}
      </button>
    </form>
  )
}
