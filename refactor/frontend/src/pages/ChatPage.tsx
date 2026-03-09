import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import { createChatSession, listChatMessages, postChatMessage } from "../lib/services/chat";
import type { ChatMessage, ChatSession } from "../lib/types";

type InsightFilter = "all" | "news" | "credit" | "market" | "macro" | "sentiment";

const INSIGHT_FILTER_OPTIONS: Array<{ value: InsightFilter; label: string }> = [
  { value: "all", label: "全部洞察" },
  { value: "news", label: "新闻" },
  { value: "credit", label: "信用" },
  { value: "market", label: "技术" },
  { value: "macro", label: "宏观" },
  { value: "sentiment", label: "情绪" },
];

export function ChatPage() {
  const [userId, setUserId] = useState("");
  const [memoryPolicy, setMemoryPolicy] = useState("summary_v1");
  const [session, setSession] = useState<ChatSession | null>(null);
  const [message, setMessage] = useState("");
  const [newsSymbol, setNewsSymbol] = useState("");
  const [newsQuery, setNewsQuery] = useState("");
  const [newsTopK, setNewsTopK] = useState("5");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [insightFilter, setInsightFilter] = useState<InsightFilter>("all");

  async function handleCreateSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const normalizedUserId = userId.trim();
    if (!normalizedUserId) {
      setError("用户ID不能为空。");
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await createChatSession({
        user_id: normalizedUserId,
        memory_policy: memoryPolicy.trim() || "summary_v1",
      });
      setSession(created);
      setMessages([]);
      setNotice(`会话已创建: ${created.session_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoadMessages() {
    if (!session) {
      setError("请先创建会话。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const response = await listChatMessages(session.session_id);
      setMessages(response.messages);
      setNotice(`已加载 ${response.messages.length} 条消息。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      setError("请先创建会话。");
      return;
    }
    const content = message.trim();
    if (!content) {
      setError("消息内容不能为空。");
      return;
    }

    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const composedContent = buildComposedMessage({
        content,
        symbol: newsSymbol,
        query: newsQuery,
        topK: newsTopK,
      });
      await postChatMessage(session.session_id, { content: composedContent });
      setMessage("");
      await handleLoadMessages();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-panel">
      <h2>对话中心</h2>
      <p>创建会话并进行多轮问答，查看引用与工具调用轨迹，形成可复用的长期认知上下文。</p>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>会话管理</h3>
          <form className="form-grid" onSubmit={handleCreateSession}>
            <label htmlFor="chat-user-id">用户ID</label>
            <input
              id="chat-user-id"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="例如：qrh"
            />

            <label htmlFor="chat-memory-policy">记忆策略</label>
            <input
              id="chat-memory-policy"
              value={memoryPolicy}
              onChange={(event) => setMemoryPolicy(event.target.value)}
              placeholder="summary_v1"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                创建会话
              </button>
              <button type="button" onClick={handleLoadMessages} disabled={isSubmitting || !session}>
                加载消息
              </button>
            </div>
          </form>
          {session ? (
            <dl className="meta-list">
              <div>
                <dt>会话ID</dt>
                <dd>{session.session_id}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>{session.status}</dd>
              </div>
            </dl>
          ) : null}
        </article>

        <article className="card">
          <h3>消息发送</h3>
          <form className="form-grid" onSubmit={handleSendMessage}>
            <div className="hint-grid">
              <label htmlFor="chat-news-symbol">股票代码</label>
              <input
                id="chat-news-symbol"
                value={newsSymbol}
                onChange={(event) => setNewsSymbol(event.target.value)}
                placeholder="例如：600519"
                disabled={!session}
              />

              <label htmlFor="chat-news-query">新闻关键词</label>
              <input
                id="chat-news-query"
                value={newsQuery}
                onChange={(event) => setNewsQuery(event.target.value)}
                placeholder="例如：政策、流动性"
                disabled={!session}
              />

              <label htmlFor="chat-news-top-k">新闻返回条数</label>
              <input
                id="chat-news-top-k"
                type="number"
                min={1}
                max={20}
                value={newsTopK}
                onChange={(event) => setNewsTopK(event.target.value)}
                placeholder="5"
                disabled={!session}
              />
            </div>
            <p className="hint-note">填写后会自动拼接 `news.search` 参数提示，便于 Agent 触发新闻检索工具。</p>
            <label htmlFor="chat-message">消息内容</label>
            <textarea
              id="chat-message"
              rows={6}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="请输入问题，例如：结合近期情绪与量价关系，给出明日观察计划。"
              disabled={!session}
            />
            <div className="action-row">
              <button type="submit" disabled={isSubmitting || !session}>
                发送消息
              </button>
            </div>
          </form>
        </article>
      </div>

      {error ? <p className="notice error">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <article className="card">
        <h3>消息记录</h3>
        <div className="insight-toolbar" role="group" aria-label="洞察筛选">
          {INSIGHT_FILTER_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`filter-chip${insightFilter === option.value ? " active" : ""}`}
              onClick={() => setInsightFilter(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
        {messages.length === 0 ? (
          <p className="empty">暂无消息记录。</p>
        ) : (
          <ul className="message-list">
            {messages.map((item) => {
              const newsInsight = extractNewsSearchInsight(item.tool_trace);
              const creditInsight = extractCreditSnapshotInsight(item.tool_trace);
              const marketInsight = extractMarketQuoteInsight(item.tool_trace);
              const macroInsight = extractMacroSnapshotInsight(item.tool_trace);
              const sentimentInsight = extractSentimentSnapshotInsight(item.tool_trace);
              const showNewsInsight = newsInsight !== null && isInsightVisible(insightFilter, "news");
              const showCreditInsight = creditInsight !== null && isInsightVisible(insightFilter, "credit");
              const showMarketInsight = marketInsight !== null && isInsightVisible(insightFilter, "market");
              const showMacroInsight = macroInsight !== null && isInsightVisible(insightFilter, "macro");
              const showSentimentInsight = sentimentInsight !== null && isInsightVisible(insightFilter, "sentiment");
              const visibleInsightCount = [
                showNewsInsight,
                showCreditInsight,
                showMarketInsight,
                showMacroInsight,
                showSentimentInsight,
              ].filter(Boolean).length;
              return (
                <li key={item.message_id}>
                  <header>
                    <strong>{item.role}</strong>
                    <span>{item.created_at}</span>
                  </header>
                  <p>{item.content}</p>
                  {visibleInsightCount > 0 ? (
                    <details className="insight-group" open>
                      <summary>结构化洞察（{visibleInsightCount}）</summary>
                      {showNewsInsight && newsInsight ? (
                        <section className="insight-panel">
                          <h4>新闻检索洞察</h4>
                          <p className="insight-meta">
                            代码：{newsInsight.symbol}
                            {newsInsight.query ? ` ｜关键词：${newsInsight.query}` : ""}
                            {typeof newsInsight.topK === "number" ? ` ｜条数：${newsInsight.topK}` : ""}
                          </p>
                          <p className="insight-meta">情绪级别：{newsInsight.sentimentLevel ?? "unknown"}</p>
                          {typeof newsInsight.sentimentScore === "number" ? (
                            <p className="insight-meta">情绪分值：{newsInsight.sentimentScore}</p>
                          ) : null}
                          {newsInsight.tags.length > 0 ? (
                            <p className="insight-meta">标签：{newsInsight.tags.join(" / ")}</p>
                          ) : null}
                          <ul className="insight-list">
                            {newsInsight.headlines.map((headline) => (
                              <li key={headline}>{headline}</li>
                            ))}
                          </ul>
                        </section>
                      ) : null}
                      {showCreditInsight && creditInsight ? (
                        <section className="insight-panel">
                          <h4>风险与信用洞察</h4>
                          <p className="insight-meta">
                            代码：{creditInsight.symbol}
                            {creditInsight.riskLevel ? ` ｜风险等级：${creditInsight.riskLevel}` : ""}
                          </p>
                          <p className="insight-meta">
                            {typeof creditInsight.cdsBps === "number" ? `CDS：${creditInsight.cdsBps} bps` : "CDS：N/A"}
                            {typeof creditInsight.bondSpreadBps === "number"
                              ? ` ｜债券利差：${creditInsight.bondSpreadBps} bps`
                              : " ｜债券利差：N/A"}
                          </p>
                          {creditInsight.qualityStatus ? (
                            <p className="insight-meta">标签：{creditInsight.qualityStatus}</p>
                          ) : null}
                        </section>
                      ) : null}
                      {showMarketInsight && marketInsight ? (
                        <section className="insight-panel">
                          <h4>行情技术洞察</h4>
                          <p className="insight-meta">代码：{marketInsight.symbol}</p>
                          {typeof marketInsight.trendScore === "number" ? (
                            <p className="insight-meta">趋势分：{marketInsight.trendScore}</p>
                          ) : null}
                          {marketInsight.maAlignment ? <p className="insight-meta">均线形态：{marketInsight.maAlignment}</p> : null}
                          <p className="insight-meta">
                            {typeof marketInsight.volumeRatio === "number" ? `量能比：${marketInsight.volumeRatio}` : "量能比：N/A"}
                            {typeof marketInsight.chipConcentration === "number"
                              ? ` ｜筹码集中度：${marketInsight.chipConcentration}`
                              : " ｜筹码集中度：N/A"}
                          </p>
                        </section>
                      ) : null}
                      {showMacroInsight && macroInsight ? (
                        <section className="insight-panel">
                          <h4>宏观洞察</h4>
                          <p className="insight-meta">代码：{macroInsight.symbol}</p>
                          <p className="insight-meta">
                            {typeof macroInsight.gdpGrowthPct === "number" ? `GDP：${macroInsight.gdpGrowthPct}%` : "GDP：N/A"}
                            {typeof macroInsight.unemploymentRatePct === "number"
                              ? ` ｜失业率：${macroInsight.unemploymentRatePct}%`
                              : " ｜失业率：N/A"}
                          </p>
                          <p className="insight-meta">
                            {typeof macroInsight.liquidityIndex === "number"
                              ? `流动性指数：${macroInsight.liquidityIndex}`
                              : "流动性指数：N/A"}
                          </p>
                        </section>
                      ) : null}
                      {showSentimentInsight && sentimentInsight ? (
                        <section className="insight-panel">
                          <h4>情绪洞察</h4>
                          <p className="insight-meta">
                            代码：{sentimentInsight.symbol}
                            {sentimentInsight.sentimentLevel ? ` ｜情绪级别：${sentimentInsight.sentimentLevel}` : ""}
                          </p>
                          <p className="insight-meta">
                            {typeof sentimentInsight.sentimentScore === "number"
                              ? `情绪分值：${sentimentInsight.sentimentScore}`
                              : "情绪分值：N/A"}
                            {typeof sentimentInsight.headlineCount === "number"
                              ? ` ｜样本条数：${sentimentInsight.headlineCount}`
                              : " ｜样本条数：N/A"}
                          </p>
                          {sentimentInsight.headlines.length > 0 ? (
                            <ul className="insight-list">
                              {sentimentInsight.headlines.map((headline) => (
                                <li key={headline}>{headline}</li>
                              ))}
                            </ul>
                          ) : null}
                        </section>
                      ) : null}
                    </details>
                  ) : null}
                  <details>
                    <summary>引用与调用轨迹</summary>
                    <pre>{JSON.stringify({ citations: item.citations, tool_trace: item.tool_trace }, null, 2)}</pre>
                  </details>
                </li>
              );
            })}
          </ul>
        )}
      </article>
    </section>
  );
}

type NewsSearchInsight = {
  symbol: string;
  query: string | null;
  topK: number | null;
  headlines: string[];
  sentimentLevel: string | null;
  sentimentScore: number | null;
  tags: string[];
};

type CreditSnapshotInsight = {
  symbol: string;
  riskLevel: string | null;
  cdsBps: number | null;
  bondSpreadBps: number | null;
  qualityStatus: string | null;
};

type MarketQuoteInsight = {
  symbol: string;
  trendScore: number | null;
  maAlignment: string | null;
  volumeRatio: number | null;
  chipConcentration: number | null;
};

type MacroSnapshotInsight = {
  symbol: string;
  gdpGrowthPct: number | null;
  unemploymentRatePct: number | null;
  liquidityIndex: number | null;
};

type SentimentSnapshotInsight = {
  symbol: string;
  sentimentLevel: string | null;
  sentimentScore: number | null;
  headlineCount: number | null;
  headlines: string[];
};

function buildComposedMessage(input: { content: string; symbol: string; query: string; topK: string }): string {
  const symbol = input.symbol.trim();
  const query = input.query.trim();
  const topKNumber = Number.parseInt(input.topK, 10);
  const normalizedTopK = Number.isFinite(topKNumber) ? Math.max(1, Math.min(topKNumber, 20)) : null;
  const hints: string[] = [];
  if (symbol) {
    hints.push(`symbol=${symbol}`);
  }
  if (query) {
    hints.push(`query=${query}`);
  }
  if (normalizedTopK !== null) {
    hints.push(`top_k=${normalizedTopK}`);
  }
  if (hints.length === 0) {
    return input.content;
  }
  return `${input.content}\n\n[news.search] ${hints.join(" ")}`.trim();
}

function extractNewsSearchInsight(toolTrace: unknown): NewsSearchInsight | null {
  const traceRecord = asRecord(toolTrace);
  const agentTrace = asRecord(traceRecord?.agent_trace);
  const results = asRecord(agentTrace?.results);
  const newsSearch = asRecord(results?.["news.search"]);
  if (!newsSearch) {
    return null;
  }

  const symbol = readOptionalString(newsSearch.symbol);
  if (!symbol) {
    return null;
  }
  const headlinesRaw = Array.isArray(newsSearch.headlines) ? newsSearch.headlines : [];
  const headlines = headlinesRaw
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
  if (headlines.length === 0) {
    return null;
  }

  const sentiment = asRecord(newsSearch.sentiment);
  const sentimentLevel = readOptionalString(sentiment?.sentiment_level);
  const sentimentScore = readOptionalNumber(sentiment?.sentiment_score);
  const riskTags = readOptionalStringArray(newsSearch.risk_tags);
  const qualityFlag = asRecord(newsSearch.quality_flag);
  const qualityStatus = readOptionalString(qualityFlag?.status);
  const tags = [sentimentLevel, ...riskTags, qualityStatus].filter((item): item is string => Boolean(item));
  const uniqueTags: string[] = [];
  for (const tag of tags) {
    if (!uniqueTags.includes(tag)) {
      uniqueTags.push(tag);
    }
  }

  return {
    symbol,
    query: readOptionalString(newsSearch.query),
    topK: readOptionalNumber(newsSearch.top_k),
    headlines,
    sentimentLevel,
    sentimentScore,
    tags: uniqueTags,
  };
}

function extractCreditSnapshotInsight(toolTrace: unknown): CreditSnapshotInsight | null {
  const traceRecord = asRecord(toolTrace);
  const agentTrace = asRecord(traceRecord?.agent_trace);
  const results = asRecord(agentTrace?.results);
  const creditSnapshot = asRecord(results?.["credit.snapshot"]);
  if (!creditSnapshot) {
    return null;
  }

  const credit = asRecord(creditSnapshot.credit);
  const symbol = readOptionalString(creditSnapshot.symbol);
  if (!symbol) {
    return null;
  }

  const qualityFlag = asRecord(creditSnapshot.quality_flag);
  return {
    symbol,
    riskLevel: readOptionalString(credit?.risk_level),
    cdsBps: readOptionalNumber(credit?.cds_bps),
    bondSpreadBps: readOptionalNumber(credit?.bond_spread_bps),
    qualityStatus: readOptionalString(qualityFlag?.status),
  };
}

function extractMarketQuoteInsight(toolTrace: unknown): MarketQuoteInsight | null {
  const traceRecord = asRecord(toolTrace);
  const agentTrace = asRecord(traceRecord?.agent_trace);
  const results = asRecord(agentTrace?.results);
  const marketQuote = asRecord(results?.["market.quote"]);
  if (!marketQuote) {
    return null;
  }

  const technical = asRecord(marketQuote.technical);
  const symbol = readOptionalString(marketQuote.symbol);
  if (!symbol) {
    return null;
  }

  return {
    symbol,
    trendScore: readOptionalNumber(technical?.trend_score),
    maAlignment: readOptionalString(technical?.ma_alignment),
    volumeRatio: readOptionalNumber(technical?.volume_ratio),
    chipConcentration: readOptionalNumber(technical?.chip_concentration),
  };
}

function extractMacroSnapshotInsight(toolTrace: unknown): MacroSnapshotInsight | null {
  const traceRecord = asRecord(toolTrace);
  const agentTrace = asRecord(traceRecord?.agent_trace);
  const results = asRecord(agentTrace?.results);
  const macroSnapshot = asRecord(results?.["macro.snapshot"]);
  if (!macroSnapshot) {
    return null;
  }

  const macro = asRecord(macroSnapshot.macro);
  const symbol = readOptionalString(macroSnapshot.symbol);
  if (!symbol) {
    return null;
  }

  return {
    symbol,
    gdpGrowthPct: readOptionalNumber(macro?.gdp_growth_pct),
    unemploymentRatePct: readOptionalNumber(macro?.unemployment_rate_pct),
    liquidityIndex: readOptionalNumber(macro?.liquidity_index),
  };
}

function extractSentimentSnapshotInsight(toolTrace: unknown): SentimentSnapshotInsight | null {
  const traceRecord = asRecord(toolTrace);
  const agentTrace = asRecord(traceRecord?.agent_trace);
  const results = asRecord(agentTrace?.results);
  const sentimentSnapshot = asRecord(results?.["sentiment.snapshot"]);
  if (!sentimentSnapshot) {
    return null;
  }

  const sentiment = asRecord(sentimentSnapshot.sentiment);
  const symbol = readOptionalString(sentimentSnapshot.symbol);
  if (!symbol) {
    return null;
  }

  const sentimentLevel = readOptionalString(sentiment?.sentiment_level);
  const sentimentScore = readOptionalNumber(sentiment?.sentiment_score);
  const headlineCount = readOptionalNumber(sentiment?.headline_count);
  const headlines = readOptionalStringArray(sentiment?.headlines);
  if (!sentimentLevel && sentimentScore === null && headlines.length === 0) {
    return null;
  }

  return {
    symbol,
    sentimentLevel,
    sentimentScore,
    headlineCount,
    headlines,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  return value as Record<string, unknown>;
}

function readOptionalString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function readOptionalNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

function readOptionalStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
}

function isInsightVisible(currentFilter: InsightFilter, insightType: Exclude<InsightFilter, "all">): boolean {
  return currentFilter === "all" || currentFilter === insightType;
}
