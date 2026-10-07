import { MainLayout } from '@/components/layout/main-layout'
import { AIChat } from '@/components/ai-assistant/ai-chat'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Box,
  Container,
} from '@mui/material'
import {
  AutoAwesome as SparklesIcon,
  Description as DocumentTextIcon,
  Schedule as ClockIcon,
  CheckCircle as CheckCircleIcon,
  Lightbulb as LightBulbIcon,
} from '@mui/icons-material'

export default function AIAssistantPage() {
  const examples = [
    "Fazer procuração pública de João Silva CPF 123.456.789-00 para Maria Oliveira CPF 987.654.321-00, com poderes gerais",
    "Escritura de compra e venda do imóvel situado na Rua das Flores, 123, pelo valor de R$ 500.000,00",
    "Autenticar cópia do documento de identidade de Carlos Mendes, CPF 111.222.333-44",
    "Reconhecer firma de Ana Santos, brasileira, casada, advogada, portadora do RG 12.345.678-9",
    "Testamento público de Pedro Costa, solteiro, engenheiro, residente na Av. Paulista, 1000",
  ]

  const features = [
    {
      icon: SparklesIcon,
      title: "Geração Inteligente",
      description: "Cria documentos completos a partir de comandos em linguagem natural",
    },
    {
      icon: DocumentTextIcon,
      title: "Templates Dinâmicos",
      description: "Aplica templates predefinidos com substituição automática de variáveis",
    },
    {
      icon: CheckCircleIcon,
      title: "Validação Automática",
      description: "Verifica conformidade legal e sugere melhorias",
    },
    {
      icon: ClockIcon,
      title: "Processamento Rápido",
      description: "Gera documentos em segundos com alta precisão",
    },
  ]

  return (
    <MainLayout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Header */}
          <Box>
            <Typography variant="h3" component="h1" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <SparklesIcon sx={{ fontSize: 32, color: 'primary.main' }} />
              AI Assistant
            </Typography>
            <Typography color="text.secondary">
              Crie documentos notariais usando inteligência artificial e linguagem natural
            </Typography>
          </Box>

          {/* Main Content */}
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 3 }}>
            {/* AI Chat */}
            <Box sx={{ flex: 2 }}>
              <AIChat className="h-[700px]" />
            </Box>

            {/* Sidebar */}
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Features */}
                <Card>
                  <CardHeader>
                    <Typography variant="h6">Recursos do AI</Typography>
                  </CardHeader>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {features.map((feature, index) => (
                        <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                          <Box sx={{ flexShrink: 0, mt: 0.5 }}>
                            <feature.icon sx={{ fontSize: 20, color: 'primary.main' }} />
                          </Box>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {feature.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {feature.description}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>

                {/* Examples */}
                <Card>
                  <CardHeader>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LightBulbIcon sx={{ fontSize: 20, color: 'warning.main' }} />
                      Exemplos
                    </Typography>
                  </CardHeader>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {examples.map((example, index) => (
                        <Box
                          key={index}
                          sx={{
                            p: 2,
                            bgcolor: 'grey.50',
                            borderRadius: 1,
                            cursor: 'pointer',
                            '&:hover': {
                              bgcolor: 'grey.100'
                            },
                            transition: 'background-color 0.2s'
                          }}
                        >
                          <Typography variant="body2" color="text.secondary">
                            {example}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>

                {/* Stats */}
                <Card>
                  <CardHeader>
                    <Typography variant="h6">Estatísticas</Typography>
                  </CardHeader>
                  <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          Documentos gerados hoje
                        </Typography>
                        <Chip label="24" color="success" size="small" />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          Taxa de aprovação
                        </Typography>
                        <Chip label="94%" color="success" size="small" />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          Tempo médio
                        </Typography>
                        <Chip label="1.2s" color="info" size="small" />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          Confiança média
                        </Typography>
                        <Chip label="92%" color="success" size="small" />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          </Box>
        </Box>
      </Container>
    </MainLayout>
  )
}
