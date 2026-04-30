type UploadSectionProps = {
  file: File | null
  loading: boolean
  onFileChange: (file: File | null) => void
  onUpload: () => void
  statusMessage: string
}

export function UploadSection({
  file,
  loading,
  onFileChange,
  onUpload,
  statusMessage,
}: UploadSectionProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="panel-kicker">1. Upload PDF</p>
        <h2>Ingest document</h2>
      </div>

      <label className="field">
        <span>PDF file</span>
        <input
          accept="application/pdf"
          type="file"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
      </label>

      <button
        className="primary-button"
        disabled={!file || loading}
        type="button"
        onClick={onUpload}
      >
        {loading ? 'Working...' : 'Upload PDF'}
      </button>

      <p className="status-text">{statusMessage}</p>
    </section>
  )
}
