/**
 * AI Service (Frontend)
 * 
 * Proxies messages to FastAPI /api/v1/ai/chat and manages conversation history.
 * Strictly never contacts LLMs directly from React Native and never fabricates mock AI answers.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import {
  AIChatRequest,
  AIChatResponse,
  ConversationRecord,
  PaginatedConversations,
  PaginatedMessages,
} from '../api/types';

export const aiService = {
  async sendMessage(request: AIChatRequest): Promise<AIChatResponse> {
    return await apiRequest<AIChatResponse>(
      ENDPOINTS.AI.CHAT,
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      45000
    ); // 45s timeout for LLM generation
  },

  async createConversation(title?: string): Promise<ConversationRecord> {
    return await apiRequest<ConversationRecord>(
      ENDPOINTS.CONVERSATIONS.CREATE,
      {
        method: 'POST',
        body: JSON.stringify({ title }),
      }
    );
  },

  async listConversations(limit = 20, offset = 0): Promise<PaginatedConversations> {
    return await apiRequest<PaginatedConversations>(
      `${ENDPOINTS.CONVERSATIONS.LIST}?limit=${limit}&offset=${offset}`,
      { method: 'GET' }
    );
  },

  async getMessages(conversationId: string, limit = 50, offset = 0): Promise<PaginatedMessages> {
    return await apiRequest<PaginatedMessages>(
      `${ENDPOINTS.CONVERSATIONS.MESSAGES(conversationId)}?limit=${limit}&offset=${offset}`,
      { method: 'GET' }
    );
  },

  async deleteConversation(conversationId: string): Promise<{ status: string }> {
    return await apiRequest<{ status: string }>(
      ENDPOINTS.CONVERSATIONS.DELETE(conversationId),
      { method: 'DELETE' }
    );
  },
};
