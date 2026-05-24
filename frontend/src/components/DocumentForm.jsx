import { useState } from 'react'
import { Plus } from 'lucide-react'
import TagInput from './TagInput'
import { api } from '../api/client'

export default function DocumentForm({ onCreated }) {
  const [name, setName] = useState('')
  const [icon, setIcon] = useState('✨')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim() || tags.length === 0) return
    setSaving(true)
    setError('')
    try {
      const doc = await api.createDocument({ name: name.trim(), icon, description: description.trim() || null, tags })
      onCreated(doc)
      setName('')
      setIcon('✨')
      setDescription('')
      setTags([])
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          className="w-12 p-2 border border-slate-200 rounded-lg text-center bg-slate-50 text-xl"
          value={icon}
          onChange={(e) => setIcon(e.target.value)}
          maxLength={4}
        />
        <input
          type="text"
          placeholder="Item name *"
          className="flex-1 p-2 border border-slate-200 rounded-lg text-sm focus:border-yellow-400 focus:outline-none"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>

      <input
        type="text"
        placeholder="Description (optional)"
        className="w-full p-2 border border-slate-200 rounded-lg text-sm focus:border-yellow-400 focus:outline-none"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <TagInput
        selectedTags={tags}
        onAdd={(path) => setTags(t => [...t, path])}
        onRemove={(path) => setTags(t => t.filter(x => x !== path))}
        placeholder="Add taxonomy tags *"
        chipColor="bg-blue-100 text-blue-800 border-blue-200"
      />

      {error && <p className="text-red-500 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={!name.trim() || tags.length === 0 || saving}
        className="w-full bg-slate-900 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-30 hover:bg-slate-700 transition-colors"
      >
        {saving ? 'Adding…' : 'Add to Index'}
      </button>
    </form>
  )
}
