import { Box, Typography, Button, Alert, Card, CardContent, Chip } from '@mui/material'
import { Warning as ExclamationTriangleIcon, Refresh as RefreshIcon, Edit as EditIcon, Help as HelpIcon } from '@mui/icons-material'

interface ErrorStateProps {
  error: string
  onRetry: () => void
}

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const suggestions = [
    "Verifique se a descrição contém informações suficientes",
    "Tente ser mais específico sobre as partes envolvidas",
    "Inclua CPFs, nomes completos e detalhes do processo",
    "Use linguagem clara e objetiva"
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
      {/* Error Icon */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ 
          width: 80, 
          height: 80, 
          borderRadius: '50%', 
          bgcolor: 'error.50', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          mb: 2
        }}>
          <ExclamationTriangleIcon sx={{ fontSize: 40, color: 'error.main' }} />
        </Box>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: 'error.main' }}>
          ⚠️ Erro na Análise
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: '500px', mb: 3 }}>
          Ops! Algo deu errado ao processar sua descrição. Vamos tentar resolver isso.
        </Typography>
      </Box>

      {/* Error Details */}
      <Alert 
        severity="error" 
        sx={{ 
          maxWidth: '600px', 
          width: '100%',
          '& .MuiAlert-message': {
            width: '100%'
          }
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
          Detalhes do erro:
        </Typography>
        <Typography variant="body2">
          {error}
        </Typography>
      </Alert>

      {/* Suggestions */}
      <Card sx={{ maxWidth: '600px', width: '100%', bgcolor: 'info.50' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, color: 'info.main', display: 'flex', alignItems: 'center', gap: 1 }}>
            <HelpIcon />
            💡 Dicas para melhorar sua descrição:
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {suggestions.map((suggestion, index) => (
              <Typography key={index} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Chip label={index + 1} size="small" color="info" sx={{ minWidth: 24, height: 20 }} />
                {suggestion}
              </Typography>
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Example */}
      <Card sx={{ maxWidth: '600px', width: '100%', bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
            📝 Exemplo de descrição completa:
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
            "Procuração para venda de imóvel. Outorgante: João da Silva, CPF 123.456.789-00, brasileiro, casado, engenheiro, portador do RG 12.345.678-9; Outorgado: Maria Souza, CPF 987.654.321-00, brasileira, solteira, advogada, portadora do RG 98.765.432-1. Imóvel localizado na Rua das Flores, 123, São Paulo/SP. Válida por 90 dias."
          </Typography>
        </CardContent>
      </Card>

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Button 
          onClick={onRetry} 
          variant="contained"
          startIcon={<RefreshIcon />}
          sx={{ 
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0, #1976d2)',
            }
          }}
        >
          🔄 Tentar Novamente
        </Button>
        <Button 
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => {
            // This would trigger the edit action from the parent
            window.location.reload()
          }}
        >
          ✏️ Editar Descrição
        </Button>
      </Box>
    </Box>
  )
}

