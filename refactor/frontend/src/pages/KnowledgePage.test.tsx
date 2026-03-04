import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgePage } from "./KnowledgePage";

function mockJsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 201,
    headers: { "Content-Type": "application/json" },
  });
}

describe("KnowledgePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows validation error when title or markdown is missing", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<KnowledgePage />);
    fireEvent.click(screen.getByRole("button", { name: /上传文档/i }));

    expect(screen.getByText(/标题和 Markdown 内容不能为空。/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("uploads markdown document to knowledge api", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse({
        doc_id: "doc-123",
        title: "Macro Notes",
        status: "UPLOADED",
        tags: ["macro"],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<KnowledgePage />);

    fireEvent.change(screen.getByLabelText(/标题/i), { target: { value: "Macro Notes" } });
    fireEvent.change(screen.getByLabelText(/Markdown 内容/i), { target: { value: "# Notes" } });
    fireEvent.change(screen.getByLabelText(/标签/i), { target: { value: "macro" } });

    fireEvent.click(screen.getByRole("button", { name: /上传文档/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/knowledge/documents/upload"),
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(screen.getByText(/文档上传成功: doc-123/i)).toBeInTheDocument();
  });
});
