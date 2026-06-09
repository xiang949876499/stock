import React, { useEffect } from 'react';
import { Form, InputNumber, Input, Select, Button, Typography, Card, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ParameterDef {
  type: string;
  default: any;
  description: string;
}

interface ParameterFormProps {
  parameters: Record<string, ParameterDef>;
  loading: boolean;
  onSubmit: (params: Record<string, any>) => void;
}

const ParameterForm: React.FC<ParameterFormProps> = ({ parameters, loading, onSubmit }) => {
  const [form] = Form.useForm();

  // 当参数定义变化时，重置表单为默认值
  useEffect(() => {
    const defaults: Record<string, any> = {};
    for (const [key, def] of Object.entries(parameters)) {
      defaults[key] = def.default;
    }
    form.setFieldsValue(defaults);
  }, [parameters, form]);

  const renderField = (name: string, def: ParameterDef) => {
    const label = (
      <span>
        {name}
        <Tooltip title={def.description}>
          <QuestionCircleOutlined style={{ marginLeft: 4, color: '#999' }} />
        </Tooltip>
      </span>
    );

    // List[str] 类型 - 用逗号分隔输入
    if (def.type === 'List[str]') {
      return (
        <Form.Item key={name} name={name} label={label}>
          <Select
            mode="tags"
            placeholder="输入后回车添加"
            tokenSeparators={[',']}
          />
        </Form.Item>
      );
    }

    // Dict 类型 - 用 JSON 输入
    if (def.type.startsWith('Dict')) {
      return (
        <Form.Item
          key={name}
          name={name}
          label={label}
          rules={[
            {
              validator: async (_, value) => {
                if (!value) return;
                if (typeof value === 'object') return;
                try {
                  JSON.parse(value);
                } catch {
                  throw new Error('请输入有效的 JSON');
                }
              },
            },
          ]}
        >
          <Input.TextArea
            rows={3}
            placeholder={JSON.stringify(def.default || {}, null, 2)}
          />
        </Form.Item>
      );
    }

    // int 类型
    if (def.type === 'int') {
      return (
        <Form.Item key={name} name={name} label={label}>
          <InputNumber style={{ width: '100%' }} />
        </Form.Item>
      );
    }

    // float 类型
    if (def.type === 'float') {
      return (
        <Form.Item key={name} name={name} label={label}>
          <InputNumber style={{ width: '100%' }} step={0.01} />
        </Form.Item>
      );
    }

    // str 类型
    return (
      <Form.Item key={name} name={name} label={label}>
        <Input placeholder={def.description} />
      </Form.Item>
    );
  };

  const handleFinish = (values: Record<string, any>) => {
    // 处理 Dict 类型的 JSON 字符串输入
    const processed: Record<string, any> = {};
    for (const [key, value] of Object.entries(values)) {
      const def = parameters[key];
      if (def && def.type.startsWith('Dict') && typeof value === 'string') {
        try {
          processed[key] = JSON.parse(value);
        } catch {
          processed[key] = {};
        }
      } else {
        processed[key] = value;
      }
    }
    onSubmit(processed);
  };

  const paramEntries = Object.entries(parameters);

  if (paramEntries.length === 0) {
    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Text type="secondary">此插件无需额外参数</Text>
        <div style={{ marginTop: 12 }}>
          <Button type="primary" loading={loading} onClick={() => onSubmit({})}>
            执行分析
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card size="small" title="插件参数" style={{ marginBottom: 16 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        size="small"
      >
        {paramEntries.map(([name, def]) => renderField(name, def))}
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            执行分析
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ParameterForm;
