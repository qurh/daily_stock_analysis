import { getJson, postJson } from "../api";
import type {
  BacktestJob,
  BacktestJobAccepted,
  BacktestPerformanceResponse,
  BacktestResultsResponse,
} from "../types";

export type CreateBacktestJobInput = {
  scope: "market" | "symbol";
  symbol?: string;
  eval_window_days: number;
};

export type ListBacktestResultsInput = {
  job_id?: string;
  symbol?: string;
  outcome?: string;
  limit?: number;
};

export type GetBacktestPerformanceInput = {
  job_id?: string;
  symbol?: string;
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

export async function createBacktestJob(input: CreateBacktestJobInput): Promise<BacktestJobAccepted> {
  return postJson<BacktestJobAccepted>("/backtest/jobs", input);
}

export async function getBacktestJob(jobId: string): Promise<BacktestJob> {
  return getJson<BacktestJob>(`/backtest/jobs/${jobId}`);
}

export async function listBacktestResults(input: ListBacktestResultsInput = {}): Promise<BacktestResultsResponse> {
  const query = buildQuery({
    job_id: input.job_id,
    symbol: input.symbol,
    outcome: input.outcome,
    limit: input.limit,
  });
  const suffix = query ? `?${query}` : "";
  return getJson<BacktestResultsResponse>(`/backtest/results${suffix}`);
}

export async function getBacktestPerformance(
  input: GetBacktestPerformanceInput = {},
): Promise<BacktestPerformanceResponse> {
  const query = buildQuery({
    job_id: input.job_id,
    symbol: input.symbol,
  });
  const suffix = query ? `?${query}` : "";
  return getJson<BacktestPerformanceResponse>(`/backtest/performance${suffix}`);
}
