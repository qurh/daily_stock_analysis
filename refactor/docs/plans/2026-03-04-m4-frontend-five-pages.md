# M4 Frontend Five Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver MVP M4 frontend first version with five pages (chat, knowledge, workflow, strategy, backtest) and backend `/api/v2` integration.

**Architecture:** Build a React + TypeScript SPA with router-based page modules, shared app shell, and a typed API client layer. Keep page components thin by delegating request logic to service helpers and normalize error handling in one place.

**Tech Stack:** React 18, TypeScript, Vite, React Router, Vitest, React Testing Library.

### Task 1: Establish frontend test baseline (RED)

**Files:**
- Modify: `refactor/frontend/package.json`
- Create: `refactor/frontend/src/test/setup.ts`
- Create: `refactor/frontend/vitest.config.ts`
- Create: `refactor/frontend/src/App.test.tsx`
- Create: `refactor/frontend/src/lib/api.test.ts`

**Step 1: Write failing tests for app navigation shell**

```tsx
expect(screen.getByRole("link", { name: /chat/i })).toBeInTheDocument();
expect(screen.getByText(/M4 Frontend Console/i)).toBeInTheDocument();
```

**Step 2: Write failing tests for API base URL resolution and JSON error extraction**

```ts
expect(resolveApiBaseUrl()).toBe("http://localhost:18000/api/v2");
await expect(requestJson("/x")).rejects.toThrow("request failed");
```

**Step 3: Run tests to verify RED**

Run: `cd refactor/frontend && npm test -- --runInBand`  
Expected: fail because test stack and target modules do not exist yet.

### Task 2: Build app shell and route skeleton (GREEN)

**Files:**
- Modify: `refactor/frontend/src/main.tsx`
- Replace: `refactor/frontend/src/App.tsx`
- Create: `refactor/frontend/src/app/layout/AppLayout.tsx`
- Create: `refactor/frontend/src/app/router.tsx`
- Create: `refactor/frontend/src/pages/ChatPage.tsx`
- Create: `refactor/frontend/src/pages/KnowledgePage.tsx`
- Create: `refactor/frontend/src/pages/WorkflowPage.tsx`
- Create: `refactor/frontend/src/pages/StrategyPage.tsx`
- Create: `refactor/frontend/src/pages/BacktestPage.tsx`
- Modify: `refactor/frontend/src/styles.css`

**Step 1: Implement minimal route-driven app shell**

```tsx
<Routes>
  <Route path="/" element={<Navigate to="/chat" replace />} />
  <Route path="/chat" element={<ChatPage />} />
  <Route path="/knowledge" element={<KnowledgePage />} />
</Routes>
```

**Step 2: Add shared navigation layout and responsive structure**

```tsx
<nav aria-label="Primary">
  <NavLink to="/chat">Chat</NavLink>
</nav>
```

**Step 3: Re-run tests**

Run: `cd refactor/frontend && npm test -- --runInBand`  
Expected: app-shell tests pass.

### Task 3: Implement API client and page-level interactions (RED -> GREEN)

**Files:**
- Create: `refactor/frontend/src/lib/api.ts`
- Create: `refactor/frontend/src/lib/types.ts`
- Create: `refactor/frontend/src/lib/services/chat.ts`
- Create: `refactor/frontend/src/lib/services/knowledge.ts`
- Create: `refactor/frontend/src/lib/services/workflow.ts`
- Create: `refactor/frontend/src/lib/services/strategy.ts`
- Create: `refactor/frontend/src/lib/services/backtest.ts`
- Modify: `refactor/frontend/src/pages/ChatPage.tsx`
- Modify: `refactor/frontend/src/pages/KnowledgePage.tsx`
- Modify: `refactor/frontend/src/pages/WorkflowPage.tsx`
- Modify: `refactor/frontend/src/pages/StrategyPage.tsx`
- Modify: `refactor/frontend/src/pages/BacktestPage.tsx`

**Step 1: Add failing interaction tests for at least chat + knowledge critical paths**

```tsx
await user.click(screen.getByRole("button", { name: /create session/i }));
expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/chat/sessions"), expect.anything());
```

```tsx
await user.click(screen.getByRole("button", { name: /upload document/i }));
expect(screen.getByText(/doc_id/i)).toBeInTheDocument();
```

**Step 2: Implement typed request helpers and service methods**

```ts
export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, init);
  ...
}
```

**Step 3: Implement page forms and result panels**

```tsx
const result = await createBacktestJob(payload);
setState(result);
```

**Step 4: Run targeted tests and fix failures**

Run: `cd refactor/frontend && npm test -- --runInBand`  
Expected: page interaction tests pass.

### Task 4: Build and documentation sync

**Files:**
- Modify: `refactor/frontend/README.md`
- Modify: `refactor/docs/CHANGELOG.md`
- Create: `refactor/docs/迭代开发记录/2026-03-04-迭代268-M4-frontend-five-pages.md`

**Step 1: Update frontend usage docs**

```markdown
VITE_API_BASE_URL=http://localhost:18000/api/v2
npm run dev
```

**Step 2: Record feature scope and verification evidence**

```markdown
M4 frontend pages: Chat / Knowledge / Workflow / Strategy / Backtest
```

**Step 3: Final verification**

Run: `cd refactor/frontend && npm run test -- --runInBand && npm run build`  
Expected: pass.
