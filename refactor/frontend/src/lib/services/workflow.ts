import { getJson, postJson } from "../api";
import type { WorkflowCancelResponse, WorkflowExecution, WorkflowExecutionAccepted } from "../types";

export type StartWorkflowExecutionInput = {
  flow_id: string;
  input: Record<string, unknown>;
};

export async function startWorkflowExecution(input: StartWorkflowExecutionInput): Promise<WorkflowExecutionAccepted> {
  return postJson<WorkflowExecutionAccepted>("/workflows/executions", input);
}

export async function getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
  return getJson<WorkflowExecution>(`/workflows/executions/${executionId}`);
}

export async function cancelWorkflowExecution(executionId: string): Promise<WorkflowCancelResponse> {
  return postJson<WorkflowCancelResponse>(`/workflows/executions/${executionId}/cancel`);
}
