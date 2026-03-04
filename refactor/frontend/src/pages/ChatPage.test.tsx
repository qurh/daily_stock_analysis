import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChatPage } from "./ChatPage";

function mockJsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("ChatPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows validation error when user id is empty", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));

    expect(screen.getByText(/用户ID不能为空。/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("creates a chat session with user input", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse({
        session_id: "session-001",
        user_id: "user-a",
        memory_policy: "summary_v1",
        status: "ACTIVE",
        created_at: "2026-03-04T00:00:00Z",
        updated_at: "2026-03-04T00:00:00Z",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);

    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/chat/sessions"),
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
  });
});
