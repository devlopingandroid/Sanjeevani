/**
 * AI Service (Frontend)
 * 
 * Proxies messages to FastAPI /api/v1/ai/chat.
 * Strictly never contacts xAI directly from React Native and never fabricates mock AI answers.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { AIChatRequest, AIChatResponse } from '../api/types';

export const aiService = {
  async sendMessage(request: AIChatRequest): Promise<AIChatResponse> {
    return await apiRequest<AIChatResponse>(ENDPOINTS.AI.CHAT, {
      method: 'POST',
      body: JSON.stringify(request),
    }, 25000); // 25s timeout for LLM generation
  },
};
