'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api/client'
import { MetricCard } from '@/components/MetricCard'
import { PostsFeed } from '@/components/PostsFeed'
import { EngagementChart } from '@/components/EngagementChart'

export default function DashboardPage() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await api.get('/analytics/engagement?days=30')
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Here's your lead generation overview.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Posts Detected"
          value={analytics?.total_posts_detected || 0}
          change="+12%"
          trend="up"
        />
        <MetricCard
          title="Responses Generated"
          value={analytics?.responses_generated || 0}
          change="+8%"
          trend="up"
        />
        <MetricCard
          title="Responses Posted"
          value={analytics?.responses_posted || 0}
          change="+15%"
          trend="up"
        />
        <MetricCard
          title="Avg Quality Score"
          value={`${((analytics?.avg_quality_score || 0) * 100).toFixed(0)}%`}
          change="+5%"
          trend="up"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PostsFeed />
        </div>

        <div>
          <EngagementChart />
        </div>
      </div>
    </div>
  )
}
