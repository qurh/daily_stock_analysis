import { getJson, postJson } from "../api";
import type {
  CognitionMemo,
  StrategyArtifact,
  StrategyBinding,
  StrategyBindingsResponse,
  StrategyVersionsResponse,
} from "../types";

export type DistillCognitionInput = {
  session_id: string;
  start_index?: number;
  end_index?: number;
  title?: string;
};

export type ReviewCognitionInput = {
  action: "approve" | "reject" | "edit";
  reviewer: string;
  editor_notes?: string;
  edited_markdown?: string;
};

export type ExtractStrategyInput = {
  strategy_type: "analysis" | "trading";
  source_scope?: string;
  prompt_ref?: string;
};

export type PublishStrategyInput = {
  backtest_job_id?: string;
  proposal_id?: string;
};

export type BindStrategyInput = {
  flow_id: string;
  prompt_refs?: string[];
  prompt_lock_mode?: "strict" | "lenient";
  effective_scope?: Record<string, unknown>;
};

export type RollbackStrategyInput = {
  reason?: string;
};

export type ListVersionsInput = {
  strategy_type?: string;
  status?: string;
  limit?: number;
};

export type ListBindingsInput = {
  flow_id?: string;
  strategy_id?: string;
  status?: string;
  limit?: number;
};

function buildQuery(input: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(input).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      return;
    }
    params.set(key, String(value));
  });
  return params.toString();
}

export async function distillCognition(input: DistillCognitionInput): Promise<CognitionMemo> {
  return postJson<CognitionMemo>("/strategy/cognition/distill", input);
}

export async function reviewCognition(memoId: string, input: ReviewCognitionInput): Promise<CognitionMemo> {
  return postJson<CognitionMemo>(`/strategy/cognition/${memoId}/review`, input);
}

export async function extractStrategy(input: ExtractStrategyInput): Promise<StrategyArtifact> {
  return postJson<StrategyArtifact>("/strategy/extract", input);
}

export async function listStrategyVersions(input: ListVersionsInput = {}): Promise<StrategyVersionsResponse> {
  const query = buildQuery({
    strategy_type: input.strategy_type,
    status: input.status,
    limit: input.limit,
  });
  const suffix = query ? `?${query}` : "";
  return getJson<StrategyVersionsResponse>(`/strategy/versions${suffix}`);
}

export async function publishStrategy(strategyId: string, input: PublishStrategyInput): Promise<StrategyArtifact> {
  return postJson<StrategyArtifact>(`/strategy/${strategyId}/publish`, input);
}

export async function bindStrategy(strategyId: string, input: BindStrategyInput): Promise<StrategyBinding> {
  return postJson<StrategyBinding>(`/strategy/${strategyId}/bind`, input);
}

export async function listStrategyBindings(input: ListBindingsInput = {}): Promise<StrategyBindingsResponse> {
  const query = buildQuery({
    flow_id: input.flow_id,
    strategy_id: input.strategy_id,
    status: input.status,
    limit: input.limit,
  });
  const suffix = query ? `?${query}` : "";
  return getJson<StrategyBindingsResponse>(`/strategy/bindings${suffix}`);
}

export async function rollbackStrategy(strategyId: string, input: RollbackStrategyInput): Promise<StrategyArtifact> {
  return postJson<StrategyArtifact>(`/strategy/${strategyId}/rollback`, input);
}
