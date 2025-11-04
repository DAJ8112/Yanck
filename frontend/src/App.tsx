import './App.css'

function App() {
  return (
    <main className="app">
      <header className="app__header">
        <h1>RAG Builder</h1>
        <p>No-code workspace for creating retrieval-augmented chatbots.</p>
      </header>
      <section className="app__grid">
        <article className="app__card">
          <h2>Authentication</h2>
          <p>Secure access control and API key management for model providers.</p>
        </article>
        <article className="app__card">
          <h2>Document Ingestion</h2>
          <p>Upload documents, process text, and build a vector index automatically.</p>
        </article>
        <article className="app__card">
          <h2>Chatbot Playground</h2>
          <p>Preview RAG conversations before deploying to the web.</p>
        </article>
        <article className="app__card">
          <h2>Deploy & Embed</h2>
          <p>Generate shareable links and iframe snippets for your chatbot.</p>
        </article>
      </section>
    </main>
  )
}

export default App
