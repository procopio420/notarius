'use client'

import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Box,
} from '@mui/material'
import {
  Description as DocumentTextIcon,
  AssignmentTurnedIn as ClipboardDocumentCheckIcon,
  Schedule as ClockIcon,
  Visibility as EyeIcon,
} from '@mui/icons-material'

interface StatsCardsProps {
  stats?: {
    total_open_tasks: number
    total_pending: number
    total_in_progress: number
    total_overdue: number
  }
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Rascunho',
      value: stats?.total_pending || 0,
      icon: DocumentTextIcon,
      color: 'primary.main',
      bgColor: 'primary.50',
      description: 'Processos em rascunho'
    },
    {
      title: 'Análise',
      value: stats?.total_in_progress || 0,
      icon: EyeIcon,
      color: 'warning.main',
      bgColor: 'warning.50',
      description: 'Em análise'
    },
    {
      title: 'Checklist Pendente',
      value: stats?.total_overdue || 0,
      icon: ClipboardDocumentCheckIcon,
      color: 'error.main',
      bgColor: 'error.50',
      description: 'Aguardando checklist'
    },
    {
      title: 'OCR',
      value: 0, // This would come from document stats
      icon: ClockIcon,
      color: 'secondary.main',
      bgColor: 'secondary.50',
      description: 'Processando OCR'
    }
  ]

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: '1fr 1fr 1fr 1fr' }, gap: 3 }}>
      {cards.map((card, index) => (
        <Card key={index} sx={{ position: 'relative', overflow: 'hidden' }}>
          <CardHeader sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', pb: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              {card.title}
            </Typography>
            <Box sx={{ p: 1, borderRadius: 1, bgcolor: card.bgColor }}>
              <card.icon sx={{ fontSize: 20, color: card.color }} />
            </Box>
          </CardHeader>
          <CardContent>
            <Typography variant="h4" component="div" sx={{ fontWeight: 700, color: 'text.primary' }}>
              {card.value}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {card.description}
            </Typography>
            {card.value > 0 && (
              <Chip
                label={card.value > 5 ? 'Atenção' : 'Normal'}
                color={card.value > 5 ? 'error' : 'default'}
                size="small"
                sx={{ mt: 1 }}
              />
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  )
}
