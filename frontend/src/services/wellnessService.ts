/**
 * Wellness Context & Retention Service (Frontend)
 *
 * Sourced strictly from FastAPI endpoints:
 * - /api/v1/wellness-context
 * - /api/v1/users/me/emotional-data
 *
 * STRICT RULE: Frontend MUST NEVER infer or calculate risk levels itself.
 */
import { apiRequest } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import {
  MultimodalWellnessResponse,
  EmotionalDataDeletionResponse,
} from '../api/types';

export const wellnessService = {
  async getWellnessContext(
    conversationId?: string
  ): Promise<MultimodalWellnessResponse> {
    const url = conversationId
      ? `${ENDPOINTS.WELLNESS.CONTEXT}?conversation_id=${encodeURIComponent(conversationId)}`
      : ENDPOINTS.WELLNESS.CONTEXT;

    return await apiRequest<MultimodalWellnessResponse>(url, {
      method: 'GET',
    });
  },

  async deleteEmotionalData(): Promise<EmotionalDataDeletionResponse> {
    return await apiRequest<EmotionalDataDeletionResponse>(
      ENDPOINTS.USERS.EMOTIONAL_DATA,
      {
        method: 'DELETE',
      }
    );
  },

  async getExerciseVideos(exerciseName: string) {
    return await apiRequest<import('../api/types').ExerciseVideosResponse>(
      ENDPOINTS.WELLNESS.EXERCISE_VIDEOS(exerciseName),
      {
        method: 'GET',
      }
    );
  },
};
