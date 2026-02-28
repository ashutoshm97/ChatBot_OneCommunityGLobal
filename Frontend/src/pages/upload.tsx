import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileText, Video, Upload as UploadIcon, ArrowLeft } from 'lucide-react'
import { documentsAPI } from '../lib/api'

export default function Upload() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'text' | 'video'>('text')

  // Text form
  const [text, setText] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const [textSource, setTextSource] = useState('')
  const [textLoading, setTextLoading] = useState(false)
  const [textError, setTextError] = useState('')
  const [textSuccess, setTextSuccess] = useState('')

  // Video form
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoTitle, setVideoTitle] = useState('')
  const [videoDescription, setVideoDescription] = useState('')
  const [videoLoading, setVideoLoading] = useState(false)
  const [videoError, setVideoError] = useState('')
  const [videoSuccess, setVideoSuccess] = useState('')

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setTextError('')
    setTextSuccess('')
    const content = text.trim()
    if (!content) {
      setTextError('Please enter or paste some text.')
      return
    }
    setTextLoading(true)
    try {
      await documentsAPI.uploadText(content, {
        title: textTitle.trim() || undefined,
        source: textSource.trim() || undefined,
      })
      setTextSuccess('Document stored successfully.')
      setText('')
      setTextTitle('')
      setTextSource('')
    } catch (err: any) {
      setTextError(err.response?.data?.detail ?? err.message ?? 'Failed to store document.')
    } finally {
      setTextLoading(false)
    }
  }

  const handleVideoSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setVideoError('')
    setVideoSuccess('')
    if (!videoFile) {
      setVideoError('Please select a video file.')
      return
    }
    if (!videoFile.type.startsWith('video/')) {
      setVideoError('File must be a video.')
      return
    }
    setVideoLoading(true)
    try {
      await documentsAPI.uploadVideo(
        videoFile,
        videoTitle.trim() || undefined,
        videoDescription.trim() || undefined
      )
      setVideoSuccess('Video processed and stored successfully.')
      setVideoFile(null)
      setVideoTitle('')
      setVideoDescription('')
    } catch (err: any) {
      setVideoError(err.response?.data?.detail ?? err.message ?? 'Failed to upload video.')
    } finally {
      setVideoLoading(false)
    }
  }

  const handleTextFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setText(String(reader.result ?? ''))
    reader.readAsText(file)
    e.target.value = ''
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
            to="/documents"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            My documents
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-2xl w-full mx-auto px-4 py-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-6">Upload</h1>

        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg mb-6">
          <button
            type="button"
            onClick={() => setActiveTab('text')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'text'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            Text
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('video')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'video'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Video className="w-4 h-4" />
            Video
          </button>
        </div>

        {activeTab === 'text' && (
          <form onSubmit={handleTextSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste or type document text..."
                rows={8}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent resize-y"
              />
              <div className="mt-1 flex justify-end">
                <label className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                  Or upload .txt file
                  <input
                    type="file"
                    accept=".txt,text/plain"
                    className="hidden"
                    onChange={handleTextFileSelect}
                  />
                </label>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title (optional)
                </label>
                <input
                  type="text"
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                  placeholder="Document title"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source (optional)
                </label>
                <input
                  type="text"
                  value={textSource}
                  onChange={(e) => setTextSource(e.target.value)}
                  placeholder="e.g. example.com"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent"
                />
              </div>
            </div>
            {textError && (
              <p className="text-sm text-red-600">{textError}</p>
            )}
            {textSuccess && (
              <p className="text-sm text-green-600">{textSuccess}</p>
            )}
            <button
              type="submit"
              disabled={textLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {textLoading ? (
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              ) : (
                <UploadIcon className="w-4 h-4" />
              )}
              {textLoading ? 'Storing…' : 'Store document'}
            </button>
          </form>
        )}

        {activeTab === 'video' && (
          <form onSubmit={handleVideoSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Video file
              </label>
              <div className="border border-gray-200 border-dashed rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setVideoFile(e.target.files?.[0] ?? null)}
                  className="hidden"
                  id="video-input"
                />
                <label
                  htmlFor="video-input"
                  className="cursor-pointer flex flex-col items-center gap-2 text-gray-500 hover:text-gray-700"
                >
                  <Video className="w-10 h-10" />
                  <span className="text-sm">
                    {videoFile ? videoFile.name : 'Choose a video file'}
                  </span>
                </label>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title (optional)
              </label>
              <input
                type="text"
                value={videoTitle}
                onChange={(e) => setVideoTitle(e.target.value)}
                placeholder="Video title"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <textarea
                value={videoDescription}
                onChange={(e) => setVideoDescription(e.target.value)}
                placeholder="Brief description"
                rows={2}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent resize-y"
              />
            </div>
            {videoError && (
              <p className="text-sm text-red-600">{videoError}</p>
            )}
            {videoSuccess && (
              <p className="text-sm text-green-600">{videoSuccess}</p>
            )}
            <button
              type="submit"
              disabled={videoLoading || !videoFile}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {videoLoading ? (
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              ) : (
                <UploadIcon className="w-4 h-4" />
              )}
              {videoLoading ? 'Processing…' : 'Upload & process video'}
            </button>
          </form>
        )}
      </main>
    </div>
  )
}
