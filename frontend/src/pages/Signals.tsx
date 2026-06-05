import { useEffect, useState } from 'react'
import { Table, Tag, Button, Space, message, Modal } from 'antd'
import { signalApi } from '../services/api'
import type { Signal } from '../types'

const Signals = () => {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(false)

  const fetchSignals = async () => {
    setLoading(true)
    try {
      const response = await signalApi.list()
      setSignals(response.data)
    } catch (error) {
      console.error('获取信号失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignals()
  }, [])

  const handleApprove = async (signalId: string) => {
    try {
      await signalApi.approve(signalId)
      message.success('审批成功')
      fetchSignals()
    } catch (error) {
      message.error('审批失败')
    }
  }

  const handleReject = async (signalId: string) => {
    Modal.confirm({
      title: '确认拒绝',
      content: '请输入拒绝原因',
      onOk: async () => {
        try {
          await signalApi.reject(signalId, '手动拒绝')
          message.success('已拒绝')
          fetchSignals()
        } catch (error) {
          message.error('拒绝失败')
        }
      },
    })
  }

  const columns = [
    {
      title: '信号ID',
      dataIndex: 'signal_id',
      key: 'signal_id',
      render: (id: string) => id.substring(0, 8) + '...',
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      render: (source: string) => (
        <Tag color="blue">{source}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          draft: 'default',
          approved: 'processing',
          published: 'success',
          rejected: 'error',
        }
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: '标的数量',
      key: 'targets_count',
      render: (_: any, record: Signal) => Object.keys(record.targets).length,
    },
    {
      title: '时间',
      dataIndex: 'as_of',
      key: 'as_of',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Signal) => (
        <Space>
          {record.status === 'draft' && (
            <>
              <Button type="link" onClick={() => handleApprove(record.signal_id)}>
                审批
              </Button>
              <Button type="link" danger onClick={() => handleReject(record.signal_id)}>
                拒绝
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2>信号管理</h2>

      <Table
        columns={columns}
        dataSource={signals}
        rowKey="signal_id"
        loading={loading}
      />
    </div>
  )
}

export default Signals
