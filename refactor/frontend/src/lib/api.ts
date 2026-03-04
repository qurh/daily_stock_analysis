const DEFAULT_API_BASE_URL = "http://localhost:18000/api/v2";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function resolveApiBaseUrl(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  if (!configured) {
    return DEFAULT_API_BASE_URL;
  }
  return configured.replace(/\/+$/, "");
}

export function normalizeErrorMessage(payload: unknown): string {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (typeof payload === "object" && payload !== null) {
    const detail = (payload as Record<string, unknown>).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (typeof detail === "object" && detail !== null) {
      const nestedMessage = (detail as Record<string, unknown>).message;
      if (typeof nestedMessage === "string" && nestedMessage.trim()) {
        return nestedMessage;
      }
    }
    const message = (payload as Record<string, unknown>).message;
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  return "Request failed.";
}

function buildHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

function maybeJsonBody(body: unknown): string | undefined {
  if (body === undefined) {
    return undefined;
  }
  return JSON.stringify(body);
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
    ...init,
    headers: buildHeaders(init),
  });

  const rawText = await response.text();
  let payload: unknown = {};
  if (rawText.trim()) {
    try {
      payload = JSON.parse(rawText);
    } catch {
      payload = rawText;
    }
  }

  if (!response.ok) {
    throw new ApiError(normalizeErrorMessage(payload), response.status, payload);
  }

  return payload as T;
}

export async function getJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, {
    method: "GET",
  });
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    body: maybeJsonBody(body),
  });
}

export async function deleteJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, {
    method: "DELETE",
  });
}
