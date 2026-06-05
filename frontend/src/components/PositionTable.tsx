import { Table, Tag } from 'antd'
import type { Position } from '../types'

interface PositionTableProps {
  positions: Position[]
  loading?: boolean
}

const PositionTable = ({ positions, loading }: PositionTableProps) => {
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
    <Table
      columns={columns}
      dataSource={positions}
      rowKey="symbol"
      loading={loading}
      pagination={false}
    />
  )
}

export default PositionTable
