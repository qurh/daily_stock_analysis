import { ApiError, normalizeErrorMessage } from "./api";

export function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `HTTP ${error.status}: ${error.message}`;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return normalizeErrorMessage(error);
}
