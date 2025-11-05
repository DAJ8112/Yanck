# Frontend

React + TypeScript dashboard powered by Vite. Provides the no-code interface for configuring chatbots, uploading documents, and previewing RAG conversations.

## Prerequisites

- Node.js 18+
- Backend API running locally (defaults to `http://localhost:8000/api`)

You can override the API base URL by creating a `.env.local` file with:

```bash
VITE_API_URL="http://localhost:8000/api"
```

## Commands

```bash
npm install
npm run dev
npm run lint
npm run build
npm run test
```

The development server runs on http://localhost:5173.

## Usage

1. Start the backend stack (see repository root README).
2. Run `npm run dev` and open the dashboard.
3. Paste a valid JWT access token into the header form — the app stores it in `localStorage` for subsequent API calls.
4. From the Chatbots list you can create assistants, upload documents in the detail view, and chat against the RAG pipeline.

Vitest tests live under `src/__tests__`; run `npm run test` for quick smoke coverage.
