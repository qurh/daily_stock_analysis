export type JsonObject = Record<string, unknown>;

export type ChatSession = {
  session_id: string;
  user_id: string;
  memory_policy: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ChatCitation = Record<string, unknown>;

export type ChatMessage = {
  message_id: string;
  session_id: string;
  role: string;
  content: string;
  citations: ChatCitation[];
  tool_trace: JsonObject;
  created_at: string;
};

export type ChatPostMessageResponse = {
  session_id: string;
  assistant: ChatMessage;
};

export type ChatListMessagesResponse = {
  session_id: string;
  messages: ChatMessage[];
};

export type KnowledgeUploadResponse = {
  doc_id: string;
  title: string;
  status: string;
  tags: string[];
};

export type KnowledgeOptimizeResponse = {
  doc_id: string;
  status: string;
  optimized_markdown: string;
};

export type KnowledgeIngestResponse = {
  doc_id: string;
  status: string;
  chunk_count: number;
};

export type KnowledgeDocument = {
  doc_id: string;
  title: string;
  source_type: string;
  status: string;
  tags: string[];
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type KnowledgeChunkHit = {
  doc_id: string;
  chunk_id: string;
  section_path: string;
  score: number;
  summary?: string;
  content?: string;
};

export type KnowledgeSearchChunksResponse = {
  hits: KnowledgeChunkHit[];
};

export type WorkflowExecutionAccepted = {
  execution_id: string;
  status: string;
};

export type WorkflowTraceNode = {
  node_id: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  attempts: number;
  duration_ms: number;
  degraded: boolean;
  failure_code: string | null;
  degrade_reason: string | null;
  failure_context: string | null;
};

export type WorkflowExecution = {
  execution_id: string;
  flow_id: string;
  input: JsonObject;
  status: string;
  output: JsonObject;
  trace: {
    flow_id: string;
    nodes: WorkflowTraceNode[];
  };
  created_at: string;
  updated_at: string;
};

export type WorkflowCancelResponse = {
  execution_id: string;
  cancelled: boolean;
};

export type CognitionMemo = {
  memo_id: string;
  title: string;
  markdown: string;
  source_sessions: string[];
  source_message_ids: string[];
  status: string;
  reviewer: string | null;
  review_notes: string | null;
  knowledge_doc_id: string | null;
  created_at: string;
  updated_at: string;
};

export type StrategyArtifact = {
  strategy_id: string;
  strategy_type: string;
  version: number;
  rules: string[];
  thresholds: JsonObject;
  conditions: JsonObject;
  source_memo_ids: string[];
  status: string;
  gate_result: JsonObject;
  backtest_job_id: string | null;
  created_at: string;
  updated_at: string;
};

export type StrategyVersionsResponse = {
  items: StrategyArtifact[];
  count: number;
};

export type StrategyBinding = {
  binding_id: string;
  strategy_id: string;
  flow_id: string;
  prompt_refs: string[];
  effective_scope: JsonObject;
  prompt_lock_mode: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type StrategyBindingsResponse = {
  items: StrategyBinding[];
  count: number;
};

export type BacktestJob = {
  job_id: string;
  scope: string;
  symbol: string | null;
  eval_window_days: number;
  status: string;
  progress: number;
  metrics: JsonObject;
  engine_version: string;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
};

export type BacktestJobAccepted = {
  job_id: string;
  status: string;
};

export type BacktestResultItem = {
  record_id: string;
  job_id: string;
  analysis_job_id: string;
  symbol: string;
  direction: string;
  outcome: string;
  return_pct: number | null;
  direction_correct: boolean | null;
  flags: string[];
  created_at: string;
};

export type BacktestResultsResponse = {
  items: BacktestResultItem[];
  count: number;
};

export type BacktestPerformanceResponse = {
  scope: string;
  symbol: string | null;
  job_id: string | null;
  engine_version: string;
  metrics: JsonObject;
};
