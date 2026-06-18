import { Card, Tag, Button, Space } from 'antd'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons'
import type { Signal } from '../types'
import { formatDateTime } from '../utils'

interface SignalCardProps {
  signal: Signal
  onApprove?: (signalId: string) => void
  onReject?: (signalId: string) => void
}

const SignalCard = ({ signal, onApprove, onReject }: SignalCardProps) => {
  const statusColors: Record<string, string> = {
    draft: 'default',
    approved: 'processing',
    published: 'success',
    rejected: 'error',
    consumed: 'warning',
    archived: 'default',
  }

  const statusTexts: Record<string, string> = {
    draft: '草稿',
    approved: '已审批',
    published: '已发布',
    rejected: '已拒绝',
    consumed: '已消费',
    archived: '已归档',
  }

  return (
    <Card
      title={`信号 ${signal.signal_id.substring(0, 8)}...`}
      extra={<Tag color={statusColors[signal.status]}>{statusTexts[signal.status]}</Tag>}
      style={{ marginBottom: 16 }}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <span>来源: </span>
          <Tag color="blue">{signal.source}</Tag>
        </div>

        <div>
          <span>时间: </span>
          <span>{formatDateTime(signal.as_of)}</span>
        </div>

        <div>
          <span>标的: </span>
          {Object.keys(signal.targets).map((symbol) => (
            <Tag key={symbol} color="orange">
              {symbol} {(signal.targets[symbol] * 100).toFixed(1)}%
            </Tag>
          ))}
        </div>

        {signal.status === 'draft' && (
          <Space>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => onApprove?.(signal.signal_id)}
            >
              审批
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              onClick={() => onReject?.(signal.signal_id)}
            >
              拒绝
            </Button>
          </Space>
        )}
      </Space>
    </Card>
  )
}

export default SignalCard
