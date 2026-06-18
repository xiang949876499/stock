import { useState, useEffect } from 'react'
import { Card, Form, Input, Select, Button, Descriptions, Tag, message, Space, DatePicker } from 'antd'
import { useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { analysisApi } from '../services/api'
import type { AnalysisResponse } from '../types'

const { Option } = Select

const Analysis = () => {
  const [form] = Form.useForm()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResponse | null>(null)

  useEffect(() => {
    // 从 URL 参数获取股票代码
    const symbol = searchParams.get('symbol')
    if (symbol) {
      form.setFieldsValue({ symbol })
      // 自动触发分析
      handleAnalyze(
        symbol,
        form.getFieldValue('market') || 'A',
        form.getFieldValue('strategy') || 'comprehensive',
        form.getFieldValue('analysis_date'),
      )
    }
  }, [searchParams])

  const toAnalysisDate = (value?: any) => {
    if (!value) return undefined
    return typeof value.format === 'function' ? value.format('YYYY-MM-DD') : value
  }

  const handleAnalyze = async (symbol: string, market: string, strategy: string, analysisDate?: any) => {
    setLoading(true)
    try {
      const response = await analysisApi.analyze({
        symbol,
        market,
        strategy,
        analysis_date: toAnalysisDate(analysisDate),
      })
      setResult(response.data)
      message.success('分析完成')
    } catch (error) {
      message.error('分析失败，请检查 AI 配置')
    } finally {
      setLoading(false)
    }
  }

  const onFinish = async (values: any) => {
    await handleAnalyze(values.symbol, values.market, values.strategy, values.analysis_date)
  }

  return (
    <div>
      <h2>股票分析</h2>

      <Card style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={onFinish}
          initialValues={{ market: 'A', strategy: 'comprehensive', analysis_date: dayjs() }}
        >
          <Form.Item
            name="symbol"
            label="股票代码"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <Input placeholder="例如: 600519" style={{ width: 150 }} />
          </Form.Item>

          <Form.Item name="market" label="市场">
            <Select style={{ width: 100 }}>
              <Option value="A">A股</Option>
              <Option value="HK">港股</Option>
            </Select>
          </Form.Item>

          <Form.Item name="strategy" label="策略">
            <Select style={{ width: 220 }}>
              <Option value="comprehensive">综合分析</Option>
              <Option value="ma_cross">均线金叉</Option>
              <Option value="macd">MACD</Option>
              <Option value="trend">趋势分析</Option>
              <Option value="news">新闻事件</Option>
              <Option value="macd_trend_resonance">MACD趋势共振</Option>
              <Option value="macd_second_golden_cross">MACD二次金叉</Option>
              <Option value="tuige_shortline">退哥短线</Option>
              <Option value="swing_defensive">摆动防御</Option>
              <Option value="tradingagents">TradingAgents 多智能体</Option>
            </Select>
          </Form.Item>

          <Form.Item name="analysis_date" label="分析日期">
            <DatePicker style={{ width: 140 }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                分析
              </Button>
              <Button onClick={() => { setResult(null); form.resetFields() }}>
                清空
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <Card title="分析结果">
          <Descriptions column={2}>
            <Descriptions.Item label="股票代码">{result.symbol}</Descriptions.Item>
            <Descriptions.Item label="评分">
              <Tag color={result.score >= 70 ? 'green' : result.score >= 50 ? 'orange' : 'red'}>
                {result.score}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="信号">
              <Tag color={result.signal === 'buy' ? 'green' : result.signal === 'sell' ? 'red' : 'blue'}>
                {result.signal === 'buy' ? '买入' : result.signal === 'sell' ? '卖出' : '持有'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="趋势">
              <Tag color={result.trend === 'bullish' ? 'green' : result.trend === 'bearish' ? 'red' : 'blue'}>
                {result.trend === 'bullish' ? '看多' : result.trend === 'bearish' ? '看空' : '震荡'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="分析理由" span={2}>
              {result.reason}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  )
}

export default Analysis
