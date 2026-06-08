import { useState } from 'react'
import { Card, Table, Tag, Button, Select, Space, InputNumber, Spin, message } from 'antd'
import { StarOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { recommendApi } from '../services/api'
import { useNavigate } from 'react-router-dom'

const { Option } = Select

interface RecommendStock {
  symbol: string
  name: string
  market: string
  technical_score: number
  ai_score: number | null
  signal: string | null
  trend: string | null
  reason: string | null
  combined_score: number
}

const Recommend = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [stocks, setStocks] = useState<RecommendStock[]>([])
  const [market, setMarket] = useState('A')
  const [topN, setTopN] = useState(10)
  const [withAnalysis, setWithAnalysis] = useState(false)

  const handleRecommend = async () => {
    setLoading(true)
    try {
      let response
      if (withAnalysis) {
        response = await recommendApi.analyze(market, topN)
      } else {
        response = await recommendApi.stocks(market, topN)
      }
      setStocks(response.data.stocks)
      message.success(`找到 ${response.data.count} 只推荐股票`)
    } catch (error) {
      message.error('推荐失败，请检查 AI 配置')
    } finally {
      setLoading(false)
    }
  }

  const getSignalColor = (signal: string | null) => {
    if (!signal) return 'default'
    switch (signal) {
      case 'buy': return 'green'
      case 'sell': return 'red'
      default: return 'blue'
    }
  }

  const getSignalText = (signal: string | null) => {
    if (!signal) return '-'
    switch (signal) {
      case 'buy': return '买入'
      case 'sell': return '卖出'
      default: return '持有'
    }
  }

  const getTrendColor = (trend: string | null) => {
    if (!trend) return 'default'
    switch (trend) {
      case 'bullish': return 'green'
      case 'bearish': return 'red'
      default: return 'blue'
    }
  }

  const getTrendText = (trend: string | null) => {
    if (!trend) return '-'
    switch (trend) {
      case 'bullish': return '看多'
      case 'bearish': return '看空'
      default: return '震荡'
    }
  }

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Button type="link" onClick={() => navigate(`/analysis?symbol=${symbol}`)}>
          {symbol}
        </Button>
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '技术评分',
      dataIndex: 'technical_score',
      key: 'technical_score',
      sorter: (a: RecommendStock, b: RecommendStock) => a.technical_score - b.technical_score,
      render: (score: number) => (
        <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'}>
          {score.toFixed(1)}
        </Tag>
      ),
    },
    {
      title: 'AI 评分',
      dataIndex: 'ai_score',
      key: 'ai_score',
      sorter: (a: RecommendStock, b: RecommendStock) => (a.ai_score || 0) - (b.ai_score || 0),
      render: (score: number | null) => {
        if (!score) return '-'
        return (
          <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'}>
            {score.toFixed(1)}
          </Tag>
        )
      },
    },
    {
      title: '综合评分',
      dataIndex: 'combined_score',
      key: 'combined_score',
      sorter: (a: RecommendStock, b: RecommendStock) => a.combined_score - b.combined_score,
      defaultSortOrder: 'descend' as const,
      render: (score: number) => (
        <Tag color={score >= 70 ? 'green' : score >= 50 ? 'orange' : 'red'} style={{ fontWeight: 'bold' }}>
          {score.toFixed(1)}
        </Tag>
      ),
    },
    {
      title: '信号',
      dataIndex: 'signal',
      key: 'signal',
      render: (signal: string | null) => (
        <Tag color={getSignalColor(signal)}>
          {getSignalText(signal)}
        </Tag>
      ),
    },
    {
      title: '趋势',
      dataIndex: 'trend',
      key: 'trend',
      render: (trend: string | null) => (
        <Tag color={getTrendColor(trend)}>
          {getTrendText(trend)}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: RecommendStock) => (
        <Space>
          <Button
            type="link"
            onClick={() => navigate(`/analysis?symbol=${record.symbol}`)}
          >
            详细分析
          </Button>
          <Button
            type="link"
            onClick={() => navigate(`/stocks?symbol=${record.symbol}`)}
          >
            查看行情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2>
        <StarOutlined /> 股票推荐
      </h2>

      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          <Select value={market} onChange={setMarket} style={{ width: 120 }}>
            <Option value="A">A股</Option>
            <Option value="HK">港股</Option>
          </Select>

          <InputNumber
            value={topN}
            onChange={(value) => setTopN(value || 10)}
            min={1}
            max={50}
            style={{ width: 120 }}
            placeholder="推荐数量"
          />

          <Select
            value={withAnalysis}
            onChange={setWithAnalysis}
            style={{ width: 180 }}
          >
            <Option value={false}>仅技术评分</Option>
            <Option value={true}>技术 + AI 分析</Option>
          </Select>

          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleRecommend}
            loading={loading}
          >
            开始推荐
          </Button>
        </Space>
      </Card>

      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={stocks}
            rowKey="symbol"
            pagination={false}
            scroll={{ x: 1000 }}
          />
        </Spin>
      </Card>
    </div>
  )
}

export default Recommend
