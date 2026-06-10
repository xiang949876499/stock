import { useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  message,
  Modal,
  Tabs,
} from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useTradingStore } from '../stores/trading'
import { formatDateTime, formatAmount } from '../utils'

const Trading = () => {
  const {
    account,
    positions,
    trades,
    analysisLogs,
    running,
    loading,
    fetchAccount,
    fetchPositions,
    fetchTrades,
    fetchAnalysisLogs,
    startTrading,
    stopTrading,
    runAnalysis,
    resetAccount,
    fetchStatus,
  } = useTradingStore()

  useEffect(() => {
    const loadAll = async () => {
      await Promise.allSettled([
        fetchAccount(),
        fetchPositions(),
        fetchTrades(),
        fetchAnalysisLogs(),
        fetchStatus(),
      ])
    }
    loadAll()
  }, [])

  const handleToggleTrading = async () => {
    try {
      if (running) {
        await stopTrading()
        message.success('交易已停止')
      } else {
        await startTrading()
        message.success('交易已启动')
      }
    } catch (error: any) {
      message.error(`操作失败: ${error.message || '未知错误'}`)
    }
  }

  const handleAnalyze = async () => {
    try {
      message.loading('正在分析...', 0)
      await runAnalysis()
      message.destroy()
      message.success('分析完成')
    } catch (error: any) {
      message.destroy()
      message.error(`分析失败: ${error.message || '未知错误'}`)
    }
  }

  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      content: '重置将清空所有持仓和交易记录，确定要重置吗？',
      onOk: async () => {
        try {
          await resetAccount()
          message.success('账户已重置')
        } catch (error: any) {
          message.error(`重置失败: ${error.message || '未知错误'}`)
        }
      },
    })
  }

  const positionColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '成本价',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (val: number) => val?.toFixed(2),
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (val: number) => val?.toFixed(2),
    },
    {
      title: '市值',
      key: 'market_value',
      render: (_: any, record: any) =>
        formatAmount(record.quantity * record.current_price),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Tag color={pnl >= 0 ? 'green' : 'red'} icon={pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
          {pnl >= 0 ? '+' : ''}
          {pnl?.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '盈亏比例',
      dataIndex: 'pnl_pct',
      key: 'pnl_pct',
      render: (pct: number) => (
        <Tag color={pct >= 0 ? 'green' : 'red'}>
          {pct >= 0 ? '+' : ''}
          {(pct * 100)?.toFixed(2)}%
        </Tag>
      ),
    },
  ]

  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'executed_at',
      key: 'executed_at',
      render: (val: string) => formatDateTime(val),
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      render: (direction: string) => (
        <Tag color={direction === 'BUY' ? 'green' : 'red'}>
          {direction === 'BUY' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (val: number) => val?.toFixed(2),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (val: number) => formatAmount(val),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'executed' ? 'blue' : 'default'}>
          {status}
        </Tag>
      ),
    },
  ]

  const analysisLogColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val: string) => formatDateTime(val),
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (val: number) => `${(val * 100)?.toFixed(1)}%`,
    },
    {
      title: '决策',
      dataIndex: 'decision',
      key: 'decision',
      render: (decision: string) => {
        const colorMap: Record<string, string> = {
          buy: 'green',
          sell: 'red',
          hold: 'blue',
        }
        const textMap: Record<string, string> = {
          buy: '买入',
          sell: '卖出',
          hold: '持有',
        }
        return <Tag color={colorMap[decision] || 'default'}>{textMap[decision] || decision}</Tag>
      },
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
  ]

  const totalAssets = account?.total_assets || 0
  const cash = account?.cash || 0
  const totalPnl = account?.total_pnl || 0
  const totalPnlPct = account?.total_pnl_pct || 0
  const positionCount = positions.length

  const tabItems = [
    {
      key: 'positions',
      label: '持仓',
      children: (
        <Table
          columns={positionColumns}
          dataSource={positions}
          rowKey="symbol"
          loading={loading}
          pagination={false}
        />
      ),
    },
    {
      key: 'trades',
      label: '交易记录',
      children: (
        <Table
          columns={tradeColumns}
          dataSource={trades}
          rowKey="trade_id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      ),
    },
    {
      key: 'analysis',
      label: '分析日志',
      children: (
        <Table
          columns={analysisLogColumns}
          dataSource={analysisLogs}
          rowKey="log_id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      ),
    },
  ]

  return (
    <div>
      <h2>模拟交易</h2>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="总资产"
              value={totalAssets}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="可用资金"
              value={cash}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="累计盈亏"
              value={totalPnl}
              precision={2}
              suffix="元"
              valueStyle={{ color: totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={totalPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="累计收益率"
              value={totalPnlPct * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: totalPnlPct >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={totalPnlPct >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="持仓数量" value={positionCount} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="状态"
              value={running ? '运行中' : '已停止'}
              valueStyle={{ color: running ? '#3f8600' : '#999' }}
            />
          </Card>
        </Col>
      </Row>

      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          onClick={handleToggleTrading}
          loading={loading}
        >
          {running ? '停止交易' : '启动交易'}
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
          loading={loading}
        >
          重置账户
        </Button>
        <Button
          icon={<ThunderboltOutlined />}
          onClick={handleAnalyze}
          loading={loading}
        >
          手动分析
        </Button>
      </Space>

      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

export default Trading
