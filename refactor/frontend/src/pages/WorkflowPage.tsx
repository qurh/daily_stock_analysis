import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import {
  cancelWorkflowExecution,
  getWorkflowExecution,
  startWorkflowExecution,
} from "../lib/services/workflow";
import type { WorkflowExecution } from "../lib/types";

function parseJsonObject(input: string): Record<string, unknown> {
  const parsed = JSON.parse(input);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("流程输入必须是 JSON 对象。");
  }
  return parsed as Record<string, unknown>;
}

export function WorkflowPage() {
  const [flowId, setFlowId] = useState("stock_analysis_v1");
  const [flowInput, setFlowInput] = useState('{"symbol":"000001.SZ","report_type":"detailed"}');
  const [executionId, setExecutionId] = useState("");
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function handleStartExecution(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");

    const normalizedFlowId = flowId.trim();
    if (!normalizedFlowId) {
      setError("flow_id 不能为空。");
      return;
    }

    let parsedInput: Record<string, unknown>;
    try {
      parsedInput = parseJsonObject(flowInput);
    } catch (err) {
      setError(toErrorMessage(err));
      return;
    }

    setIsSubmitting(true);
    try {
      const accepted = await startWorkflowExecution({
        flow_id: normalizedFlowId,
        input: parsedInput,
      });
      setExecutionId(accepted.execution_id);
      setNotice(`执行已启动: ${accepted.execution_id} (${accepted.status})`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleFetchExecution() {
    const id = executionId.trim();
    if (!id) {
      setError("execution_id 不能为空。");
      return;
    }

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const current = await getWorkflowExecution(id);
      setExecution(current);
      setNotice(`当前执行状态: ${current.status}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCancelExecution() {
    const id = executionId.trim();
    if (!id) {
      setError("execution_id 不能为空。");
      return;
    }

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const cancelled = await cancelWorkflowExecution(id);
      setNotice(`取消结果: ${cancelled.cancelled ? "已取消" : "当前状态不可取消"}`);
      await handleFetchExecution();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-panel">
      <h2>流程编排中心</h2>
      <p>启动分析流程、追踪节点执行细节，并在需要时中止运行中的任务。</p>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>启动执行</h3>
          <form className="form-grid" onSubmit={handleStartExecution}>
            <label htmlFor="workflow-flow-id">流程ID</label>
            <input
              id="workflow-flow-id"
              value={flowId}
              onChange={(event) => setFlowId(event.target.value)}
            />

            <label htmlFor="workflow-flow-input">流程输入 JSON</label>
            <textarea
              id="workflow-flow-input"
              rows={8}
              value={flowInput}
              onChange={(event) => setFlowInput(event.target.value)}
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                启动执行
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>执行操作</h3>
          <div className="form-grid">
            <label htmlFor="workflow-execution-id">执行ID</label>
            <input
              id="workflow-execution-id"
              value={executionId}
              onChange={(event) => setExecutionId(event.target.value)}
              placeholder="execution_id"
            />
            <div className="action-row wrap">
              <button type="button" onClick={handleFetchExecution} disabled={isSubmitting}>
                查询执行
              </button>
              <button type="button" className="danger" onClick={handleCancelExecution} disabled={isSubmitting}>
                取消执行
              </button>
            </div>
          </div>
        </article>
      </div>

      {error ? <p className="notice error">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <article className="card">
        <h3>执行载荷</h3>
        <pre>{JSON.stringify(execution, null, 2)}</pre>
      </article>

      <article className="card">
        <h3>追踪节点</h3>
        {!execution || execution.trace.nodes.length === 0 ? (
          <p className="empty">暂无节点追踪信息。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>节点</th>
                  <th>状态</th>
                  <th>重试次数</th>
                  <th>耗时(ms)</th>
                  <th>是否降级</th>
                  <th>失败码</th>
                </tr>
              </thead>
              <tbody>
                {execution.trace.nodes.map((node) => (
                  <tr key={`${node.node_id}-${node.started_at}`}>
                    <td>{node.node_id}</td>
                    <td>{node.status}</td>
                    <td>{node.attempts}</td>
                    <td>{node.duration_ms}</td>
                    <td>{String(node.degraded)}</td>
                    <td>{node.failure_code ?? "-"}</td>
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
