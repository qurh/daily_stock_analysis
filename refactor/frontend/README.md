# Refactor Frontend (M4)

## Quick Start

```bash
cd refactor/frontend
npm install
export VITE_API_BASE_URL="http://localhost:18000/api/v2"
npm run dev
```

Default API base URL is `http://localhost:18000/api/v2`.

## Available Scripts

```bash
npm run dev
npm run test -- --run
npm run build
```

## M4 Functional Scope

- Chat page:
  - create session
  - send/load messages
  - optional `news.search` hint composition (`symbol/query/top_k`)
  - structured news insight panel rendering from tool trace
  - structured credit risk insight panel rendering from tool trace
  - structured market/macro/sentiment insight panel rendering from tool trace
  - insight filter chips (`all/news/credit/market/macro/sentiment`) and grouped collapsible insight section
  - inspect citations/tool trace
- Knowledge page:
  - upload markdown
  - optimize/ingest/get/delete document
  - semantic chunk search
- Workflow page:
  - start execution
  - fetch execution payload
  - cancel execution
  - inspect trace nodes
- Strategy page:
  - distill/review cognition memo
  - extract strategy
  - list versions
  - publish/bind/rollback strategy
  - publish gate hint when backend returns `STR-GATE-*`
  - list bindings
- Backtest page:
  - create job
  - fetch job status
  - list records
  - load aggregate performance

## Testing Coverage (Current)

- App shell routing and primary navigation.
- API helper defaults and error normalization.
- Chat page validation + create session action.
- Chat page `news.search` hint composition, news tags rendering, and structured factor insight rendering
  (`credit/market/macro/sentiment`).
- Chat page grouped insight filtering interaction and grouped insight count rendering.
- Knowledge page validation + upload action.
