import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, FileText, Video, Trash2 } from 'lucide-react'
import { documentsAPI, type DocumentRecord } from '../lib/api'

function formatDate(iso: string) {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function docTitle(doc: DocumentRecord): string {
  const meta = doc.metadata || {}
  if (typeof meta.title === 'string' && meta.title.trim()) return meta.title
  if (typeof meta.filename === 'string' && meta.filename.trim()) return meta.filename
  const preview = (doc.text || '').slice(0, 50)
  return preview ? `${preview}${doc.text.length > 50 ? '…' : ''}` : 'Untitled'
}

export default function Documents() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'text' | 'video'>('all')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchDocuments = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await documentsAPI.list({
        limit: 100,
        document_type: filter === 'all' ? undefined : filter,
      })
      setDocuments(res.documents)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? 'Failed to load documents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [filter])

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await documentsAPI.delete(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? 'Failed to delete.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col">
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            to="/"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
          <Link
            to="/upload"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Upload
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-2xl w-full mx-auto px-4 py-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-6">Documents</h1>

        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg mb-6">
          {(['all', 'text', 'video'] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`flex-1 py-2 rounded-md text-sm font-medium capitalize transition ${
                filter === f
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {error && (
          <p className="text-sm text-red-600 mb-4">{error}</p>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <span className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-900" />
          </div>
        ) : documents.length === 0 ? (
          <p className="text-sm text-gray-500 py-8 text-center">
            No documents yet. <Link to="/upload" className="text-gray-900 underline">Upload</Link> text or video to get started.
          </p>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg"
              >
                <span className="text-gray-400">
                  {doc.document_type === 'video' ? (
                    <Video className="w-5 h-5" />
                  ) : (
                    <FileText className="w-5 h-5" />
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {docTitle(doc)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDate(doc.created_at)}
                    {doc.metadata?.chunk_index != null && doc.metadata?.total_chunks != null && (
                      <span> · Chunk {Number(doc.metadata.chunk_index) + 1}/{doc.metadata.total_chunks}</span>
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                  aria-label="Delete"
                >
                  {deletingId === doc.id ? (
                    <span className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-gray-600 block" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
