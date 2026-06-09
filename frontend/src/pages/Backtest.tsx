import { useState } from 'react'
import { Card, Form, Input, Button, Select, DatePicker, Table, message, Space } from 'antd'
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

// 内置策略列表
const STRATEGIES = [
  { name: 'comprehensive', label: '综合分析' },
  { name: 'ma_cross', label: '均线金叉' },
  { name: 'macd', label: 'MACD策略' },
  { name: 'trend', label: '趋势跟踪' },
  { name: 'wave', label: '波浪理论' },
  { name: 'chan', label: '缠论' },
  { name: 'news', label: '新闻事件' },
  { name: 'hot', label: '热点题材' },
  { name: 'growth', label: '成长质量' },
  { name: 'value', label: '价值投资' },
  { name: 'macd_trend_resonance', label: 'MACD趋势共振' },
  { name: 'macd_second_golden_cross', label: 'MACD二次金叉' },
  { name: 'tuige_shortline', label: '退哥短线' },
  { name: 'swing_defensive', label: '摆动防御' },
]

// 热门股票
const HOT_STOCKS = [
  { code: '600519', name: '贵州茅台' },
  { code: '000858', name: '五粮液' },
  { code: '601318', name: '中国平安' },
  { code: '000333', name: '美的集团' },
  { code: '300750', name: '宁德时代' },
  { code: '002594', name: '比亚迪' },
  { code: '600036', name: '招商银行' },
  { code: '002230', name: '科大讯飞' },
]

const Backtest = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<BacktestResult[]>([])

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      // 模拟回测结果（实际应调用后端 API）
      const mockResult: BacktestResult = {
        backtest_id: Date.now().toString(),
        strategy_name: values.strategy,
        symbols: values.symbols.split(',').map((s: string) => s.trim()),
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital || 1000000,
        final_value: 1050000 + Math.random() * 100000,
        total_return: 0.05 + Math.random() * 0.1,
        max_drawdown: 0.05 + Math.random() * 0.1,
        sharpe_ratio: 1.0 + Math.random() * 2,
      }

      setResults(prev => [mockResult, ...prev])
      message.success('回测完成')
    } catch (error) {
      message.error('回测失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '回测ID', dataIndex: 'backtest_id', key: 'backtest_id', width: 100, render: (id: string) => id.substring(0, 8) + '...' },
    { title: '策略', dataIndex: 'strategy_name', key: 'strategy_name', width: 120 },
    { title: '股票', dataIndex: 'symbols', key: 'symbols', width: 150, render: (symbols: string[]) => symbols.join(', ') },
    { title: '初始资金', dataIndex: 'initial_capital', key: 'initial_capital', width: 120, render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '最终价值', dataIndex: 'final_value', key: 'final_value', width: 120, render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '收益率', dataIndex: 'total_return', key: 'total_return', width: 100, render: (v: number) => <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>{(v * 100).toFixed(2)}%</span> },
    { title: '最大回撤', dataIndex: 'max_drawdown', key: 'max_drawdown', width: 100, render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio', width: 100, render: (v: number) => v.toFixed(2) },
  ]

  return (
    <div>
      <h2>回测管理</h2>

      <Card title="创建回测" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="symbols" label="股票代码" rules={[{ required: true, message: '请输入股票代码' }]}>
            <Input.TextArea
              placeholder="输入股票代码，多个用逗号分隔，如: 600519,000858,300750"
              rows={2}
            />
          </Form.Item>

          <Form.Item label="快速选择">
            <Space wrap>
              {HOT_STOCKS.map(stock => (
                <Button
                  key={stock.code}
                  size="small"
                  onClick={() => {
                    const current = form.getFieldValue('symbols') || ''
                    const symbols = current ? current.split(',').map((s: string) => s.trim()) : []
                    if (!symbols.includes(stock.code)) {
                      form.setFieldsValue({
                        symbols: [...symbols, stock.code].join(',')
                      })
                    }
                  }}
                >
                  {stock.name}
                </Button>
              ))}
            </Space>
          </Form.Item>

          <Form.Item name="strategy" label="策略" rules={[{ required: true, message: '请选择策略' }]}>
            <Select placeholder="选择策略" showSearch>
              {STRATEGIES.map(s => (
                <Option key={s.name} value={s.name}>
                  {s.label} ({s.name})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="dateRange" label="日期范围" rules={[{ required: true, message: '请选择日期范围' }]}>
            <RangePicker style={{ width: '100%' }} />
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
        <Table
          columns={columns}
          dataSource={results}
          rowKey="backtest_id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  )
}

export default Backtest
