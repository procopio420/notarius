import { Box, Typography, Card, CardContent, Chip } from '@mui/material'
import { AutoAwesome as SparklesIcon, Description as DocumentIcon, Person as PersonIcon, Schedule as ClockIcon } from '@mui/icons-material'

export function EmptyState() {
  const examples = [
    "Procuração para venda de imóvel. Outorgante: João Silva, CPF 123.456.789-00; Outorgado: Maria Souza, CPF 987.654.321-00. Imóvel em SP. Válida por 90 dias.",
    "Escritura de compra e venda do imóvel situado na Rua das Flores, 123, pelo valor de R$ 500.000,00",
    "Autenticar cópia do documento de identidade de Carlos Mendes, CPF 111.222.333-44"
  ]

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100%', 
      textAlign: 'center', 
      py: 4,
      gap: 3
    }}>
      {/* Main Icon and Title */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ 
          width: 80, 
          height: 80, 
          borderRadius: '50%', 
          bgcolor: 'primary.50', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          mb: 2
        }}>
          <SparklesIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        </Box>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
          🤖 IA Pronta para Analisar
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: '500px', mb: 3 }}>
          Descreva o processo desejado em linguagem natural e nossa IA irá estruturar automaticamente as partes, dados e checklist necessários.
        </Typography>
      </Box>

      {/* Features */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Chip 
          icon={<DocumentIcon />} 
          label="Identifica tipo de documento" 
          variant="outlined" 
          color="primary"
        />
        <Chip 
          icon={<PersonIcon />} 
          label="Extrai partes envolvidas" 
          variant="outlined" 
          color="success"
        />
        <Chip 
          icon={<ClockIcon />} 
          label="Detecta prazos e condições" 
          variant="outlined" 
          color="info"
        />
      </Box>

      {/* Example */}
      <Card sx={{ maxWidth: '600px', bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
            💡 Exemplo de comando:
          </Typography>
          <Typography variant="body2" sx={{ 
            fontStyle: 'italic', 
            color: 'text.secondary',
            p: 2,
            bgcolor: 'white',
            borderRadius: 1,
            border: 1,
            borderColor: 'divider'
          }}>
            "{examples[0]}"
          </Typography>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          ✨ Digite sua descrição no campo à esquerda e clique em <strong>"Analisar"</strong> para começar
        </Typography>
      </Box>
    </Box>
  )
}
