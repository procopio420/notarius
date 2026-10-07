'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  DocumentTextIcon,
  ClipboardDocumentCheckIcon,
  ClockIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

interface StatsCardsProps {
  className?: string
}

export function StatsCards({ className }: StatsCardsProps) {
  const stats = [
    {
      title: 'Documentos Hoje',
      value: '24',
      change: '+12%',
      changeType: 'positive' as const,
      icon: DocumentTextIcon,
      color: 'blue',
    },
    {
      title: 'Assinaturas Pendentes',
      value: '8',
      change: '-3',
      changeType: 'negative' as const,
      icon: ClipboardDocumentCheckIcon,
      color: 'yellow',
    },
    {
      title: 'Gerações AI',
      value: '156',
      change: '+45%',
      changeType: 'positive' as const,
      icon: SparklesIcon,
      color: 'purple',
    },
    {
      title: 'Taxa de Aprovação',
      value: '94%',
      change: '+2%',
      changeType: 'positive' as const,
      icon: CheckCircleIcon,
      color: 'green',
    },
  ]

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'blue':
        return 'bg-blue-500 text-white'
      case 'yellow':
        return 'bg-yellow-500 text-white'
      case 'purple':
        return 'bg-purple-500 text-white'
      case 'green':
        return 'bg-green-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
      {stats.map((stat) => (
        <Card key={stat.title} className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              {stat.title}
            </CardTitle>
            <div className={`p-2 rounded-lg ${getColorClasses(stat.color)}`}>
              <stat.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
            <div className="flex items-center space-x-2 mt-1">
              <Badge
                variant={stat.changeType === 'positive' ? 'success' : 'destructive'}
                className="text-xs"
              >
                {stat.change}
              </Badge>
              <span className="text-xs text-gray-500">vs ontem</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
