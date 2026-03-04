import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import { createChatSession, listChatMessages, postChatMessage } from "../lib/services/chat";
import type { ChatMessage, ChatSession } from "../lib/types";

export function ChatPage() {
  const [userId, setUserId] = useState("");
  const [memoryPolicy, setMemoryPolicy] = useState("summary_v1");
  const [session, setSession] = useState<ChatSession | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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
      await postChatMessage(session.session_id, { content });
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
        {messages.length === 0 ? (
          <p className="empty">暂无消息记录。</p>
        ) : (
          <ul className="message-list">
            {messages.map((item) => (
              <li key={item.message_id}>
                <header>
                  <strong>{item.role}</strong>
                  <span>{item.created_at}</span>
                </header>
                <p>{item.content}</p>
                <details>
                  <summary>引用与调用轨迹</summary>
                  <pre>{JSON.stringify({ citations: item.citations, tool_trace: item.tool_trace }, null, 2)}</pre>
                </details>
              </li>
            ))}
          </ul>
        )}
      </article>
    </section>
  );
}
