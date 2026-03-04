import { FormEvent, useState } from "react";

import { toErrorMessage } from "../lib/error";
import {
  deleteKnowledgeDocument,
  getKnowledgeDocument,
  ingestKnowledgeDocument,
  optimizeKnowledgeDocument,
  searchKnowledgeChunks,
  uploadKnowledgeDocument,
} from "../lib/services/knowledge";
import type {
  KnowledgeChunkHit,
  KnowledgeDocument,
  KnowledgeIngestResponse,
  KnowledgeOptimizeResponse,
  KnowledgeUploadResponse,
} from "../lib/types";

export function KnowledgePage() {
  const [title, setTitle] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [tags, setTags] = useState("");
  const [docId, setDocId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchTopK, setSearchTopK] = useState(5);
  const [searchDocId, setSearchDocId] = useState("");

  const [uploadResult, setUploadResult] = useState<KnowledgeUploadResponse | null>(null);
  const [optimizeResult, setOptimizeResult] = useState<KnowledgeOptimizeResponse | null>(null);
  const [ingestResult, setIngestResult] = useState<KnowledgeIngestResponse | null>(null);
  const [documentResult, setDocumentResult] = useState<KnowledgeDocument | null>(null);
  const [searchHits, setSearchHits] = useState<KnowledgeChunkHit[]>([]);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");

    const normalizedTitle = title.trim();
    const normalizedMarkdown = markdown.trim();
    if (!normalizedTitle || !normalizedMarkdown) {
      setError("标题和 Markdown 内容不能为空。");
      return;
    }

    const parsedTags = tags
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    setIsSubmitting(true);
    try {
      const result = await uploadKnowledgeDocument({
        title: normalizedTitle,
        markdown: normalizedMarkdown,
        tags: parsedTags,
      });
      setUploadResult(result);
      setDocId(result.doc_id);
      setNotice(`文档上传成功: ${result.doc_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleOptimize() {
    if (!docId.trim()) {
      setError("文档ID不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await optimizeKnowledgeDocument(docId.trim());
      setOptimizeResult(result);
      setNotice(`文档优化完成: ${result.doc_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleIngest() {
    if (!docId.trim()) {
      setError("文档ID不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await ingestKnowledgeDocument(docId.trim());
      setIngestResult(result);
      setNotice(`已入库 ${result.chunk_count} 个分块。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGetDocument() {
    if (!docId.trim()) {
      setError("文档ID不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await getKnowledgeDocument(docId.trim());
      setDocumentResult(result);
      setNotice("已获取文档详情。");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteDocument() {
    if (!docId.trim()) {
      setError("文档ID不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await deleteKnowledgeDocument(docId.trim());
      if (result.deleted) {
        setDocumentResult(null);
        setIngestResult(null);
        setOptimizeResult(null);
        setSearchHits([]);
      }
      setNotice(`文档已删除: ${result.doc_id}`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query) {
      setError("检索问题不能为空。");
      return;
    }
    setError("");
    setNotice("");
    setIsSubmitting(true);
    try {
      const result = await searchKnowledgeChunks({
        query,
        top_k: searchTopK,
        doc_id: searchDocId.trim() || undefined,
      });
      setSearchHits(result.hits);
      setNotice(`检索返回 ${result.hits.length} 条结果。`);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-panel">
      <h2>知识库中心</h2>
      <p>上传 Markdown 文档，执行清洗、摘要和向量入库，并基于语义分块完成精准检索。</p>

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>文档上传</h3>
          <form className="form-grid" onSubmit={handleUpload}>
            <label htmlFor="knowledge-title">标题</label>
            <input
              id="knowledge-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="例如：宏观风险观察（2026Q1）"
            />

            <label htmlFor="knowledge-markdown">Markdown 内容</label>
            <textarea
              id="knowledge-markdown"
              rows={10}
              value={markdown}
              onChange={(event) => setMarkdown(event.target.value)}
              placeholder="# 今日复盘&#10;&#10;1. 市场结构..."
            />

            <label htmlFor="knowledge-tags">标签</label>
            <input
              id="knowledge-tags"
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              placeholder="宏观, 情绪, 风险"
            />

            <div className="action-row">
              <button type="submit" disabled={isSubmitting}>
                上传文档
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>文档操作</h3>
          <div className="form-grid">
            <label htmlFor="knowledge-doc-id">文档ID</label>
            <input
              id="knowledge-doc-id"
              value={docId}
              onChange={(event) => setDocId(event.target.value)}
              placeholder="doc_id"
            />

            <div className="action-row wrap">
              <button type="button" onClick={handleOptimize} disabled={isSubmitting}>
                清洗优化
              </button>
              <button type="button" onClick={handleIngest} disabled={isSubmitting}>
                入库向量化
              </button>
              <button type="button" onClick={handleGetDocument} disabled={isSubmitting}>
                查看详情
              </button>
              <button type="button" className="danger" onClick={handleDeleteDocument} disabled={isSubmitting}>
                删除文档
              </button>
            </div>
          </div>
        </article>
      </div>

      <article className="card">
        <h3>分块检索</h3>
        <form className="form-grid two-cols" onSubmit={handleSearch}>
          <div>
            <label htmlFor="knowledge-search-query">检索问题</label>
            <input
              id="knowledge-search-query"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="例如：文档中对最大回撤的控制建议是什么？"
            />
          </div>
          <div>
            <label htmlFor="knowledge-search-doc-id">文档ID过滤</label>
            <input
              id="knowledge-search-doc-id"
              value={searchDocId}
              onChange={(event) => setSearchDocId(event.target.value)}
              placeholder="可选"
            />
          </div>
          <div>
            <label htmlFor="knowledge-search-top-k">返回数量 Top K</label>
            <input
              id="knowledge-search-top-k"
              type="number"
              min={1}
              max={20}
              value={searchTopK}
              onChange={(event) => setSearchTopK(Number(event.target.value))}
            />
          </div>
          <div className="action-row">
            <button type="submit" disabled={isSubmitting}>
              开始检索
            </button>
          </div>
        </form>
      </article>

      {error ? <p className="notice error">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="stack-grid two-cols">
        <article className="card">
          <h3>最近上传结果</h3>
          <pre>{JSON.stringify(uploadResult, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>最近优化结果</h3>
          <pre>{JSON.stringify(optimizeResult, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>最近入库结果</h3>
          <pre>{JSON.stringify(ingestResult, null, 2)}</pre>
        </article>
        <article className="card">
          <h3>文档详情</h3>
          <pre>{JSON.stringify(documentResult, null, 2)}</pre>
        </article>
      </div>

      <article className="card">
        <h3>检索命中</h3>
        {searchHits.length === 0 ? (
          <p className="empty">暂无命中结果。</p>
        ) : (
          <ul className="chunk-list">
            {searchHits.map((hit) => (
              <li key={hit.chunk_id}>
                <header>
                  <strong>{hit.chunk_id}</strong>
                  <span>分数: {hit.score}</span>
                </header>
                <p>{hit.section_path}</p>
                {hit.summary ? <p>{hit.summary}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </article>
    </section>
  );
}
