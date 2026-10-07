'use client'

import { Button, Box, Typography } from '@mui/material'
import { 
  Help as QuestionMarkCircleIcon,
  Description as DocumentTextIcon,
  AssignmentTurnedIn as ClipboardDocumentCheckIcon,
  Security as ShieldCheckIcon,
  Schedule as ClockIcon,
  Settings as CogIcon
} from '@mui/icons-material'

interface FAQButtonsProps {
  onQuestionClick: (question: string) => void
}

const faqQuestions = [
  {
    icon: DocumentTextIcon,
    question: "Como criar uma procuração pública?",
    color: "primary"
  },
  {
    icon: ClipboardDocumentCheckIcon,
    question: "Quais documentos são necessários para autenticação?",
    color: "success"
  },
  {
    icon: ShieldCheckIcon,
    question: "Como funciona o processo de assinatura digital?",
    color: "secondary"
  },
  {
    icon: ClockIcon,
    question: "Qual o prazo para conclusão de um processo?",
    color: "warning"
  },
  {
    icon: QuestionMarkCircleIcon,
    question: "Como alterar dados de uma parte em um processo?",
    color: "info"
  },
  {
    icon: CogIcon,
    question: "Como configurar notificações automáticas?",
    color: "default"
  }
]

export function FAQButtons({ onQuestionClick }: FAQButtonsProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="h6" sx={{ fontWeight: 500, color: 'text.primary' }}>
        Perguntas Frequentes
      </Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
        {faqQuestions.map((faq, index) => (
          <Button
            key={index}
            variant="outlined"
            onClick={() => onQuestionClick(faq.question)}
            sx={{
              height: 'auto',
              p: 2,
              textAlign: 'left',
              justifyContent: 'flex-start',
              color: `${faq.color}.main`,
              borderColor: `${faq.color}.main`,
              bgcolor: `${faq.color}.50`,
              '&:hover': {
                bgcolor: `${faq.color}.100`,
                borderColor: `${faq.color}.main`,
              }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <faq.icon sx={{ fontSize: 20, mt: 0.5, flexShrink: 0 }} />
              <Typography variant="body2" sx={{ fontWeight: 500, lineHeight: 1.5 }}>
                {faq.question}
              </Typography>
            </Box>
          </Button>
        ))}
      </Box>
    </Box>
  )
}
