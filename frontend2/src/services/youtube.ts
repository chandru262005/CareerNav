import apiClient from "./apiClient.ts";

export interface YouTubeVideo {
  title: string;
  url: string;
  channel: string;
  views?: string;
  duration?: string;
}

export interface YouTubeRecommendationsResponse {
  title: string;
  summary: string;
  youtube_resources: YouTubeVideo[];
  tips: string[];
}

export interface YouTubeRecommendationsRequest {
  current_skills: string[];
  target_job: string;
  timeframe_months: number;
  additional_context?: Record<string, unknown>;
}

export const getYouTubeRecommendations = async (
  payload: YouTubeRecommendationsRequest
): Promise<YouTubeRecommendationsResponse> => {
  try {
    const { data } = await apiClient.post<YouTubeRecommendationsResponse>(
      "/youtube/recommendations",
      payload
    );
    
    return data;
  } catch (error) {
    console.error('Error fetching YouTube recommendations:', error);
    throw error;
  }
};
