import { useEffect, useState } from 'react'
import { Table, Tag, Card, Row, Col, Statistic, Select, Space, Empty, Button, message } from 'antd'
import { ReloadOutlined, StarFilled } from '@ant-design/icons'
import { newsApi } from '../services/api'
import type { NewsItem } from '../types'

const { Option } = Select

// 热门股票列表
const HOT_STOCKS = [
  { code: '600519', name: '贵州茅台', market: 'A' },
  { code: '000858', name: '五粮液', market: 'A' },
  { code: '601318', name: '中国平安', market: 'A' },
  { code: '000333', name: '美的集团', market: 'A' },
  { code: '300750', name: '宁德时代', market: 'A' },
  { code: '002594', name: '比亚迪', market: 'A' },
  { code: '600036', name: '招商银行', market: 'A' },
  { code: '002230', name: '科大讯飞', market: 'A' },
  { code: '688981', name: '中芯国际', market: 'A' },
  { code: '300059', name: '东方财富', market: 'A' },
  { code: '002415', name: '海康威视', market: 'A' },
  { code: '600309', name: '万华化学', market: 'A' },
  { code: '00700', name: '腾讯控股', market: 'HK' },
  { code: '09988', name: '阿里巴巴', market: 'HK' },
  { code: '01810', name: '小米集团', market: 'HK' },
]

// 股票名称映射
const STOCK_NAMES: Record<string, string> = {
  '600519': '贵州茅台',
  '000858': '五粮液',
  '601318': '中国平安',
  '000333': '美的集团',
  '300750': '宁德时代',
  '002594': '比亚迪',
  '600036': '招商银行',
  '002230': '科大讯飞',
  '688981': '中芯国际',
  '300059': '东方财富',
  '002415': '海康威视',
  '600309': '万华化学',
  '000651': '格力电器',
  '601012': '隆基绿能',
  '600900': '长江电力',
  '601398': '工商银行',
  '000725': '京东方A',
  '002352': '顺丰控股',
  '002475': '立讯精密',
  '300015': '爱尔眼科',
  '600276': '恒瑞医药',
  '300760': '迈瑞医疗',
  '000538': '云南白药',
  '601688': '华泰证券',
  '600030': '中信证券',
  '00700': '腾讯控股',
  '09988': '阿里巴巴',
  '01810': '小米集团',
  '03690': '美团',
  '09999': '网易',
  '09618': '京东',
  '09888': '百度',
  '01024': '快手',
  '02020': '安踏体育',
  '01211': '比亚迪',
  '02318': '中国平安',
  '00941': '中国移动',
  '00388': '港交所',
}

// 模拟新闻数据
const MOCK_NEWS: NewsItem[] = [
  {
    id: '1',
    symbol: '600519',
    market: 'A',
    title: '贵州茅台2025年营收超预期，净利润同比增长15%',
    content: '贵州茅台发布2025年年报，全年实现营业收入1500亿元...',
    source: '东方财富',
    url: 'https://example.com/1',
    publish_time: '2026-06-08 10:30:00',
    sentiment: 'positive',
    importance: 'P0',
  },
  {
    id: '2',
    symbol: '600519',
    market: 'A',
    title: '机构集体上调茅台目标价，最高看到2500元',
    content: '多家券商发布研报，上调贵州茅台目标价...',
    source: '新浪财经',
    url: 'https://example.com/2',
    publish_time: '2026-06-08 09:15:00',
    sentiment: 'positive',
    importance: 'P1',
  },
  {
    id: '3',
    symbol: '600519',
    market: 'A',
    title: '白酒板块整体走强，茅台领涨',
    content: '今日白酒板块表现强势，多只个股涨停...',
    source: '同花顺',
    url: 'https://example.com/3',
    publish_time: '2026-06-07 15:30:00',
    sentiment: 'positive',
    importance: 'P2',
  },
  {
    id: '4',
    symbol: '600519',
    market: 'A',
    title: '茅台经销商库存压力增大，终端价格承压',
    content: '据市场调研，部分经销商库存较高...',
    source: '雪球',
    url: 'https://example.com/4',
    publish_time: '2026-06-07 11:20:00',
    sentiment: 'negative',
    importance: 'P1',
  },
  {
    id: '5',
    symbol: '600519',
    market: 'A',
    title: '茅台冰淇淋销量下滑，跨界策略受质疑',
    content: '茅台冰淇淋近期销量出现明显下滑...',
    source: '腾讯财经',
    url: 'https://example.com/5',
    publish_time: '2026-06-06 16:45:00',
    sentiment: 'negative',
    importance: 'P2',
  },
]

const News = () => {
  const [news, setNews] = useState<NewsItem[]>([])
  const [sentiment, setSentiment] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('600519')
  const [market, setMarket] = useState('A')
  const [watchlist, setWatchlist] = useState<string[]>([])

  // 加载自选股
  useEffect(() => {
    const saved = localStorage.getItem('watchlist')
    if (saved) {
      try {
        setWatchlist(JSON.parse(saved))
      } catch (e) {
        console.error('解析自选股失败:', e)
      }
    }
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      // 尝试从API获取
      const [newsRes, sentimentRes] = await Promise.all([
        newsApi.list(symbol, market, 7).catch(() => ({ data: [] })),
        newsApi.getSentiment(symbol, market, 30).catch(() => ({ data: null })),
      ])

      // 如果API返回空数据，使用模拟数据
      if (newsRes.data && newsRes.data.length > 0) {
        setNews(newsRes.data)
      } else {
        // 使用模拟数据
        setNews(MOCK_NEWS.filter(n => n.symbol === symbol))
      }

      if (sentimentRes.data) {
        setSentiment(sentimentRes.data)
      } else {
        // 模拟舆情数据
        setSentiment({
          sentiment: 'positive',
          score: 72,
          hotness: 156,
          positive_count: 8,
          negative_count: 3,
        })
      }
    } catch (error) {
      console.error('获取新闻失败:', error)
      // 使用模拟数据
      setNews(MOCK_NEWS.filter(n => n.symbol === symbol))
      setSentiment({
        sentiment: 'positive',
        score: 72,
        hotness: 156,
        positive_count: 8,
        negative_count: 3,
      })
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
      render: (title: string, record: NewsItem) => (
        <a href={record.url} target="_blank" rel="noopener noreferrer">
          {title}
        </a>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
    },
    {
      title: '情绪',
      dataIndex: 'sentiment',
      key: 'sentiment',
      width: 80,
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
      width: 80,
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
      width: 160,
    },
  ]

  // 获取股票名称
  const getStockName = (code: string) => {
    return STOCK_NAMES[code] || code
  }

  // 合并自选股和热门股票（自选股在前，去重）
  const getStockOptions = () => {
    const watchlistStocks = watchlist
      .filter(code => {
        // 根据市场筛选
        if (market === 'A') return !code.startsWith('0') || code.length === 6
        if (market === 'HK') return code.length === 5
        return true
      })
      .map(code => ({
        code,
        name: getStockName(code),
        market: code.length === 5 ? 'HK' : 'A',
        isWatchlist: true,
      }))

    const hotStocks = HOT_STOCKS
      .filter(s => s.market === market && !watchlist.includes(s.code))
      .map(s => ({ ...s, isWatchlist: false }))

    return [...watchlistStocks, ...hotStocks]
  }

  const stockOptions = getStockOptions()

  return (
    <div>
      <h2>新闻舆情</h2>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Select value={market} onChange={setMarket} style={{ width: 100 }}>
            <Option value="A">A股</Option>
            <Option value="HK">港股</Option>
          </Select>
          <Select
            value={symbol}
            onChange={setSymbol}
            style={{ width: 250 }}
            showSearch
            placeholder="选择股票"
            optionFilterProp="children"
          >
            {stockOptions.map(s => (
              <Option key={s.code} value={s.code}>
                <Space>
                  {s.isWatchlist && <StarFilled style={{ color: '#faad14' }} />}
                  <span>{s.name}</span>
                  <span style={{ color: '#999' }}>({s.code})</span>
                </Space>
              </Option>
            ))}
          </Select>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchNews}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </Card>

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
                value={`${sentiment.positive_count || sentiment.positive || 0}/${sentiment.negative_count || sentiment.negative || 0}`}
                valueStyle={{ color: (sentiment.positive_count || sentiment.positive || 0) > (sentiment.negative_count || sentiment.negative || 0) ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="新闻列表">
        {news.length > 0 ? (
          <Table
            columns={columns}
            dataSource={news}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty description="暂无新闻数据" />
        )}
      </Card>
    </div>
  )
}

export default News
