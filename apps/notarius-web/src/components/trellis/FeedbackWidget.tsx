'use client';

import { useState } from 'react';
import { Button, Box, TextField, Rating, Typography } from '@mui/material';
import { ThumbUp, ThumbDown } from '@mui/icons-material';
import { useTRELLISFeedback } from '@/hooks/api/useTRELLIS';

interface FeedbackWidgetProps {
  interactionId: string;
  onFeedbackSubmitted?: () => void;
}

export const TRELLISFeedbackWidget = ({ interactionId, onFeedbackSubmitted }: FeedbackWidgetProps) => {
  const [sentiment, setSentiment] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const feedbackMutation = useTRELLISFeedback();
  
  const handleFeedback = async (accepted: boolean) => {
    await feedbackMutation.mutateAsync({
      interaction_id: interactionId,
      accepted,
      edited: false, // Track this separately
      sentiment_score: sentiment,
      feedback_text: feedbackText,
    });
    
    onFeedbackSubmitted?.();
  };
  
  return (
    <Box sx={{ mt: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
      <Typography variant="body2" gutterBottom>
        O resultado foi útil?
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Button
          startIcon={<ThumbUp />}
          variant="outlined"
          onClick={() => handleFeedback(true)}
        >
          Sim
        </Button>
        <Button
          startIcon={<ThumbDown />}
          variant="outlined"
          onClick={() => handleFeedback(false)}
        >
          Não
        </Button>
      </Box>
      
      <Rating
        value={sentiment}
        onChange={(_, value) => setSentiment(value)}
        max={5}
      />
      
      <TextField
        fullWidth
        multiline
        rows={2}
        placeholder="Comentários adicionais (opcional)"
        value={feedbackText}
        onChange={(e) => setFeedbackText(e.target.value)}
        sx={{ mt: 1 }}
      />
    </Box>
  );
};
