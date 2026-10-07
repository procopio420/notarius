'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DocumentTextIcon,
  SparklesIcon,
  CheckCircleIcon,
  ClockIcon,
  UserIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { formatDateTime } from '@/lib/utils'

interface Activity {
  id: string
  type: 'document_created' | 'ai_generation' | 'signature_completed' | 'task_assigned' | 'deadline_warning'
  title: string
  description: string
  timestamp: Date
  user?: string
  status?: 'success' | 'warning' | 'error' | 'info'
}

interface RecentActivitiesProps {
  className?: string
}

export function RecentActivities({ className }: RecentActivitiesProps) {
  const activities: Activity[] = [
    {
      id: '1',
      type: 'ai_generation',
      title: 'Documento gerado via AI',
      description: 'Procuração pública de João Silva para Maria Oliveira',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      user: 'Maria Escrevente',
      status: 'success',
    },
    {
      id: '2',
      type: 'signature_completed',
      title: 'Assinatura concluída',
      description: 'Escritura de Compra e Venda - Protocolo 2024/001',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      user: 'Carlos Silva',
      status: 'success',
    },
    {
      id: '3',
      type: 'task_assigned',
      title: 'Tarefa atribuída',
      description: 'Revisar minuta v2.1 - Procuração Especial',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      user: 'João Escrevente',
      status: 'info',
    },
    {
      id: '4',
      type: 'deadline_warning',
      title: 'Prazo próximo',
      description: 'Assinatura pendente - Procuração Geral (vence em 2h)',
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      user: 'Ana Costa',
      status: 'warning',
    },
    {
      id: '5',
      type: 'document_created',
      title: 'Documento criado',
      description: 'Autenticação de Cópia - RG de Pedro Santos',
      timestamp: new Date(Date.now() - 60 * 60 * 1000),
      user: 'Maria Escrevente',
      status: 'success',
    },
  ]

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'ai_generation':
        return <SparklesIcon className="w-5 h-5 text-purple-500" />
      case 'signature_completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'task_assigned':
        return <UserIcon className="w-5 h-5 text-blue-500" />
      case 'deadline_warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
      case 'document_created':
        return <DocumentTextIcon className="w-5 h-5 text-gray-500" />
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusBadge = (status?: Activity['status']) => {
    switch (status) {
      case 'success':
        return <Badge variant="success" className="text-xs">Sucesso</Badge>
      case 'warning':
        return <Badge variant="warning" className="text-xs">Atenção</Badge>
      case 'error':
        return <Badge variant="destructive" className="text-xs">Erro</Badge>
      case 'info':
        return <Badge variant="info" className="text-xs">Info</Badge>
      default:
        return null
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Atividades Recentes</CardTitle>
        <Button variant="outline" size="sm">
          Ver todas
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex-shrink-0 mt-0.5">
                {getActivityIcon(activity.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {activity.title}
                  </h4>
                  {getStatusBadge(activity.status)}
                </div>
                
                <p className="text-sm text-gray-600 mt-1">
                  {activity.description}
                </p>
                
                <div className="flex items-center space-x-2 mt-2">
                  <span className="text-xs text-gray-500">
                    {formatDateTime(activity.timestamp)}
                  </span>
                  {activity.user && (
                    <>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">
                        por {activity.user}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
