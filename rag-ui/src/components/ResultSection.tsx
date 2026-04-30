type Source = {
  document_id: string
  chunk_id: string
  text: string
}

type ResultSectionProps = {
  answer: string
  loading: boolean
  sources: Source[]
}

export function ResultSection({
  answer,
  loading,
  sources,
}: ResultSectionProps) {
  return (
    <section className="panel result-panel">
      <div className="panel-heading">
        <p className="panel-kicker">3. Answer + Sources</p>
        <h2>Response</h2>
      </div>

      <div className="answer-block">
        <h3>Answer</h3>
        <p>{loading ? 'Waiting for response...' : answer || 'No answer yet.'}</p>
      </div>

      <div className="sources-block">
        <h3>Sources</h3>
        {sources.length === 0 ? (
          <p>No sources yet.</p>
        ) : (
          <ul className="sources-list">
            {sources.map((source) => (
              <li key={source.chunk_id} className="source-item">
                <p className="source-meta">
                  {source.document_id} - {source.chunk_id}
                </p>
                <p>{source.text}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
