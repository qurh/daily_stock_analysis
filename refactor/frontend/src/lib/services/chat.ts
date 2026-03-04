import { getJson, postJson } from "../api";
import type { ChatListMessagesResponse, ChatPostMessageResponse, ChatSession } from "../types";

export type CreateChatSessionInput = {
  user_id: string;
  memory_policy?: string;
};

export type PostChatMessageInput = {
  content: string;
};

export async function createChatSession(input: CreateChatSessionInput): Promise<ChatSession> {
  return postJson<ChatSession>("/chat/sessions", input);
}

export async function postChatMessage(sessionId: string, input: PostChatMessageInput): Promise<ChatPostMessageResponse> {
  return postJson<ChatPostMessageResponse>(`/chat/sessions/${sessionId}/messages`, input);
}

export async function listChatMessages(sessionId: string): Promise<ChatListMessagesResponse> {
  return getJson<ChatListMessagesResponse>(`/chat/sessions/${sessionId}/messages`);
}
