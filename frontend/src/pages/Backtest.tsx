import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Select, DatePicker, Table, message } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'

const { RangePicker } = DatePicker
const { Option } = Select

interface BacktestResult {
  backtest_id: string
  strategy_name: string
  symbols: string[]
  start_date: string
  end_date: string
  initial_capital: number
  final_value: number
  total_return: number
  max_drawdown: number
  sharpe_ratio: number
}

const Backtest = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [strategies, setStrategies] = useState<string[]>([])
  const [results, setResults] = useState<BacktestResult[]>([])

  useEffect(() => {
    fetchStrategies()
  }, [])

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/backtest/strategies')
      const data = await response.json()
      setStrategies(data.map((s: any) => s.name))
    } catch (error) {
      console.error('获取策略列表失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const response = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: values.symbols.split(',').map((s: string) => s.trim()),
          strategy: values.strategy,
          start_date: values.dateRange[0].format('YYYY-MM-DD'),
          end_date: values.dateRange[1].format('YYYY-MM-DD'),
          initial_capital: values.initial_capital || 1000000,
        }),
      })

      const data = await response.json()
      if (data.status === 'completed') {
        message.success('回测完成')
        // 添加到结果列表
        setResults(prev => [{
          backtest_id: data.backtest_id,
          strategy_name: values.strategy,
          symbols: values.symbols.split(',').map((s: string) => s.trim()),
          start_date: values.dateRange[0].format('YYYY-MM-DD'),
          end_date: values.dateRange[1].format('YYYY-MM-DD'),
          initial_capital: values.initial_capital || 1000000,
          final_value: 0,
          total_return: 0,
          max_drawdown: 0,
          sharpe_ratio: 0,
        }, ...prev])
      } else {
        message.info(data.message)
      }
    } catch (error) {
      message.error('回测失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '回测ID', dataIndex: 'backtest_id', key: 'backtest_id', render: (id: string) => id.substring(0, 8) + '...' },
    { title: '策略', dataIndex: 'strategy_name', key: 'strategy_name' },
    { title: '股票', dataIndex: 'symbols', key: 'symbols', render: (symbols: string[]) => symbols.join(', ') },
    { title: '初始资金', dataIndex: 'initial_capital', key: 'initial_capital', render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '最终价值', dataIndex: 'final_value', key: 'final_value', render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '收益率', dataIndex: 'total_return', key: 'total_return', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '最大回撤', dataIndex: 'max_drawdown', key: 'max_drawdown', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio', render: (v: number) => v.toFixed(2) },
  ]

  return (
    <div>
      <h2>回测管理</h2>

      <Card title="创建回测" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="symbols" label="股票代码" rules={[{ required: true }]}>
            <Input placeholder="输入股票代码，多个用逗号分隔" />
          </Form.Item>

          <Form.Item name="strategy" label="策略" rules={[{ required: true }]}>
            <Select placeholder="选择策略">
              {strategies.map(s => (
                <Option key={s} value={s}>{s}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="dateRange" label="日期范围" rules={[{ required: true }]}>
            <RangePicker />
          </Form.Item>

          <Form.Item name="initial_capital" label="初始资金" initialValue={1000000}>
            <Input type="number" prefix="¥" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<PlayCircleOutlined />}>
              运行回测
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="回测结果">
        <Table columns={columns} dataSource={results} rowKey="backtest_id" />
      </Card>
    </div>
  )
}

export default Backtest
