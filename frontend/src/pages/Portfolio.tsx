import { useEffect } from 'react'
import { Table, Card, Row, Col, Statistic, Tag } from 'antd'
import { usePortfolioStore } from '../stores/portfolio'

const Portfolio = () => {
  const { positions, account, fetchPositions, fetchAccount, loading } = usePortfolioStore()

  useEffect(() => {
    fetchPositions()
    fetchAccount()
  }, [])

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '市场',
      dataIndex: 'market',
      key: 'market',
      render: (market: string) => (
        <Tag color={market === 'A' ? 'blue' : 'green'}>
          {market === 'A' ? 'A股' : '港股'}
        </Tag>
      ),
    },
    {
      title: '持仓数量',
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
      <h2>持仓管理</h2>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总资产"
              value={account?.balance || 0}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="可用资金"
              value={account?.available || 0}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="冻结资金"
              value={account?.frozen || 0}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
      </Row>

      <Card title="持仓明细">
        <Table
          columns={columns}
          dataSource={positions}
          rowKey="symbol"
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default Portfolio
