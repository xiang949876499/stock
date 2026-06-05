import { useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Tag } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  StockOutlined,
  FundOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { usePortfolioStore } from '../stores/portfolio'
import { useNavigate } from 'react-router-dom'

const Dashboard = () => {
  const { positions, account, fetchPositions, fetchAccount } = usePortfolioStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchPositions()
    fetchAccount()
  }, [])

  const columns = [
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
      render: (price: number) => price.toFixed(2),
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => price.toFixed(2),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Tag color={pnl >= 0 ? 'green' : 'red'}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
        </Tag>
      ),
    },
  ]

  return (
    <div>
      <h2>工作台</h2>

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

      <Card title="持仓列表" extra={<a onClick={() => navigate('/portfolio')}>查看全部</a>}>
        <Table
          columns={columns}
          dataSource={positions}
          rowKey="symbol"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}

export default Dashboard
