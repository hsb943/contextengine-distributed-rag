import { useState } from 'react'
import './App.css'
import { QuerySection } from './components/QuerySection'
import { ResultSection } from './components/ResultSection'
import { UploadSection } from './components/UploadSection'

type Source = {
  document_id: string
  chunk_id: string
  text: string
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState('No document uploaded yet.')

  const handleUpload = async () => {
    if (!file) {
      setStatusMessage('Select a PDF file before uploading.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)
    setStatusMessage('Uploading PDF...')
    setAnswer('')
    setSources([])

    try {
      const response = await fetch(`${API_BASE_URL}/ingest/file`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
      }

      const data: { document_id: string; num_chunks: number } =
        await response.json()
      setDocumentId(data.document_id)
      setStatusMessage(
        `Stored ${data.document_id} with ${data.num_chunks} chunk${data.num_chunks === 1 ? '' : 's'}.`,
      )
    } catch (error) {
      console.log(error)
      setStatusMessage('Upload failed. Check the ingestion service logs.')
    } finally {
      setLoading(false)
    }
  }

  const handleAsk = async () => {
    if (!query.trim()) {
      return
    }

    setLoading(true)
    setStatusMessage('Generating answer...')
    setAnswer('')
    setSources([])

    try {
      const payload: Record<string, unknown> = {
        query,
        top_k: 5,
      }

      if (documentId) {
        payload.document_id = documentId
      }

      const response = await fetch(`${API_BASE_URL}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`Answer request failed with status ${response.status}`)
      }

      const data: { answer: string; sources: Source[] } = await response.json()
      setAnswer(data.answer)
      setSources(data.sources)
      setStatusMessage('Answer ready.')
    } catch (error) {
      console.log(error)
      setStatusMessage('Answer request failed. Check the LLM service logs.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <h1>Upload a PDF and ask questions about it.</h1>
        <p className="intro">
          This page talks to the Ray Serve backend for both ingestion and
          answers.
        </p>
      </header>

      <div className="layout">
        <div className="top-row">
          <UploadSection
            file={file}
            loading={loading}
            onFileChange={setFile}
            onUpload={handleUpload}
            statusMessage={statusMessage}
          />

          <QuerySection
            loading={loading}
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleAsk}
          />
        </div>

        <ResultSection answer={answer} loading={loading} sources={sources} />
      </div>
    </main>
  )
}

export default App
