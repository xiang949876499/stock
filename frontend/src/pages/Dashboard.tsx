import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Button, Space, List } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  StockOutlined,
  FundOutlined,
  StarOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { usePortfolioStore } from '../stores/portfolio'
import { useNavigate } from 'react-router-dom'
import { stockApi } from '../services/api'

interface WatchlistStock {
  symbol: string
  name: string
  market: string
}

const Dashboard = () => {
  const { positions, account, fetchPositions, fetchAccount } = usePortfolioStore()
  const navigate = useNavigate()
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchPositions()
    fetchAccount()
    loadWatchlist()
  }, [])

  const loadWatchlist = async () => {
    const saved = JSON.parse(localStorage.getItem('watchlist') || '[]')
    if (saved.length === 0) return

    setLoading(true)
    try {
      const stocks: WatchlistStock[] = []
      for (const symbol of saved.slice(0, 10)) {
        try {
          const res = await stockApi.get(symbol, 'A')
          stocks.push({
            symbol,
            name: res.data.name || symbol,
            market: 'A',
          })
        } catch {
          stocks.push({ symbol, name: symbol, market: 'A' })
        }
      }
      setWatchlist(stocks)
    } catch (error) {
      console.error('加载自选股失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeFromWatchlist = (symbol: string) => {
    const newList = watchlist.filter(s => s.symbol !== symbol)
    setWatchlist(newList)
    localStorage.setItem('watchlist', JSON.stringify(newList.map(s => s.symbol)))
  }

  const positionColumns = [
    {
      title: '股票',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '持仓',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '成本价',
      dataIndex: 'avg_price',
      key: 'avg_price',
      render: (price: number) => price?.toFixed(2),
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => price?.toFixed(2),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Tag color={pnl >= 0 ? 'green' : 'red'}>
          {pnl >= 0 ? '+' : ''}{pnl?.toFixed(2)}
        </Tag>
      ),
    },
  ]

  return (
    <div>
      <h2>
        <StockOutlined /> 工作台
      </h2>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="持仓市值"
              value={account?.balance || 0}
              precision={2}
              prefix={<FundOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={account?.pnl || 0}
              precision={2}
              prefix={account?.pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="元"
              valueStyle={{ color: account?.pnl >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="持仓数量"
              value={positions.length}
              prefix={<StockOutlined />}
              suffix="只"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card
            title={
              <Space>
                <StarOutlined style={{ color: '#faad14' }} />
                我的自选股
              </Space>
            }
            extra={
              <Button type="link" onClick={() => navigate('/stocks')}>
                查看全部
              </Button>
            }
          >
            {watchlist.length > 0 ? (
              <List
                dataSource={watchlist}
                loading={loading}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        size="small"
                        onClick={() => navigate(`/stocks/${item.symbol}`)}
                      >
                        详情
                      </Button>,
                      <Button
                        type="link"
                        size="small"
                        onClick={() => navigate(`/analysis?symbol=${item.symbol}`)}
                      >
                        分析
                      </Button>,
                      <Button
                        type="link"
                        size="small"
                        danger
                        onClick={() => removeFromWatchlist(item.symbol)}
                      >
                        移除
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <span>{item.name}</span>
                          <Tag color="blue">{item.symbol}</Tag>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                <p>暂无自选股</p>
                <Button type="link" onClick={() => navigate('/stocks')}>
                  去添加
                </Button>
              </div>
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="持仓列表"
            extra={<Button type="link" onClick={() => navigate('/portfolio')}>查看全部</Button>}
          >
            <Table
              columns={positionColumns}
              dataSource={positions.slice(0, 5)}
              rowKey="symbol"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="快捷操作">
            <Space size="large">
              <Button
                icon={<ThunderboltOutlined />}
                type="primary"
                onClick={() => navigate('/recommend')}
              >
                股票推荐
              </Button>
              <Button
                icon={<LineChartOutlined />}
                onClick={() => navigate('/analysis')}
              >
                AI 分析
              </Button>
              <Button
                icon={<StarOutlined />}
                onClick={() => navigate('/stocks')}
              >
                自选股管理
              </Button>
              <Button onClick={() => navigate('/news')}>
                新闻舆情
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
