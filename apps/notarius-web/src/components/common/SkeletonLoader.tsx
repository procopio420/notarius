'use client'

import { Card, CardContent, CardHeader, Box, Skeleton } from '@mui/material'

interface SkeletonLoaderProps {
  type?: 'card' | 'table' | 'list' | 'form'
  count?: number
}

export function SkeletonLoader({ type = 'card', count = 1 }: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return (
          <Card>
            <CardHeader>
              <Skeleton variant="text" width="75%" height={24} />
              <Skeleton variant="text" width="50%" height={20} />
            </CardHeader>
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Skeleton variant="text" height={20} />
                <Skeleton variant="text" width="83%" height={20} />
                <Skeleton variant="text" width="67%" height={20} />
              </Box>
            </CardContent>
          </Card>
        )

      case 'table':
        return (
          <Box sx={{ bgcolor: 'white', borderRadius: 1, boxShadow: 1, border: 1, borderColor: 'divider' }}>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Skeleton variant="text" width="25%" height={24} />
            </Box>
            <Box>
              {Array.from({ length: 5 }).map((_, i) => (
                <Box key={i} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2, borderBottom: i < 4 ? 1 : 0, borderColor: 'divider' }}>
                  <Skeleton variant="text" width={64} height={20} />
                  <Skeleton variant="text" width={128} height={20} />
                  <Skeleton variant="text" width={96} height={20} />
                  <Skeleton variant="text" width={80} height={20} />
                  <Skeleton variant="text" width={64} height={20} />
                </Box>
              ))}
            </Box>
          </Box>
        )

      case 'list':
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'white', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                <Skeleton variant="circular" width={40} height={40} />
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Skeleton variant="text" width="75%" height={20} />
                  <Skeleton variant="text" width="50%" height={16} />
                </Box>
              </Box>
            ))}
          </Box>
        )

      case 'form':
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Skeleton variant="text" width="25%" height={20} />
              <Skeleton variant="rectangular" height={40} />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Skeleton variant="text" width="33%" height={20} />
              <Skeleton variant="rectangular" height={40} />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Skeleton variant="text" width="20%" height={20} />
              <Skeleton variant="rectangular" height={96} />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Skeleton variant="rectangular" width={96} height={40} />
              <Skeleton variant="rectangular" width={96} height={40} />
            </Box>
          </Box>
        )

      default:
        return null
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: count }).map((_, i) => (
        <Box key={i}>
          {renderSkeleton()}
        </Box>
      ))}
    </Box>
  )
}
