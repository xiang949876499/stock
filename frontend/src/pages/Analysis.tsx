import { useState } from 'react'
import { Card, Form, Input, Select, Button, Result, Descriptions, Tag } from 'antd'
import { analysisApi } from '../services/api'
import type { AnalysisResponse } from '../types'

const { Option } = Select

const Analysis = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResponse | null>(null)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const response = await analysisApi.analyze(values)
      setResult(response.data)
    } catch (error) {
      console.error('分析失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>股票分析</h2>

      <Card style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={onFinish}
          initialValues={{ market: 'A', strategy: 'comprehensive' }}
        >
          <Form.Item
            name="symbol"
            label="股票代码"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <Input placeholder="例如: 600519" />
          </Form.Item>

          <Form.Item name="market" label="市场">
            <Select style={{ width: 100 }}>
              <Option value="A">A股</Option>
              <Option value="HK">港股</Option>
            </Select>
          </Form.Item>

          <Form.Item name="strategy" label="策略">
            <Select style={{ width: 150 }}>
              <Option value="comprehensive">综合分析</Option>
              <Option value="ma_cross">均线金叉</Option>
              <Option value="macd">MACD</Option>
              <Option value="trend">趋势分析</Option>
              <Option value="news">新闻事件</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              分析
            </Button>
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
