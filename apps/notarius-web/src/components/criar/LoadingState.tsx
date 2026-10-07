import { Box, Typography, CircularProgress, Card, CardContent, LinearProgress } from '@mui/material'
import { AutoAwesome as SparklesIcon, Psychology as BrainIcon, Description as DocumentIcon, Person as PersonIcon } from '@mui/icons-material'
import { useState, useEffect } from 'react'

export function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0)
  
  const steps = [
    { icon: <BrainIcon />, text: "Analisando linguagem natural..." },
    { icon: <DocumentIcon />, text: "Identificando tipo de documento..." },
    { icon: <PersonIcon />, text: "Extraindo partes envolvidas..." },
    { icon: <SparklesIcon />, text: "Estruturando dados do processo..." }
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length)
    }, 1500)

    return () => clearInterval(interval)
  }, [steps.length])

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
      {/* Animated Icon */}
      <Box sx={{ mb: 2, position: 'relative' }}>
        <Box sx={{ 
          width: 80, 
          height: 80, 
          borderRadius: '50%', 
          bgcolor: 'primary.50', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          position: 'relative'
        }}>
          <SparklesIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <CircularProgress
            size={80}
            thickness={2}
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              color: 'primary.main',
              opacity: 0.3
            }}
          />
        </Box>
      </Box>

      {/* Main Title */}
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
        🤖 IA Analisando...
      </Typography>
      
      <Typography color="text.secondary" sx={{ maxWidth: '400px', mb: 3 }}>
        Nossa inteligência artificial está processando sua descrição e estruturando o processo automaticamente.
      </Typography>

      {/* Progress Steps */}
      <Card sx={{ maxWidth: '500px', width: '100%' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
            Processando...
          </Typography>
          
          <LinearProgress 
            variant="indeterminate" 
            sx={{ mb: 3, height: 6, borderRadius: 3 }}
          />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {steps.map((step, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 2,
                  p: 1,
                  borderRadius: 1,
                  bgcolor: index === currentStep ? 'primary.50' : 'transparent',
                  transition: 'background-color 0.3s'
                }}
              >
                <Box sx={{ 
                  color: index === currentStep ? 'primary.main' : 'text.disabled',
                  transition: 'color 0.3s'
                }}>
                  {step.icon}
                </Box>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: index === currentStep ? 'primary.main' : 'text.secondary',
                    fontWeight: index === currentStep ? 500 : 400,
                    transition: 'all 0.3s'
                  }}
                >
                  {step.text}
                </Typography>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Fun Fact */}
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
        💡 Isso normalmente leva apenas alguns segundos...
      </Typography>
    </Box>
  )
}

