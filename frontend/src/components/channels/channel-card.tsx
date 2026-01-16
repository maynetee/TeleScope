import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { LanguageBadge } from '@/components/common/language-badge'
import { Timestamp } from '@/components/common/timestamp'
import { Badge } from '@/components/ui/badge'
import type { Channel } from '@/lib/api/client'
import { useTranslation } from 'react-i18next'
import type { Collection } from '@/lib/api/client'
import { ChannelCollectionPicker } from '@/components/channels/channel-collection-picker'

interface ChannelCardProps {
  channel: Channel
  collections?: Collection[]
  onView?: (id: string) => void
  onFetch?: (id: string, days: number) => void
  onDelete?: (id: string) => void
}

export function ChannelCard({ channel, collections = [], onView, onFetch, onDelete }: ChannelCardProps) {
  const { t } = useTranslation()
  const channelCollections = collections.filter((collection) =>
    collection.channel_ids.includes(channel.id),
  )

  return (
    <Card className="animate-rise-in">
      <CardContent className="flex flex-col gap-3 py-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold">{channel.username}</p>
            <p className="text-xs text-foreground/60">
              {channel.title} · {t('channels.subscribers', { count: channel.subscriber_count })}
            </p>
          </div>
          <LanguageBadge code={channel.detected_language} />
        </div>
        <p className="text-xs text-foreground/60">
          {t('channels.lastFetched')}{' '}
          {channel.last_fetched_at ? <Timestamp value={channel.last_fetched_at} /> : t('channels.never')}
        </p>
        {channelCollections.length ? (
          <div className="flex flex-wrap gap-2">
            {channelCollections.map((collection) => (
              <Badge key={collection.id} variant="outline">
                {collection.name}
              </Badge>
            ))}
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => onView?.(channel.id)}>
            {t('channels.viewMessages')}
          </Button>
          <ChannelCollectionPicker channelId={channel.id} collections={collections} />
          <Button variant="ghost" size="sm" onClick={() => onFetch?.(channel.id, 7)}>
            {t('channels.history7')}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onFetch?.(channel.id, 30)}>
            {t('channels.history30')}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete?.(channel.id)}>
            {t('channels.delete')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
