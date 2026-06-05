import { Card, Form, Input, Select, Button, Divider, message } from 'antd'

const { Option } = Select

const Settings = () => {
  const [form] = Form.useForm()

  const onFinish = (values: any) => {
    console.log('保存设置:', values)
    message.success('设置已保存')
  }

  return (
    <div>
      <h2>设置</h2>

      <Card title="AI 模型配置">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            ai_provider: 'openai',
            ai_model: 'gpt-4',
          }}
        >
          <Form.Item name="ai_provider" label="AI 提供商">
            <Select>
              <Option value="openai">OpenAI</Option>
              <Option value="claude">Claude</Option>
              <Option value="deepseek">DeepSeek</Option>
              <Option value="qwen">通义千问</Option>
              <Option value="gemini">Gemini</Option>
            </Select>
          </Form.Item>

          <Form.Item name="ai_api_key" label="API Key">
            <Input.Password placeholder="请输入 API Key" />
          </Form.Item>

          <Form.Item name="ai_model" label="模型">
            <Input placeholder="例如: gpt-4" />
          </Form.Item>

          <Form.Item name="ai_base_url" label="Base URL（可选）">
            <Input placeholder="自定义 API 地址" />
          </Form.Item>

          <Divider />

          <Form.Item name="data_provider" label="数据源">
            <Select>
              <Option value="akshare">AkShare</Option>
              <Option value="tushare">Tushare</Option>
              <Option value="yfinance">YFinance</Option>
            </Select>
          </Form.Item>

          <Divider />

          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Settings
