type QuerySectionProps = {
  documentId: string | null
  loading: boolean
  query: string
  onQueryChange: (query: string) => void
  onSubmit: () => void
}

export function QuerySection({
  documentId,
  loading,
  query,
  onQueryChange,
  onSubmit,
}: QuerySectionProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="panel-kicker">2. Ask Question</p>
        <h2>Query the document</h2>
      </div>

      <label className="field">
        <span>Question</span>
        <input
          placeholder="What does this PDF say about healthcare?"
          type="text"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </label>

      <button
        className="primary-button"
        disabled={!documentId || !query.trim() || loading}
        type="button"
        onClick={onSubmit}
      >
        {loading ? 'Working...' : 'Ask'}
      </button>

      <p className="status-text">
        {documentId
          ? `Active document: ${documentId}`
          : 'Upload a PDF before asking a question.'}
      </p>
    </section>
  )
}
