'use client';

import { Box, Card, CardContent, Typography, Table, TableHead, TableBody, TableRow, TableCell } from '@mui/material';
import { useTRELLISClusterMetrics } from '@/hooks/api/useTRELLIS';
import { MainLayout } from '@/components/layout/main-layout';

export default function TRELLISAdminPage() {
  const { data: metrics } = useTRELLISClusterMetrics();
  
  return (
    <MainLayout>
      <Typography variant="h4" gutterBottom>
        TRELLIS Cluster Prioritization
      </Typography>
      
      <Card>
        <CardContent>
          <Typography variant="h6">
            Top Priority Clusters (Oleve Formula: Volume × Negative Sentiment × Achievable Delta × Strategic Relevance)
          </Typography>
          
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Cluster</TableCell>
                <TableCell>Volume (30d)</TableCell>
                <TableCell>Success Rate</TableCell>
                <TableCell>Negative Sentiment</TableCell>
                <TableCell>Strategic Priority</TableCell>
                <TableCell>Priority Score</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {metrics?.top_priorities?.map((cluster) => (
                <TableRow key={cluster.cluster_id}>
                  <TableCell>{cluster.cluster_name}</TableCell>
                  <TableCell>{cluster.interactions_last_30_days}</TableCell>
                  <TableCell>{(cluster.success_rate * 100).toFixed(1)}%</TableCell>
                  <TableCell>{cluster.negative_sentiment_count}</TableCell>
                  <TableCell>{cluster.strategic_priority}/10</TableCell>
                  <TableCell>
                    <strong>{cluster.priority_score.toFixed(2)}</strong>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </MainLayout>
  );
}
