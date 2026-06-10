import { useEffect, useRef } from 'react'
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

const REFRESH_INTERVAL = 10000 // 10 秒刷新一次

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

  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // 初始加载
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

  // 运行中定时刷新
  useEffect(() => {
    if (running) {
      const refresh = async () => {
        await Promise.allSettled([
          fetchAccount(),
          fetchPositions(),
          fetchTrades(),
          fetchAnalysisLogs(),
        ])
      }
      timerRef.current = setInterval(refresh, REFRESH_INTERVAL)
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [running])

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

  // ── 持仓列 ──────────────────────────────────────────────────

  const positionColumns = [
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '持仓数量', dataIndex: 'volume', key: 'volume' },
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
      dataIndex: 'market_value',
      key: 'market_value',
      render: (val: number) => formatAmount(val || 0),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Tag color={pnl >= 0 ? 'green' : 'red'} icon={pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
          {pnl >= 0 ? '+' : ''}{pnl?.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '盈亏比例',
      dataIndex: 'pnl_pct',
      key: 'pnl_pct',
      render: (pct: number) => (
        <Tag color={pct >= 0 ? 'green' : 'red'}>
          {pct >= 0 ? '+' : ''}{(pct * 100)?.toFixed(2)}%
        </Tag>
      ),
    },
  ]

  // ── 交易记录列 ──────────────────────────────────────────────

  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val: string) => formatDateTime(val),
    },
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (val: number) => val?.toFixed(2),
    },
    { title: '数量', dataIndex: 'volume', key: 'volume' },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (val: number) => formatAmount(val),
    },
    {
      title: '手续费',
      dataIndex: 'commission',
      key: 'commission',
      render: (val: number) => val?.toFixed(2),
    },
    { title: '策略', dataIndex: 'strategy', key: 'strategy' },
    {
      title: '评分',
      dataIndex: 'signal_score',
      key: 'signal_score',
      render: (val: number) => val?.toFixed(0),
    },
  ]

  // ── 分析日志列 ──────────────────────────────────────────────

  const analysisLogColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val: string) => formatDateTime(val),
    },
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    { title: '策略', dataIndex: 'strategy', key: 'strategy' },
    {
      title: '评分',
      dataIndex: 'score',
      key: 'score',
      render: (val: number) => val?.toFixed(0),
    },
    {
      title: '信号',
      dataIndex: 'signal',
      key: 'signal',
      render: (signal: string) => {
        const colorMap: Record<string, string> = { buy: 'green', sell: 'red', hold: 'blue' }
        const textMap: Record<string, string> = { buy: '买入', sell: '卖出', hold: '持有' }
        return <Tag color={colorMap[signal] || 'default'}>{textMap[signal] || signal}</Tag>
      },
    },
    {
      title: '执行状态',
      dataIndex: 'action_taken',
      key: 'action_taken',
      render: (val: string) => {
        const colorMap: Record<string, string> = { executed: 'green', skipped: 'orange' }
        const textMap: Record<string, string> = { executed: '已执行', skipped: '已跳过' }
        return <Tag color={colorMap[val] || 'default'}>{textMap[val] || val}</Tag>
      },
    },
    { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true },
  ]

  // ── 统计数据 ────────────────────────────────────────────────

  const initialCapital = account?.initial_capital || 1000000
  const totalAssets = account?.total_assets || initialCapital
  const balance = account?.balance || 0
  const totalPnl = totalAssets - initialCapital
  const totalPnlPct = initialCapital > 0 ? totalPnl / initialCapital : 0
  const positionCount = positions.length

  // ── 标签页 ──────────────────────────────────────────────────

  const tabItems = [
    {
      key: 'positions',
      label: `持仓 (${positionCount})`,
      children: (
        <Table
          columns={positionColumns}
          dataSource={positions}
          rowKey="symbol"
          loading={loading}
          pagination={false}
          size="small"
        />
      ),
    },
    {
      key: 'trades',
      label: `交易记录 (${trades.length})`,
      children: (
        <Table
          columns={tradeColumns}
          dataSource={trades}
          rowKey="trade_id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
    {
      key: 'analysis',
      label: `分析日志 (${analysisLogs.length})`,
      children: (
        <Table
          columns={analysisLogColumns}
          dataSource={analysisLogs}
          rowKey="log_id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      ),
    },
  ]

  return (
    <div>
      <h2>
        模拟交易
        {running && <Tag color="green" style={{ marginLeft: 8 }}>运行中</Tag>}
      </h2>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card>
            <Statistic title="总资产" value={totalAssets} precision={2} suffix="元" />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="可用资金" value={balance} precision={2} suffix="元" />
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
            <Statistic title="持仓数量" value={positionCount} suffix="只" />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="初始资金" value={initialCapital} precision={0} suffix="元" />
          </Card>
        </Col>
      </Row>

      {/* 持仓概览 */}
      {positions.length > 0 && (
        <Card title="当前持仓" size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            {positions.map((p) => (
              <Tag key={p.symbol} color="blue" style={{ padding: '4px 12px' }}>
                {p.name || p.symbol} ({p.symbol}) × {p.volume}股
                {p.pnl !== null && p.pnl !== undefined && (
                  <span style={{ marginLeft: 8, color: p.pnl >= 0 ? '#3f8600' : '#cf1322' }}>
                    {p.pnl >= 0 ? '+' : ''}{p.pnl.toFixed(2)}
                  </span>
                )}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      {/* 控制栏 */}
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
          icon={<ThunderboltOutlined />}
          onClick={handleAnalyze}
          loading={loading}
        >
          手动分析
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
          loading={loading}
        >
          重置账户
        </Button>
      </Space>

      {/* 详情标签页 */}
      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

export default Trading
