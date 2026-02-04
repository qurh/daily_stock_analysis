# Frontend Local Development

## Prerequisites
- Node.js 18+ (LTS recommended)
- npm

## Directory Structure (Depth 2)
```
frontend/
  src/
    app/
    features/
    services/
    stores/
    types/
  next.config.js
  package.json
  package-lock.json
  postcss.config.js
  tailwind.config.js
  tsconfig.json
```

## Local Setup
1. `cd frontend`
2. `npm install`

## Environment
- `NEXT_PUBLIC_API_URL` (optional) sets the backend base URL.
- Example: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8888`

## Run
- `npm run dev` (default port `3001`)
- `npm run build` (production build)
- `npm run start` (serve the production build)

## Verify
- Open `http://localhost:3001`

## Common Issues
- `tsconfig.json` may be updated automatically by Next.js after upgrades; this is expected.
- If `npm audit` reports vulnerabilities, update dependencies intentionally (avoid blind `--force`).
