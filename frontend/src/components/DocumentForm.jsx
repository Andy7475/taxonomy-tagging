import { useState } from 'react'
import TagInput from './TagInput'
import { api } from '../api/client'

export default function DocumentForm({ onCreated }) {
  const [name, setName] = useState('')
  const [icon, setIcon] = useState('✨')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState([])
  const [metadata, setMetadata] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return

    let parsedMetadata = null
    if (metadata.trim()) {
      try {
        parsedMetadata = JSON.parse(metadata.trim())
      } catch {
        setError('metadata must be valid JSON')
        return
      }
    }

    setSaving(true)
    setError('')
    try {
      const doc = await api.createDocument({
        name: name.trim(),
        icon: icon || null,
        description: description.trim() || null,
        tags,
        metadata: parsedMetadata,
      })
      onCreated(doc)
      setName('')
      setIcon('✨')
      setDescription('')
      setTags([])
      setMetadata('')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">icon</label>
        <input
          type="text"
          className="w-full p-2 border border-slate-200 rounded-lg text-center bg-slate-50 text-xl focus:border-yellow-400 focus:outline-none"
          value={icon}
          onChange={(e) => setIcon(e.target.value)}
          maxLength={4}
        />
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
          name <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          placeholder="Item name"
          className="w-full p-2 border border-slate-200 rounded-lg text-sm focus:border-yellow-400 focus:outline-none"
          value={name}
          onChange={(e) => setName(e.target.value)}
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
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">tags</label>
        <TagInput
          selectedTags={tags}
          onAdd={(path) => setTags(t => [...t, path])}
          onRemove={(path) => setTags(t => t.filter(x => x !== path))}
          placeholder="Search taxonomy tags…"
          chipColor="bg-blue-100 text-blue-800 border-blue-200"
        />
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">metadata</label>
        <textarea
          placeholder='{"key": "value"}'
          rows={3}
          className="w-full p-2 border border-slate-200 rounded-lg text-xs font-mono focus:border-yellow-400 focus:outline-none resize-none bg-slate-50"
          value={metadata}
          onChange={(e) => setMetadata(e.target.value)}
        />
      </div>

      {error && <p className="text-red-500 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={!name.trim() || saving}
        className="w-full bg-slate-900 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-30 hover:bg-slate-700 transition-colors"
      >
        {saving ? 'Adding…' : 'Add to Index'}
      </button>
    </form>
  )
}
