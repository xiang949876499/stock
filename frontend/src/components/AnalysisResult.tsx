import { Card, Descriptions, Tag, Progress } from 'antd'
import type { AnalysisResponse } from '../types'
import { getSignalColor, getSignalText, getTrendColor, getTrendText } from '../utils'

interface AnalysisResultProps {
  result: AnalysisResponse
}

const AnalysisResult = ({ result }: AnalysisResultProps) => {
  return (
    <Card title="分析结果">
      <Descriptions column={2}>
        <Descriptions.Item label="股票代码">
          {result.symbol}
        </Descriptions.Item>

        <Descriptions.Item label="评分">
          <Progress
            type="circle"
            percent={result.score}
            width={60}
            format={(percent) => `${percent}`}
            strokeColor={result.score >= 70 ? '#3f8600' : result.score >= 50 ? '#faad14' : '#cf1322'}
          />
        </Descriptions.Item>

        <Descriptions.Item label="信号">
          <Tag color={getSignalColor(result.signal)}>
            {getSignalText(result.signal)}
          </Tag>
        </Descriptions.Item>

        <Descriptions.Item label="趋势">
          <Tag color={getTrendColor(result.trend)}>
            {getTrendText(result.trend)}
          </Tag>
        </Descriptions.Item>

        <Descriptions.Item label="分析理由" span={2}>
          {result.reason}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  )
}

export default AnalysisResult
