import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Statistic, Tag, Button, Descriptions, Spin, message, Space } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  StarOutlined,
  StarFilled,
  LineChartOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { stockApi } from '../services/api'
import StockChart from '../components/StockChart'

interface StockData {
  symbol: string
  name: string
  market: string
  industry: string
  price: number
  change: number
  changePercent: number
}

interface TechnicalData {
  ma5: number
  ma10: number
  ma20: number
  ma60: number
  macd: number
  macd_signal: number
  macd_hist: number
  kdj_k: number
  kdj_d: number
  kdj_j: number
  rsi_6: number
  rsi_12: number
  rsi_24: number
}

const StockDetail = () => {
  const { symbol } = useParams<{ symbol: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [stock, setStock] = useState<StockData | null>(null)
  const [kline, setKline] = useState<any[]>([])
  const [technical, setTechnical] = useState<TechnicalData | null>(null)
  const [isWatched, setIsWatched] = useState(false)

  useEffect(() => {
    if (symbol) {
      fetchStockData(symbol)
    }
  }, [symbol])

  const fetchStockData = async (sym: string) => {
    setLoading(true)
    try {
      // 获取股票信息
      const stockRes = await stockApi.get(sym, 'A')
      const stockData = stockRes.data as typeof stockRes.data & Partial<StockData>
      setStock({
        ...stockData,
        price: stockData.price ?? 0,
        change: stockData.change ?? 0,
        changePercent: stockData.changePercent ?? 0,
      })

      // 获取 K 线数据
      const klineRes = await stockApi.getKline(sym, 'A')
      setKline(klineRes.data || [])

      // 获取技术指标
      try {
        const techRes = await stockApi.getTechnical(sym, 'A')
        setTechnical(techRes.data)
      } catch {
        // 技术指标可能获取失败
      }

      // 检查是否在自选股
      const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]')
      setIsWatched(watchlist.includes(sym))
    } catch (error) {
      message.error('获取股票数据失败')
    } finally {
      setLoading(false)
    }
  }

  const toggleWatchlist = () => {
    if (!symbol) return

    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]')
    if (isWatched) {
      const newList = watchlist.filter((s: string) => s !== symbol)
      localStorage.setItem('watchlist', JSON.stringify(newList))
      setIsWatched(false)
      message.success('已从自选股移除')
    } else {
      watchlist.push(symbol)
      localStorage.setItem('watchlist', JSON.stringify(watchlist))
      setIsWatched(true)
      message.success('已添加到自选股')
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!stock) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <h2>股票不存在</h2>
        <Button onClick={() => navigate('/stocks')}>返回列表</Button>
      </div>
    )
  }

  const isUp = (stock.change || 0) >= 0

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={18}>
          <h2>
            {stock.name} ({stock.symbol})
            <Tag color="blue" style={{ marginLeft: 8 }}>{stock.market}</Tag>
            <Tag>{stock.industry}</Tag>
          </h2>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Space>
            <Button
              icon={isWatched ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={toggleWatchlist}
            >
              {isWatched ? '已关注' : '加自选'}
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={() => navigate(`/analysis?symbol=${symbol}`)}
            >
              AI 分析
            </Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="当前价格"
              value={stock.price || 0}
              precision={2}
              valueStyle={{ color: isUp ? '#ef232a' : '#14b143', fontSize: 28 }}
              prefix={isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="涨跌额"
              value={stock.change || 0}
              precision={2}
              valueStyle={{ color: isUp ? '#ef232a' : '#14b143' }}
              prefix={isUp ? '+' : ''}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="涨跌幅"
              value={stock.changePercent || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: isUp ? '#ef232a' : '#14b143' }}
              prefix={isUp ? '+' : ''}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="行业"
              value={stock.industry || '-'}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={16}>
          <Card title="K 线图">
            <StockChart data={kline} height={400} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="技术指标">
            {technical ? (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="MA5">{technical.ma5?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="MA10">{technical.ma10?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="MA20">{technical.ma20?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="MA60">{technical.ma60?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="MACD">
                  <Tag color={technical.macd > 0 ? 'green' : 'red'}>
                    {technical.macd?.toFixed(2)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="RSI(6)">
                  <Tag color={technical.rsi_6 > 70 ? 'red' : technical.rsi_6 < 30 ? 'green' : 'blue'}>
                    {technical.rsi_6?.toFixed(2)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="KDJ-K">{technical.kdj_k?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="KDJ-D">{technical.kdj_d?.toFixed(2)}</Descriptions.Item>
              </Descriptions>
            ) : (
              <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                技术指标加载中...
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="快速操作">
            <Space>
              <Button
                icon={<LineChartOutlined />}
                onClick={() => navigate(`/analysis?symbol=${symbol}`)}
              >
                综合分析
              </Button>
              <Button
                onClick={() => navigate(`/news?symbol=${symbol}`)}
              >
                相关新闻
              </Button>
              <Button
                onClick={() => navigate(`/recommend`)}
              >
                相似推荐
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default StockDetail
