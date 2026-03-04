import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StrategyPage } from "./StrategyPage";

function mockJsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("StrategyPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows publish gate hint when publish is blocked by backtest gate", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse(
        {
          detail: "STR-GATE-005: strategy did not pass backtest gate",
        },
        409,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<StrategyPage />);

    const publishIdInput = document.getElementById("strategy-publish-id");
    const publishBacktestInput = document.getElementById("strategy-publish-backtest-job-id");
    expect(publishIdInput).not.toBeNull();
    expect(publishBacktestInput).not.toBeNull();
    fireEvent.change(publishIdInput as HTMLElement, { target: { value: "strategy-123" } });
    fireEvent.change(publishBacktestInput as HTMLElement, { target: { value: "backtest-123" } });
    fireEvent.click(screen.getByRole("button", { name: /发布策略/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/strategy/strategy-123/publish"),
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(screen.getByText(/发布闸门提示:/i)).toBeInTheDocument();
    expect(screen.getByText(/sample_size >= 5/i)).toBeInTheDocument();
    expect(screen.getByText(/win_rate_pct >= 50/i)).toBeInTheDocument();
  });
});
