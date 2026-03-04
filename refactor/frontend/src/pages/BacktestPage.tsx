import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import {
  createBacktestJob,
  getBacktestJob,
  getBacktestPerformance,
  listBacktestResults,
} from "../lib/services/backtest";
import type {
  BacktestJob,
  BacktestJobAccepted,
  BacktestPerformanceResponse,
  BacktestResultItem,
} from "../lib/types";

export function BacktestPage() {
  const [scope, setScope] = useState<"market" | "symbol">("market");
  const [symbol, setSymbol] = useState("");
  const [evalWindowDays, setEvalWindowDays] = useState(10);
  const [jobId, setJobId] = useState("");
  const [resultsLimit, setResultsLimit] = useState(50);
  const [resultsOutcome, setResultsOutcome] = useState("");
  const [resultsSymbol, setResultsSymbol] = useState("");

  const [jobAccepted, setJobAccepted] = useState<BacktestJobAccepted | null>(null);
  const [jobDetails, setJobDetails] = useState<BacktestJob | null>(null);
  const [resultItems, setResultItems] = useState<BacktestResultItem[]>([]);
  const [performance, setPerformance] = useState<BacktestPerformanceResponse | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleCreateJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (scope === "symbol" && !symbol.trim()) {
      setError("当范围为 symbol 时，symbol 不能为空。");
      return;
    }

    setIsSubmitting(true);
    try {
      const accepted = await createBacktestJob({
        scope,
        symbol: scope === "symbol" ? symbol.trim() : undefined,
        eval_window_days: evalWindowDays,
      });
      setJobAccepted(accepted);
      setJobId(accepted.job_id);
      setNotice(`回测任务已创建: ${accepted.job_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGetJob() {
    const normalizedJobId = jobId.trim();
    if (!normalizedJobId) {
      setError("job_id 不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const job = await getBacktestJob(normalizedJobId);
      setJobDetails(job);
      setNotice(`任务状态: ${job.status}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleListResults() {
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await listBacktestResults({
        job_id: jobId.trim() || undefined,
        symbol: resultsSymbol.trim() || undefined,
        outcome: resultsOutcome.trim() || undefined,
        limit: resultsLimit,
      });
      setResultItems(result.items);
      setNotice(`已加载 ${result.count} 条回测记录。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoadPerformance() {
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await getBacktestPerformance({
        job_id: jobId.trim() || undefined,
        symbol: resultsSymbol.trim() || undefined,
      });
      setPerformance(result);
      setNotice("绩效聚合已加载。");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-panel">
      <h2>回测中心</h2>
      <p>提交回测任务，查看任务状态、结果记录和聚合绩效指标，为策略发布提供量化依据。</p>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>创建任务</h3>
          <form className="form-grid" onSubmit={handleCreateJob}>
            <label htmlFor="backtest-scope">范围</label>
            <select id="backtest-scope" value={scope} onChange={(event) => setScope(event.target.value as "market" | "symbol")}>
              <option value="market">全市场</option>
              <option value="symbol">单标的</option>
            </select>

            <label htmlFor="backtest-symbol">标的代码</label>
            <input
              id="backtest-symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="000001.SZ"
              disabled={scope === "market"}
            />

            <label htmlFor="backtest-window">评估窗口天数</label>
            <input
              id="backtest-window"
              type="number"
              min={1}
              max={365}
              value={evalWindowDays}
              onChange={(event) => setEvalWindowDays(Number(event.target.value))}
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                创建回测任务
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>查询与聚合</h3>
          <div className="form-grid">
            <label htmlFor="backtest-job-id">任务ID</label>
            <input
              id="backtest-job-id"
              value={jobId}
              onChange={(event) => setJobId(event.target.value)}
              placeholder="job_id"
            />

            <label htmlFor="backtest-results-symbol">结果过滤标的</label>
            <input
              id="backtest-results-symbol"
              value={resultsSymbol}
              onChange={(event) => setResultsSymbol(event.target.value)}
              placeholder="可选标的"
            />

            <label htmlFor="backtest-results-outcome">结果过滤条件</label>
            <input
              id="backtest-results-outcome"
              value={resultsOutcome}
              onChange={(event) => setResultsOutcome(event.target.value)}
              placeholder="win/loss/insufficient_data"
            />

            <label htmlFor="backtest-results-limit">返回上限</label>
            <input
              id="backtest-results-limit"
              type="number"
              min={1}
              max={500}
              value={resultsLimit}
              onChange={(event) => setResultsLimit(Number(event.target.value))}
            />

            <div className="action-row wrap">
              <button type="button" onClick={handleGetJob} disabled={isSubmitting}>
                查询任务
              </button>
              <button type="button" onClick={handleListResults} disabled={isSubmitting}>
                查询记录
              </button>
              <button type="button" onClick={handleLoadPerformance} disabled={isSubmitting}>
                加载绩效
              </button>
            </div>
          </div>
        </article>
      </div>

      {error ? <p className="notice error">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>任务创建结果</h3>
          <pre>{JSON.stringify(jobAccepted, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>任务详情</h3>
          <pre>{JSON.stringify(jobDetails, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>绩效聚合</h3>
          <pre>{JSON.stringify(performance, null, 2)}</pre>
        </article>
      </div>

      <article className="card">
        <h3>结果记录</h3>
        {resultItems.length === 0 ? (
          <p className="empty">暂无记录数据。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>标的</th>
                  <th>方向</th>
                  <th>结果</th>
                  <th>收益率%</th>
                  <th>方向正确</th>
                  <th>创建时间</th>
                </tr>
              </thead>
              <tbody>
                {resultItems.map((item) => (
                  <tr key={item.record_id}>
                    <td>{item.symbol}</td>
                    <td>{item.direction}</td>
                    <td>{item.outcome}</td>
                    <td>{item.return_pct ?? "-"}</td>
                    <td>{item.direction_correct === null ? "-" : String(item.direction_correct)}</td>
                    <td>{item.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
