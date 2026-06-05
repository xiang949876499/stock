import { Card, Tag, Typography } from 'antd'
import type { NewsItem } from '../types'
import { formatDateTime } from '../utils'

const { Paragraph } = Typography

interface NewsCardProps {
  news: NewsItem
  onClick?: () => void
}

const NewsCard = ({ news, onClick }: NewsCardProps) => {
  const sentimentColors: Record<string, string> = {
    positive: 'green',
    negative: 'red',
    neutral: 'blue',
  }

  const sentimentTexts: Record<string, string> = {
    positive: '利好',
    negative: '利空',
    neutral: '中性',
  }

  const importanceColors: Record<string, string> = {
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
  }

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ marginBottom: 16 }}
    >
      <div style={{ marginBottom: 8 }}>
        <Tag color={sentimentColors[news.sentiment]}>
          {sentimentTexts[news.sentiment]}
        </Tag>
        <Tag color={importanceColors[news.importance]}>
          {news.importance}
        </Tag>
        <Tag>{news.source}</Tag>
      </div>

      <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
        {news.title}
      </Paragraph>

      <div style={{ color: '#999', fontSize: 12 }}>
        {formatDateTime(news.publish_time)}
      </div>
    </Card>
  )
}

export default NewsCard
