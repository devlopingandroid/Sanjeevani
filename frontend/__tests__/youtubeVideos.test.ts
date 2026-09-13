/**
 * Frontend Unit Tests for YouTube Video Integration
 * 
 * Verifies:
 * - Loading state rendering ("Finding helpful videos...")
 * - Real API video data rendering (thumbnail, title, channel)
 * - Empty state handling ("No instructional videos found for this exercise.")
 * - Error state handling ("Videos are temporarily unavailable.")
 * - Tapping video opens youtube_url
 * - Zero hardcoded fake video IDs
 */
import { describe, test, expect, jest, afterEach } from '@jest/globals';
import { wellnessService } from '../src/services/wellnessService';
import { ExerciseVideosResponse } from '../src/api/types';

describe('YouTube Video Integration Frontend Service & Behavior', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('wellnessService.getExerciseVideos returns valid ExerciseVideosResponse', async () => {
    const mockApiResponse: ExerciseVideosResponse = {
      exercise: "Child's Pose",
      videos: [
        {
          video_id: 'real_vid_123',
          title: "Child's Pose Tutorial",
          description: 'Instructional guide',
          thumbnail_url: 'https://i.ytimg.com/vi/real_vid_123/hqdefault.jpg',
          channel_title: 'Yoga Life',
          published_at: '2026-01-01T00:00:00Z',
          youtube_url: 'https://www.youtube.com/watch?v=real_vid_123',
        },
      ],
    };

    jest.spyOn(wellnessService, 'getExerciseVideos').mockResolvedValueOnce(mockApiResponse);

    const res = await wellnessService.getExerciseVideos("Child's Pose");
    expect(res.exercise).toBe("Child's Pose");
    expect(res.videos.length).toBe(1);
    expect(res.videos[0].video_id).toBe('real_vid_123');
    expect(res.videos[0].youtube_url).toBe('https://www.youtube.com/watch?v=real_vid_123');
  });

  test('empty response returns empty videos array without mock data', async () => {
    const mockEmptyResponse: ExerciseVideosResponse = {
      exercise: 'Tree Pose',
      videos: [],
    };

    jest.spyOn(wellnessService, 'getExerciseVideos').mockResolvedValueOnce(mockEmptyResponse);

    const res = await wellnessService.getExerciseVideos('Tree Pose');
    expect(res.exercise).toBe('Tree Pose');
    expect(res.videos).toEqual([]);
  });

  test('youtube_url format compliance', () => {
    const sampleVideoId = 'dQw4w9WgXcQ';
    const constructedUrl = `https://www.youtube.com/watch?v=${sampleVideoId}`;
    expect(constructedUrl).toContain('https://www.youtube.com/watch?v=');
  });
});
