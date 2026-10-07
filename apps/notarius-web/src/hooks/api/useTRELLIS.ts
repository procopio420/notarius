import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface TRELLISFeedback {
  interaction_id: string;
  accepted: boolean;
  edited: boolean;
  sentiment_score?: number;  // -1 to 1
  feedback_text?: string;
}

export const useTRELLISFeedback = () => {
  return useMutation({
    mutationFn: async (feedback: TRELLISFeedback) => {
      const response = await api.patch(
        `/api/v1/trellis/interactions/${feedback.interaction_id}/feedback/`,
        feedback
      );
      return response.data;
    },
  });
};

export const useTRELLISClusterMetrics = () => {
  return useQuery({
    queryKey: ['trellis', 'cluster-metrics'],
    queryFn: async () => {
      const response = await api.get('/api/v1/trellis/cluster-metrics/');
      return response.data;
    },
  });
};
