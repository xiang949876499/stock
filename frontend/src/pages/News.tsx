import { useEffect, useState } from 'react'
import { Table, Tag, Card, Row, Col, Statistic, Select, Space } from 'antd'
import { newsApi } from '../services/api'
import type { NewsItem } from '../types'

const { Option } = Select

const News = () => {
  const [news, setNews] = useState<NewsItem[]>([])
  const [sentiment, setSentiment] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('600519')
  const [market, setMarket] = useState('A')

  const fetchNews = async () => {
    setLoading(true)
    try {
      const [newsRes, sentimentRes] = await Promise.all([
        newsApi.list(symbol, market, 7),
        newsApi.getSentiment(symbol, market, 30),
      ])
      setNews(newsRes.data)
      setSentiment(sentimentRes.data)
    } catch (error) {
      console.error('获取新闻失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNews()
  }, [symbol, market])

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
    },
    {
      title: '情绪',
      dataIndex: 'sentiment',
      key: 'sentiment',
      render: (sentiment: string) => {
        const colorMap: Record<string, string> = {
          positive: 'green',
          negative: 'red',
          neutral: 'blue',
        }
        const labelMap: Record<string, string> = {
          positive: '利好',
          negative: '利空',
          neutral: '中性',
        }
        return <Tag color={colorMap[sentiment]}>{labelMap[sentiment]}</Tag>
      },
    },
    {
      title: '重要性',
      dataIndex: 'importance',
      key: 'importance',
      render: (importance: string) => (
        <Tag color={importance === 'P0' ? 'red' : importance === 'P1' ? 'orange' : 'blue'}>
          {importance}
        </Tag>
      ),
    },
    {
      title: '时间',
      dataIndex: 'publish_time',
      key: 'publish_time',
    },
  ]

  return (
    <div>
      <h2>新闻舆情</h2>

      <Space style={{ marginBottom: 16 }}>
        <Select value={market} onChange={setMarket} style={{ width: 100 }}>
          <Option value="A">A股</Option>
          <Option value="HK">港股</Option>
        </Select>
        <Select value={symbol} onChange={setSymbol} style={{ width: 150 }}>
          <Option value="600519">贵州茅台</Option>
          <Option value="000858">五粮液</Option>
          <Option value="601318">中国平安</Option>
        </Select>
      </Space>

      {sentiment && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="整体情绪"
                value={sentiment.sentiment === 'positive' ? '积极' : sentiment.sentiment === 'negative' ? '消极' : '中性'}
                valueStyle={{
                  color: sentiment.sentiment === 'positive' ? '#3f8600' : sentiment.sentiment === 'negative' ? '#cf1322' : '#1890ff',
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="情绪分数" value={sentiment.score} suffix="/100" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="热度" value={sentiment.hotness} suffix="条" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="利好/利空"
                value={`${sentiment.positive_count}/${sentiment.negative_count}`}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="新闻列表">
        <Table
          columns={columns}
          dataSource={news}
          rowKey="id"
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default News
