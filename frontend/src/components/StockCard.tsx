import { Card, Tag, Statistic } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

interface StockCardProps {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  onClick?: () => void
}

const StockCard = ({
  symbol,
  name,
  price,
  change,
  changePercent,
  onClick,
}: StockCardProps) => {
  const isUp = change >= 0

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ width: 240 }}
    >
      <div style={{ marginBottom: 8 }}>
        <Tag color="blue">{symbol}</Tag>
        <span style={{ marginLeft: 8, fontWeight: 'bold' }}>{name}</span>
      </div>

      <Statistic
        value={price}
        precision={2}
        valueStyle={{ color: isUp ? '#ef232a' : '#14b143' }}
        prefix={isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
        suffix="元"
      />

      <div style={{ marginTop: 8 }}>
        <Tag color={isUp ? 'red' : 'green'}>
          {isUp ? '+' : ''}{change.toFixed(2)} ({isUp ? '+' : ''}{changePercent.toFixed(2)}%)
        </Tag>
      </div>
    </Card>
  )
}

export default StockCard
