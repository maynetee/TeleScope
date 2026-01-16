import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KpiCard } from '@/components/stats/kpi-card'
import { TrendChart } from '@/components/stats/trend-chart'
import { ChannelRanking } from '@/components/stats/channel-ranking'
import { EmptyState } from '@/components/common/empty-state'
import { statsApi, channelsApi, collectionsApi } from '@/lib/api/client'

export function DashboardPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selectedCollection, setSelectedCollection] = useState<string>('all')

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })
  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const overviewQuery = useQuery({
    queryKey: ['stats-overview'],
    queryFn: async () => (await statsApi.overview()).data,
    enabled: (channelsQuery.data?.length ?? 0) > 0 && selectedCollection === 'all',
  })

  const messagesByDayQuery = useQuery({
    queryKey: ['stats-messages-by-day'],
    queryFn: async () => (await statsApi.messagesByDay(7)).data,
    enabled: (channelsQuery.data?.length ?? 0) > 0 && selectedCollection === 'all',
  })

  const messagesByChannelQuery = useQuery({
    queryKey: ['stats-messages-by-channel'],
    queryFn: async () => (await statsApi.messagesByChannel(5)).data,
    enabled: (channelsQuery.data?.length ?? 0) > 0 && selectedCollection === 'all',
  })

  const collectionStatsQuery = useQuery({
    queryKey: ['collections', selectedCollection, 'stats'],
    queryFn: async () => (await collectionsApi.stats(selectedCollection)).data,
    enabled: selectedCollection !== 'all',
  })

  const channels = channelsQuery.data ?? []
  const overview = overviewQuery.data
  const collectionStats = collectionStatsQuery.data
  const hasNoChannels = !channelsQuery.isLoading && channels.length === 0

  const digestItems = t('dashboard.digestItems', { returnObjects: true }) as string[]

  // Show empty state when no channels are configured
  if (hasNoChannels) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <EmptyState
          title={t('dashboard.emptyTitle')}
          description={t('dashboard.emptyDescription')}
          actionLabel={t('dashboard.emptyAction')}
          onAction={() => navigate('/channels?add=true')}
        />
      </div>
    )
  }

  const kpiMessages = selectedCollection === 'all'
    ? overview?.messages_last_24h ?? 0
    : collectionStats?.message_count_24h ?? 0
  const kpiDuplicates = selectedCollection === 'all'
    ? Math.round(
        ((overview?.duplicates_last_24h ?? 0) / ((overview?.messages_last_24h ?? 0) || 1)) * 100,
      )
    : Math.round((collectionStats?.duplicate_rate ?? 0) * 100)
  const kpiChannels = selectedCollection === 'all'
    ? overview?.active_channels ?? 0
    : collectionStats?.channel_count ?? 0

  const trendData = selectedCollection === 'all'
    ? messagesByDayQuery.data ?? []
    : collectionStats?.activity_trend ?? []

  const topChannels = selectedCollection === 'all'
    ? messagesByChannelQuery.data ?? []
    : (collectionStats?.top_channels ?? [])

  const collectionOptions = useMemo(
    () => collectionsQuery.data ?? [],
    [collectionsQuery.data],
  )

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant={selectedCollection === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedCollection('all')}
        >
          {t('collections.allCollections')}
        </Button>
        {collectionOptions.map((collection) => (
          <Button
            key={collection.id}
            variant={selectedCollection === collection.id ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setSelectedCollection(collection.id)}
          >
            {collection.name}
          </Button>
        ))}
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        <KpiCard
          label={t('dashboard.kpiMessages')}
          value={Number.isFinite(kpiMessages) ? kpiMessages.toLocaleString() : '--'}
          delta="+23%"
          trend="up"
        />
        <KpiCard
          label={t('dashboard.kpiDuplicates')}
          value={Number.isFinite(kpiDuplicates) ? `${kpiDuplicates}%` : '--'}
          delta="-4%"
          trend="down"
        />
        <KpiCard
          label={t('dashboard.kpiChannels')}
          value={Number.isFinite(kpiChannels) ? kpiChannels.toLocaleString() : '--'}
          delta="+11%"
          trend="up"
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="overflow-hidden">
          <CardHeader className="flex items-start justify-between gap-4 md:flex-row md:items-center">
            <div>
              <CardTitle>{t('dashboard.digestTitle')}</CardTitle>
              <p className="text-sm text-foreground/60">{t('dashboard.digestSubtitle')}</p>
            </div>
            <Button variant="outline">{t('dashboard.digestAction')}</Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {digestItems.map((item) => (
              <div key={item} className="flex items-start justify-between gap-4 rounded-lg bg-muted/40 p-4">
                <div>
                  <p className="text-sm font-semibold">{item}</p>
                  <p className="text-xs text-foreground/60">{t('dashboard.digestItemMeta')}</p>
                </div>
                <Badge variant="outline">{t('dashboard.digestSignal')}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.trustTitle')}</CardTitle>
            <p className="text-sm text-foreground/60">{t('dashboard.trustSubtitle')}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustPrimary')}</span>
              <span className="font-semibold">68%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustPropaganda')}</span>
              <span className="font-semibold text-warning">12%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>{t('dashboard.trustVerified')}</span>
              <span className="font-semibold">31</span>
            </div>
            <Button className="w-full" variant="secondary">
              {t('dashboard.trustAction')}
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.activityTitle')}</CardTitle>
            <p className="text-sm text-foreground/60">{t('dashboard.activitySubtitle')}</p>
          </CardHeader>
          <CardContent>
            <TrendChart data={trendData} />
          </CardContent>
        </Card>
        <ChannelRanking data={topChannels} />
      </section>
    </div>
  )
}
