import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

  it("sends composed message with news search hints", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          user_id: "user-a",
          memory_policy: "summary_v1",
          status: "ACTIVE",
          created_at: "2026-03-04T00:00:00Z",
          updated_at: "2026-03-04T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          assistant: {
            message_id: "m-1",
            session_id: "session-001",
            role: "assistant",
            content: "ok",
            citations: [],
            tool_trace: {},
            created_at: "2026-03-04T00:00:01Z",
          },
        }),
      )
      .mockResolvedValueOnce(mockJsonResponse({ session_id: "session-001", messages: [] }));
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));
    await waitFor(() => {
      expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/股票代码/i), { target: { value: "600519" } });
    fireEvent.change(screen.getByLabelText(/新闻关键词/i), { target: { value: "政策" } });
    fireEvent.change(screen.getByLabelText(/新闻返回条数/i), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText(/消息内容/i), { target: { value: "请做新闻检索" } });
    fireEvent.click(screen.getByRole("button", { name: /发送消息/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    const postMessageCall = fetchMock.mock.calls.find((call) => {
      const url = String(call[0]);
      const options = call[1] as RequestInit | undefined;
      return url.includes("/messages") && options?.method === "POST";
    });
    expect(postMessageCall).toBeTruthy();
    const requestBody = JSON.parse(String((postMessageCall?.[1] as RequestInit).body));
    expect(requestBody.content).toContain("请做新闻检索");
    expect(requestBody.content).toContain("symbol=600519");
    expect(requestBody.content).toContain("query=政策");
    expect(requestBody.content).toContain("top_k=3");
  });

  it("renders structured news insight when tool trace includes news.search", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          user_id: "user-a",
          memory_policy: "summary_v1",
          status: "ACTIVE",
          created_at: "2026-03-04T00:00:00Z",
          updated_at: "2026-03-04T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          messages: [
            {
              message_id: "m-2",
              session_id: "session-001",
              role: "assistant",
              content: "已完成新闻检索。",
              citations: [],
              tool_trace: {
                agent_trace: {
                  results: {
                    "news.search": {
                      symbol: "600519",
                      query: "政策",
                      top_k: 2,
                      headlines: ["政策支持延续", "流动性边际改善"],
                      risk_tags: ["policy", "liquidity"],
                      sentiment: {
                        sentiment_score: 0.31,
                        headline_count: 2,
                        sentiment_level: "positive",
                      },
                      quality_flag: {
                        source: "news",
                        status: "degraded",
                        reason: "external source failed",
                      },
                    },
                  },
                },
              },
              created_at: "2026-03-04T00:00:02Z",
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));
    await waitFor(() => {
      expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /加载消息/i }));
    await waitFor(() => {
      const insightTitle = screen.getByText(/新闻检索洞察/i);
      const panel = insightTitle.closest("section");
      expect(panel).toBeTruthy();
      const scoped = within(panel as HTMLElement);
      expect(scoped.getByText(/政策支持延续/i)).toBeInTheDocument();
      expect(scoped.getByText(/情绪级别：positive/i)).toBeInTheDocument();
      expect(scoped.getByText(/标签：positive \/ policy \/ liquidity \/ degraded/i)).toBeInTheDocument();
    });
  });

  it("renders structured credit risk insight when tool trace includes credit.snapshot", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          user_id: "user-a",
          memory_policy: "summary_v1",
          status: "ACTIVE",
          created_at: "2026-03-04T00:00:00Z",
          updated_at: "2026-03-04T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          messages: [
            {
              message_id: "m-3",
              session_id: "session-001",
              role: "assistant",
              content: "信用风险已提取。",
              citations: [],
              tool_trace: {
                agent_trace: {
                  results: {
                    "credit.snapshot": {
                      symbol: "600519",
                      report_type: "standard",
                      credit: {
                        cds_bps: 260,
                        bond_spread_bps: 275,
                        risk_level: "high",
                      },
                    },
                  },
                },
              },
              created_at: "2026-03-04T00:00:03Z",
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));
    await waitFor(() => {
      expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /加载消息/i }));
    await waitFor(() => {
      const insightTitle = screen.getByText(/风险与信用洞察/i);
      const panel = insightTitle.closest("section");
      expect(panel).toBeTruthy();
      const scoped = within(panel as HTMLElement);
      expect(scoped.getByText(/风险等级：high/i)).toBeInTheDocument();
      expect(scoped.getByText(/CDS：260 bps/i)).toBeInTheDocument();
      expect(scoped.getByText(/债券利差：275 bps/i)).toBeInTheDocument();
    });
  });

  it("renders structured market/macro/sentiment insights from tool trace", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          user_id: "user-a",
          memory_policy: "summary_v1",
          status: "ACTIVE",
          created_at: "2026-03-04T00:00:00Z",
          updated_at: "2026-03-04T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          messages: [
            {
              message_id: "m-4",
              session_id: "session-001",
              role: "assistant",
              content: "已完成多维度因子快照。",
              citations: [],
              tool_trace: {
                agent_trace: {
                  results: {
                    "market.quote": {
                      symbol: "600519",
                      report_type: "standard",
                      technical: {
                        trend_score: 0.42,
                        ma_alignment: "bullish",
                        volume_ratio: 1.18,
                        chip_concentration: 0.67,
                      },
                    },
                    "macro.snapshot": {
                      symbol: "600519",
                      report_type: "standard",
                      macro: {
                        gdp_growth_pct: 5.2,
                        unemployment_rate_pct: 4.1,
                        liquidity_index: 62.5,
                      },
                    },
                    "sentiment.snapshot": {
                      symbol: "600519",
                      report_type: "standard",
                      sentiment: {
                        sentiment_level: "positive",
                        sentiment_score: 0.36,
                        headline_count: 12,
                        headlines: ["消费复苏预期增强", "机构关注度上升"],
                      },
                    },
                  },
                },
              },
              created_at: "2026-03-04T00:00:04Z",
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));
    await waitFor(() => {
      expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /加载消息/i }));
    await waitFor(() => {
      const marketTitle = screen.getByText(/行情技术洞察/i);
      const marketPanel = marketTitle.closest("section");
      expect(marketPanel).toBeTruthy();
      const marketScoped = within(marketPanel as HTMLElement);
      expect(marketScoped.getByText(/趋势分：0.42/i)).toBeInTheDocument();
      expect(marketScoped.getByText(/均线形态：bullish/i)).toBeInTheDocument();

      const macroTitle = screen.getByText(/宏观洞察/i);
      const macroPanel = macroTitle.closest("section");
      expect(macroPanel).toBeTruthy();
      const macroScoped = within(macroPanel as HTMLElement);
      expect(macroScoped.getByText(/GDP：5.2%/i)).toBeInTheDocument();
      expect(macroScoped.getByText(/失业率：4.1%/i)).toBeInTheDocument();

      const sentimentTitle = screen.getByText(/情绪洞察/i);
      const sentimentPanel = sentimentTitle.closest("section");
      expect(sentimentPanel).toBeTruthy();
      const sentimentScoped = within(sentimentPanel as HTMLElement);
      expect(sentimentScoped.getByText(/情绪级别：positive/i)).toBeInTheDocument();
      expect(sentimentScoped.getByText(/样本条数：12/i)).toBeInTheDocument();
      expect(sentimentScoped.getByText(/消费复苏预期增强/i)).toBeInTheDocument();
    });
  });

  it("filters grouped insights by selected type", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          user_id: "user-a",
          memory_policy: "summary_v1",
          status: "ACTIVE",
          created_at: "2026-03-04T00:00:00Z",
          updated_at: "2026-03-04T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          session_id: "session-001",
          messages: [
            {
              message_id: "m-5",
              session_id: "session-001",
              role: "assistant",
              content: "完成多源因子洞察。",
              citations: [],
              tool_trace: {
                agent_trace: {
                  results: {
                    "news.search": {
                      symbol: "600519",
                      query: "政策",
                      top_k: 2,
                      headlines: ["政策支持延续", "流动性边际改善"],
                      sentiment: {
                        sentiment_score: 0.31,
                        headline_count: 2,
                        sentiment_level: "positive",
                      },
                    },
                    "macro.snapshot": {
                      symbol: "600519",
                      report_type: "standard",
                      macro: {
                        gdp_growth_pct: 5.2,
                        unemployment_rate_pct: 4.1,
                        liquidity_index: 62.5,
                      },
                    },
                  },
                },
              },
              created_at: "2026-03-04T00:00:05Z",
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatPage />);
    fireEvent.change(screen.getByLabelText(/用户ID/i), { target: { value: "user-a" } });
    fireEvent.click(screen.getByRole("button", { name: /创建会话/i }));
    await waitFor(() => {
      expect(screen.getByText(/会话已创建: session-001/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /加载消息/i }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /全部洞察/i })).toBeInTheDocument();
      expect(screen.getByText(/新闻检索洞察/i)).toBeInTheDocument();
      expect(screen.getByText(/宏观洞察/i)).toBeInTheDocument();
      expect(screen.getByText(/结构化洞察（2）/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /^新闻$/i }));
    await waitFor(() => {
      expect(screen.getByText(/新闻检索洞察/i)).toBeInTheDocument();
      expect(screen.queryByText(/宏观洞察/i)).not.toBeInTheDocument();
      expect(screen.getByText(/结构化洞察（1）/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /全部洞察/i }));
    await waitFor(() => {
      expect(screen.getByText(/宏观洞察/i)).toBeInTheDocument();
      expect(screen.getByText(/结构化洞察（2）/i)).toBeInTheDocument();
    });
  });
});
