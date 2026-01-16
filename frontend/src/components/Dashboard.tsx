import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { summariesApi, channelsApi, messagesApi } from '../api/client'

export default function Dashboard() {
  const [isGenerating, setIsGenerating] = useState(false)
  const queryClient = useQueryClient()

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['daily-summary'],
    queryFn: () => summariesApi.getDaily().then((res) => res.data),
  })

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list().then((res) => res.data),
  })

  const { data: messagesData } = useQuery({
    queryKey: ['messages', { limit: 5 }],
    queryFn: () => messagesApi.list({ limit: 5 }).then((res) => res.data),
  })

  const generateSummary = async () => {
    setIsGenerating(true)
    try {
      await summariesApi.generate()
      await queryClient.invalidateQueries({ queryKey: ['daily-summary'] })
    } catch (error) {
      alert('Failed to generate summary')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-blue-600">
                  {channels?.length || 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Channels
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-green-600">
                  {messagesData?.total || 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Messages
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-3xl font-bold text-purple-600">
                  {summary?.message_count || 0}
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    In Last Summary
                  </dt>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Summary */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Daily Summary</h3>
            <button
              onClick={generateSummary}
              disabled={isGenerating}
              className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating...' : 'Generate New'}
            </button>
          </div>

          {summaryLoading ? (
            <div className="text-gray-500">Loading summary...</div>
          ) : summary ? (
            <div>
              <div className="text-sm text-gray-500 mb-2">
                Generated {new Date(summary.generated_at).toLocaleString()}
              </div>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">{summary.content}</p>
              </div>
            </div>
          ) : (
            <div className="text-gray-500">
              No summary available yet. Add some channels and wait for messages to be collected,
              then generate your first summary.
            </div>
          )}
        </div>
      </div>

      {/* Recent Messages Preview */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Messages</h3>
          {messagesData?.messages && messagesData.messages.length > 0 ? (
            <div className="space-y-4">
              {messagesData.messages.map((message) => (
                <div key={message.id} className="border-l-4 border-blue-500 pl-4">
                  <div className="text-sm text-gray-900">
                    {message.translated_text || message.original_text}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(message.published_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500">No messages yet. Add channels to get started.</div>
          )}
        </div>
      </div>
    </div>
  )
}
