import { deleteJson, getJson, postJson } from "../api";
import type {
  KnowledgeDocument,
  KnowledgeIngestResponse,
  KnowledgeOptimizeResponse,
  KnowledgeSearchChunksResponse,
  KnowledgeUploadResponse,
} from "../types";

export type UploadDocumentInput = {
  title: string;
  markdown: string;
  tags: string[];
};

export type SearchChunksInput = {
  query: string;
  top_k?: number;
  doc_id?: string;
};

function buildSearchQuery(input: SearchChunksInput): string {
  const params = new URLSearchParams();
  params.set("query", input.query);
  params.set("top_k", String(input.top_k ?? 5));
  if (input.doc_id) {
    params.set("doc_id", input.doc_id);
  }
  return params.toString();
}

export async function uploadKnowledgeDocument(input: UploadDocumentInput): Promise<KnowledgeUploadResponse> {
  return postJson<KnowledgeUploadResponse>("/knowledge/documents/upload", input);
}

export async function optimizeKnowledgeDocument(docId: string): Promise<KnowledgeOptimizeResponse> {
  return postJson<KnowledgeOptimizeResponse>(`/knowledge/documents/${docId}/optimize`);
}

export async function ingestKnowledgeDocument(docId: string): Promise<KnowledgeIngestResponse> {
  return postJson<KnowledgeIngestResponse>(`/knowledge/documents/${docId}/ingest`);
}

export async function getKnowledgeDocument(docId: string): Promise<KnowledgeDocument> {
  return getJson<KnowledgeDocument>(`/knowledge/documents/${docId}`);
}

export async function searchKnowledgeChunks(input: SearchChunksInput): Promise<KnowledgeSearchChunksResponse> {
  return getJson<KnowledgeSearchChunksResponse>(`/knowledge/chunks/search?${buildSearchQuery(input)}`);
}

export async function deleteKnowledgeDocument(docId: string): Promise<{ doc_id: string; deleted: boolean }> {
  return deleteJson<{ doc_id: string; deleted: boolean }>(`/knowledge/documents/${docId}`);
}
