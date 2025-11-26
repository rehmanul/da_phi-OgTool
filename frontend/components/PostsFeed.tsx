'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api/client'
import { formatDistanceToNow } from 'date-fns'
import { ExternalLink, MessageSquare } from 'lucide-react'

export function PostsFeed() {
  const { data: posts, isLoading } = useQuery({
    queryKey: ['posts'],
    queryFn: async () => {
      const response = await api.get('/posts?status=pending&page_size=10')
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  if (isLoading) {
    return <div className="bg-white rounded-lg shadow p-6">Loading posts...</div>
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Recent Posts</h2>
      </div>

      <div className="divide-y divide-gray-200">
        {posts?.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            No posts detected yet. Configure keywords and monitors to get started.
          </div>
        ) : (
          posts?.map((post: any) => (
            <div key={post.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                      ${post.platform === 'reddit' ? 'bg-orange-100 text-orange-800' :
                        post.platform === 'linkedin' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'}`}>
                      {post.platform}
                    </span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                      ${post.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                        post.priority === 'high' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'}`}>
                      {post.priority}
                    </span>
                  </div>

                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    {post.title || 'Untitled'}
                  </h3>

                  <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                    {post.content}
                  </p>

                  <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                    <span>{post.author}</span>
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(post.detected_at), { addSuffix: true })}</span>
                    <span>•</span>
                    <span className="flex items-center">
                      <MessageSquare className="w-3 h-3 mr-1" />
                      {post.comment_count}
                    </span>
                  </div>
                </div>

                <div className="ml-4 flex flex-col space-y-2">
                  <a
                    href={post.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>

                  <button
                    className="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded"
                  >
                    Generate Response
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
