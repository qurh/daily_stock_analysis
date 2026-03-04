import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import {
  bindStrategy,
  distillCognition,
  extractStrategy,
  listStrategyBindings,
  listStrategyVersions,
  publishStrategy,
  reviewCognition,
  rollbackStrategy,
} from "../lib/services/strategy";
import type { CognitionMemo, StrategyArtifact, StrategyBinding } from "../lib/types";

function parseOptionalNumber(value: string): number | undefined {
  const normalized = value.trim();
  if (!normalized) {
    return undefined;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parseJsonObject(input: string): Record<string, unknown> {
  const trimmed = input.trim();
  if (!trimmed) {
    return {};
  }
  const parsed = JSON.parse(trimmed);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("生效范围必须是 JSON 对象。");
  }
  return parsed as Record<string, unknown>;
}

function resolvePublishGateHint(message: string): string {
  const normalized = message.toLowerCase();
  if (normalized.includes("str-gate-005")) {
    return "发布闸门提示: 发布前需满足回测 sample_size >= 5 且 win_rate_pct >= 50。";
  }
  if (normalized.includes("str-gate-009")) {
    return "发布闸门提示: 当前环境在严格发布模式下要求填写 proposal_id。";
  }
  if (normalized.includes("str-gate-007") || normalized.includes("str-gate-008")) {
    return "发布闸门提示: 关联 proposal 必须存在、匹配 strategy_id 且已通过审批。";
  }
  return "";
}

export function StrategyPage() {
  const [distillSessionId, setDistillSessionId] = useState("");
  const [distillStart, setDistillStart] = useState("");
  const [distillEnd, setDistillEnd] = useState("");
  const [distillTitle, setDistillTitle] = useState("");

  const [reviewMemoId, setReviewMemoId] = useState("");
  const [reviewAction, setReviewAction] = useState<"approve" | "reject" | "edit">("approve");
  const [reviewer, setReviewer] = useState("owner");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewMarkdown, setReviewMarkdown] = useState("");

  const [extractType, setExtractType] = useState<"analysis" | "trading">("analysis");
  const [extractScope, setExtractScope] = useState("indexed_memos");
  const [extractPromptRef, setExtractPromptRef] = useState("");

  const [versionsType, setVersionsType] = useState("");
  const [versionsStatus, setVersionsStatus] = useState("");
  const [versionsLimit, setVersionsLimit] = useState(50);

  const [publishStrategyId, setPublishStrategyId] = useState("");
  const [publishBacktestJobId, setPublishBacktestJobId] = useState("");
  const [publishProposalId, setPublishProposalId] = useState("");

  const [bindStrategyId, setBindStrategyId] = useState("");
  const [bindFlowId, setBindFlowId] = useState("stock_analysis_v1");
  const [bindPromptRefs, setBindPromptRefs] = useState("");
  const [bindLockMode, setBindLockMode] = useState<"" | "strict" | "lenient">("");
  const [bindScopeJson, setBindScopeJson] = useState('{"scope":"global"}');

  const [rollbackStrategyId, setRollbackStrategyId] = useState("");
  const [rollbackReason, setRollbackReason] = useState("");

  const [bindingsFlowId, setBindingsFlowId] = useState("");
  const [bindingsStrategyId, setBindingsStrategyId] = useState("");
  const [bindingsStatus, setBindingsStatus] = useState("");
  const [bindingsLimit, setBindingsLimit] = useState(100);

  const [memoResult, setMemoResult] = useState<CognitionMemo | null>(null);
  const [strategyResult, setStrategyResult] = useState<StrategyArtifact | null>(null);
  const [versions, setVersions] = useState<StrategyArtifact[]>([]);
  const [bindings, setBindings] = useState<StrategyBinding[]>([]);
  const [bindingResult, setBindingResult] = useState<StrategyBinding | null>(null);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [publishGateHint, setPublishGateHint] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleDistill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const sessionId = distillSessionId.trim();
    if (!sessionId) {
      setError("session_id 不能为空。");
      return;
    }
    setIsSubmitting(true);
    try {
      const memo = await distillCognition({
        session_id: sessionId,
        start_index: parseOptionalNumber(distillStart),
        end_index: parseOptionalNumber(distillEnd),
        title: distillTitle.trim() || undefined,
      });
      setMemoResult(memo);
      setReviewMemoId(memo.memo_id);
      setNotice(`认知蒸馏完成: ${memo.memo_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const memoId = reviewMemoId.trim();
    if (!memoId) {
      setError("memo_id 不能为空。");
      return;
    }
    if (!reviewer.trim()) {
      setError("reviewer 不能为空。");
      return;
    }
    setIsSubmitting(true);
    try {
      const memo = await reviewCognition(memoId, {
        action: reviewAction,
        reviewer: reviewer.trim(),
        editor_notes: reviewNotes.trim() || undefined,
        edited_markdown: reviewMarkdown.trim() || undefined,
      });
      setMemoResult(memo);
      setNotice(`认知审阅完成: ${memo.memo_id} (${memo.status})`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleExtract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const artifact = await extractStrategy({
        strategy_type: extractType,
        source_scope: extractScope.trim() || undefined,
        prompt_ref: extractPromptRef.trim() || undefined,
      });
      setStrategyResult(artifact);
      setPublishStrategyId(artifact.strategy_id);
      setBindStrategyId(artifact.strategy_id);
      setRollbackStrategyId(artifact.strategy_id);
      setNotice(`策略提取完成: ${artifact.strategy_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoadVersions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const response = await listStrategyVersions({
        strategy_type: versionsType.trim() || undefined,
        status: versionsStatus.trim() || undefined,
        limit: versionsLimit,
      });
      setVersions(response.items);
      setNotice(`已加载 ${response.count} 条策略版本。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handlePublish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const strategyId = publishStrategyId.trim();
    if (!strategyId) {
      setError("发布前必须填写 strategy_id。");
      setPublishGateHint("");
      return;
    }
    setError("");
    setNotice("");
    setPublishGateHint("");
    setIsSubmitting(true);
    try {
      const artifact = await publishStrategy(strategyId, {
        backtest_job_id: publishBacktestJobId.trim() || undefined,
        proposal_id: publishProposalId.trim() || undefined,
      });
      setStrategyResult(artifact);
      setNotice(`策略发布成功: ${artifact.strategy_id} (${artifact.status})`);
      setPublishGateHint("");
    } catch (err) {
      const message = toErrorMessage(err);
      setError(message);
      setPublishGateHint(resolvePublishGateHint(message));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleBind(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const strategyId = bindStrategyId.trim();
    const flowId = bindFlowId.trim();
    if (!strategyId || !flowId) {
      setError("绑定前必须填写 strategy_id 和 flow_id。");
      return;
    }

    let scope: Record<string, unknown>;
    try {
      scope = parseJsonObject(bindScopeJson);
    } catch (err) {
      setError(toErrorMessage(err));
      return;
    }

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const binding = await bindStrategy(strategyId, {
        flow_id: flowId,
        prompt_refs: bindPromptRefs
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        prompt_lock_mode: bindLockMode || undefined,
        effective_scope: scope,
      });
      setBindingResult(binding);
      setNotice(`策略绑定成功: ${binding.binding_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRollback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const strategyId = rollbackStrategyId.trim();
    if (!strategyId) {
      setError("回滚前必须填写 strategy_id。");
      return;
    }

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const artifact = await rollbackStrategy(strategyId, {
        reason: rollbackReason.trim() || undefined,
      });
      setStrategyResult(artifact);
      setNotice(`策略已回滚: ${artifact.strategy_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoadBindings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const response = await listStrategyBindings({
        flow_id: bindingsFlowId.trim() || undefined,
        strategy_id: bindingsStrategyId.trim() || undefined,
        status: bindingsStatus.trim() || undefined,
        limit: bindingsLimit,
      });
      setBindings(response.items);
      setNotice(`已加载 ${response.count} 条绑定记录。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-panel">
      <h2>策略中心</h2>
      <p>执行认知蒸馏、策略提取、发布闸门校验与流程绑定，形成可持续演化的策略资产。</p>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>1）认知蒸馏</h3>
          <form className="form-grid" onSubmit={handleDistill}>
            <label htmlFor="strategy-distill-session-id">会话ID</label>
            <input
              id="strategy-distill-session-id"
              value={distillSessionId}
              onChange={(event) => setDistillSessionId(event.target.value)}
              placeholder="session_id"
            />

            <label htmlFor="strategy-distill-start">起始索引</label>
            <input
              id="strategy-distill-start"
              value={distillStart}
              onChange={(event) => setDistillStart(event.target.value)}
              placeholder="可选"
            />

            <label htmlFor="strategy-distill-end">结束索引</label>
            <input
              id="strategy-distill-end"
              value={distillEnd}
              onChange={(event) => setDistillEnd(event.target.value)}
              placeholder="可选"
            />

            <label htmlFor="strategy-distill-title">标题</label>
            <input
              id="strategy-distill-title"
              value={distillTitle}
              onChange={(event) => setDistillTitle(event.target.value)}
              placeholder="可选标题"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                执行蒸馏
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>2）审阅认知</h3>
          <form className="form-grid" onSubmit={handleReview}>
            <label htmlFor="strategy-review-memo-id">认知备忘ID</label>
            <input
              id="strategy-review-memo-id"
              value={reviewMemoId}
              onChange={(event) => setReviewMemoId(event.target.value)}
              placeholder="memo_id"
            />

            <label htmlFor="strategy-review-action">操作</label>
            <select
              id="strategy-review-action"
              value={reviewAction}
              onChange={(event) => setReviewAction(event.target.value as "approve" | "reject" | "edit")}
            >
              <option value="approve">通过</option>
              <option value="reject">拒绝</option>
              <option value="edit">编辑后通过</option>
            </select>

            <label htmlFor="strategy-review-reviewer">审阅人</label>
            <input
              id="strategy-review-reviewer"
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
              placeholder="owner"
            />

            <label htmlFor="strategy-review-notes">编辑备注</label>
            <textarea
              id="strategy-review-notes"
              rows={4}
              value={reviewNotes}
              onChange={(event) => setReviewNotes(event.target.value)}
              placeholder="可选"
            />

            <label htmlFor="strategy-review-markdown">修订后的 Markdown</label>
            <textarea
              id="strategy-review-markdown"
              rows={4}
              value={reviewMarkdown}
              onChange={(event) => setReviewMarkdown(event.target.value)}
              placeholder="可选"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                提交审阅
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>3）提取策略</h3>
          <form className="form-grid" onSubmit={handleExtract}>
            <label htmlFor="strategy-extract-type">策略类型</label>
            <select
              id="strategy-extract-type"
              value={extractType}
              onChange={(event) => setExtractType(event.target.value as "analysis" | "trading")}
            >
              <option value="analysis">分析策略</option>
              <option value="trading">交易策略</option>
            </select>

            <label htmlFor="strategy-extract-scope">提取范围</label>
            <input
              id="strategy-extract-scope"
              value={extractScope}
              onChange={(event) => setExtractScope(event.target.value)}
            />

            <label htmlFor="strategy-extract-prompt-ref">提示词引用</label>
            <input
              id="strategy-extract-prompt-ref"
              value={extractPromptRef}
              onChange={(event) => setExtractPromptRef(event.target.value)}
              placeholder="可选"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                执行提取
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>4）版本查询</h3>
          <form className="form-grid" onSubmit={handleLoadVersions}>
            <label htmlFor="strategy-versions-type">类型过滤</label>
            <input
              id="strategy-versions-type"
              value={versionsType}
              onChange={(event) => setVersionsType(event.target.value)}
              placeholder="analysis/trading"
            />

            <label htmlFor="strategy-versions-status">状态过滤</label>
            <input
              id="strategy-versions-status"
              value={versionsStatus}
              onChange={(event) => setVersionsStatus(event.target.value)}
              placeholder="candidate/active"
            />

            <label htmlFor="strategy-versions-limit">返回上限</label>
            <input
              id="strategy-versions-limit"
              type="number"
              min={1}
              max={200}
              value={versionsLimit}
              onChange={(event) => setVersionsLimit(Number(event.target.value))}
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                加载版本
              </button>
            </div>
          </form>
        </article>
      </div>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>5）发布策略</h3>
          <form className="form-grid" onSubmit={handlePublish}>
            <label htmlFor="strategy-publish-id">策略ID</label>
            <input
              id="strategy-publish-id"
              value={publishStrategyId}
              onChange={(event) => setPublishStrategyId(event.target.value)}
              placeholder="strategy_id"
            />

            <label htmlFor="strategy-publish-backtest-job-id">回测任务ID</label>
            <input
              id="strategy-publish-backtest-job-id"
              value={publishBacktestJobId}
              onChange={(event) => setPublishBacktestJobId(event.target.value)}
              placeholder="闸门校验可能要求"
            />

            <label htmlFor="strategy-publish-proposal-id">提案ID</label>
            <input
              id="strategy-publish-proposal-id"
              value={publishProposalId}
              onChange={(event) => setPublishProposalId(event.target.value)}
              placeholder="可选"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                发布策略
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>6）绑定流程</h3>
          <form className="form-grid" onSubmit={handleBind}>
            <label htmlFor="strategy-bind-id">策略ID</label>
            <input
              id="strategy-bind-id"
              value={bindStrategyId}
              onChange={(event) => setBindStrategyId(event.target.value)}
              placeholder="strategy_id"
            />

            <label htmlFor="strategy-bind-flow-id">流程ID</label>
            <input
              id="strategy-bind-flow-id"
              value={bindFlowId}
              onChange={(event) => setBindFlowId(event.target.value)}
              placeholder="stock_analysis_v1"
            />

            <label htmlFor="strategy-bind-prompt-refs">提示词引用列表（CSV）</label>
            <input
              id="strategy-bind-prompt-refs"
              value={bindPromptRefs}
              onChange={(event) => setBindPromptRefs(event.target.value)}
              placeholder="prompt.chat.reply@1,prompt.analysis.report@2"
            />

            <label htmlFor="strategy-bind-lock-mode">提示词锁定模式</label>
            <select
              id="strategy-bind-lock-mode"
              value={bindLockMode}
              onChange={(event) => setBindLockMode(event.target.value as "" | "strict" | "lenient")}
            >
              <option value="">继承默认</option>
              <option value="strict">严格</option>
              <option value="lenient">宽松</option>
            </select>

            <label htmlFor="strategy-bind-scope">生效范围 JSON</label>
            <textarea
              id="strategy-bind-scope"
              rows={4}
              value={bindScopeJson}
              onChange={(event) => setBindScopeJson(event.target.value)}
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                绑定策略
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>7）回滚策略</h3>
          <form className="form-grid" onSubmit={handleRollback}>
            <label htmlFor="strategy-rollback-id">策略ID</label>
            <input
              id="strategy-rollback-id"
              value={rollbackStrategyId}
              onChange={(event) => setRollbackStrategyId(event.target.value)}
              placeholder="strategy_id"
            />

            <label htmlFor="strategy-rollback-reason">回滚原因</label>
            <textarea
              id="strategy-rollback-reason"
              rows={4}
              value={rollbackReason}
              onChange={(event) => setRollbackReason(event.target.value)}
              placeholder="可选"
            />

            <div className="action-row">
              <button type="submit" className="danger" disabled={isSubmitting}>
                执行回滚
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>8）绑定查询</h3>
          <form className="form-grid" onSubmit={handleLoadBindings}>
            <label htmlFor="strategy-bindings-flow-id">流程ID</label>
            <input
              id="strategy-bindings-flow-id"
              value={bindingsFlowId}
              onChange={(event) => setBindingsFlowId(event.target.value)}
              placeholder="可选"
            />

            <label htmlFor="strategy-bindings-strategy-id">策略ID</label>
            <input
              id="strategy-bindings-strategy-id"
              value={bindingsStrategyId}
              onChange={(event) => setBindingsStrategyId(event.target.value)}
              placeholder="可选"
            />

            <label htmlFor="strategy-bindings-status">状态</label>
            <input
              id="strategy-bindings-status"
              value={bindingsStatus}
              onChange={(event) => setBindingsStatus(event.target.value)}
              placeholder="active/inactive"
            />

            <label htmlFor="strategy-bindings-limit">返回上限</label>
            <input
              id="strategy-bindings-limit"
              type="number"
              min={1}
              max={500}
              value={bindingsLimit}
              onChange={(event) => setBindingsLimit(Number(event.target.value))}
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                加载绑定
              </button>
            </div>
          </form>
        </article>
      </div>

      {error ? <p className="notice error">{error}</p> : null}
      {publishGateHint ? <p className="notice">{publishGateHint}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>认知结果</h3>
          <pre>{JSON.stringify(memoResult, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>最新策略结果</h3>
          <pre>{JSON.stringify(strategyResult, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>最新绑定结果</h3>
          <pre>{JSON.stringify(bindingResult, null, 2)}</pre>
        </article>
      </div>

      <article className="card">
        <h3>版本列表</h3>
        {versions.length === 0 ? (
          <p className="empty">暂无版本数据。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>策略ID</th>
                  <th>类型</th>
                  <th>版本</th>
                  <th>状态</th>
                  <th>回测任务</th>
                </tr>
              </thead>
              <tbody>
                {versions.map((item) => (
                  <tr key={item.strategy_id}>
                    <td>{item.strategy_id}</td>
                    <td>{item.strategy_type}</td>
                    <td>{item.version}</td>
                    <td>{item.status}</td>
                    <td>{item.backtest_job_id ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      <article className="card">
        <h3>绑定列表</h3>
        {bindings.length === 0 ? (
          <p className="empty">暂无绑定数据。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>绑定ID</th>
                  <th>策略ID</th>
                  <th>流程ID</th>
                  <th>状态</th>
                  <th>锁定模式</th>
                </tr>
              </thead>
              <tbody>
                {bindings.map((item) => (
                  <tr key={item.binding_id}>
                    <td>{item.binding_id}</td>
                    <td>{item.strategy_id}</td>
                    <td>{item.flow_id}</td>
                    <td>{item.status}</td>
                    <td>{item.prompt_lock_mode ?? "-"}</td>
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
