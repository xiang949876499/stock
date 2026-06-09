import { useState, useEffect, useCallback } from 'react';
import { Card, Input, Typography, Alert, Descriptions, Tag, Table, Spin, Empty } from 'antd';
import PluginSelector from '../components/PluginSelector';
import ParameterForm from '../components/ParameterForm';
import SlashCommand from '../components/SlashCommand';
import { pluginApi } from '../services/api';

const { Title, Text } = Typography;

interface PluginInfo {
  name: string;
  description: string;
  version: string;
  parameters: Record<string, { type: string; default: any; description: string }>;
}

const PluginAnalysis = () => {
  const [plugins, setPlugins] = useState<{ name: string; description: string }[]>([]);
  const [selectedPlugin, setSelectedPlugin] = useState<string>('');
  const [pluginInfo, setPluginInfo] = useState<PluginInfo | null>(null);
  const [symbol, setSymbol] = useState<string>('600519');
  const [loading, setLoading] = useState(false);
  const [pluginsLoading, setPluginsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  // 加载插件列表
  useEffect(() => {
    setPluginsLoading(true);
    pluginApi
      .list()
      .then((res) => {
        const data = res.data;
        const list = Object.entries(data).map(([name, description]) => ({
          name,
          description: description as string,
        }));
        setPlugins(list);
      })
      .catch((err) => {
        console.error('加载插件列表失败:', err);
        setError('加载插件列表失败，请确认后端服务已启动');
      })
      .finally(() => setPluginsLoading(false));
  }, []);

  // 选择插件后加载插件详情
  const handleSelectPlugin = useCallback((pluginName: string) => {
    setSelectedPlugin(pluginName);
    setResult(null);
    setError('');

    pluginApi
      .getInfo(pluginName)
      .then((res) => {
        setPluginInfo(res.data);
      })
      .catch((err) => {
        console.error('加载插件信息失败:', err);
        setError('加载插件信息失败');
        setPluginInfo(null);
      });
  }, []);

  // 执行插件分析
  const handleExecute = useCallback(
    (params: Record<string, any>) => {
      if (!selectedPlugin) return;

      setLoading(true);
      setError('');
      setResult(null);

      pluginApi
        .execute(selectedPlugin, { symbol, params })
        .then((res) => {
          setResult(res.data);
        })
        .catch((err) => {
          console.error('执行分析失败:', err);
          setError(err.response?.data?.detail || '执行分析失败');
        })
        .finally(() => setLoading(false));
    },
    [selectedPlugin, symbol]
  );

  // 斜杠命令执行
  const handleSlashCommand = useCallback(
    (plugin: string, params: any) => {
      setSelectedPlugin(plugin);
      if (params.symbol) {
        setSymbol(params.symbol);
      }
      setResult(null);
      setError('');

      setLoading(true);
      pluginApi
        .execute(plugin, { symbol: params.symbol || symbol, params })
        .then((res) => {
          setResult(res.data);
        })
        .catch((err) => {
          console.error('执行分析失败:', err);
          setError(err.response?.data?.detail || '执行分析失败');
        })
        .finally(() => setLoading(false));
    },
    [symbol]
  );

  // 渲染结果
  const renderResult = (data: any) => {
    if (data === null || data === undefined) {
      return <Text type="secondary">无数据</Text>;
    }

    // 数组结果 - 用表格展示
    if (Array.isArray(data)) {
      if (data.length === 0) {
        return <Empty description="无结果" />;
      }
      // 数组元素是对象时用表格
      if (typeof data[0] === 'object' && data[0] !== null) {
        const columns = Object.keys(data[0]).map((key) => ({
          title: key,
          dataIndex: key,
          key,
          ellipsis: true,
          render: (val: any) =>
            typeof val === 'object' ? JSON.stringify(val) : String(val ?? ''),
        }));
        return (
          <Table
            dataSource={data.map((item, i) => ({ ...item, key: i }))}
            columns={columns}
            size="small"
            pagination={false}
            scroll={{ x: true }}
          />
        );
      }
      // 数组元素是基本类型
      return (
        <div>
          {data.map((item, i) => (
            <Tag key={i}>{String(item)}</Tag>
          ))}
        </div>
      );
    }

    // 对象结果 - 用 Descriptions 展示
    if (typeof data === 'object') {
      return (
        <Descriptions column={2} bordered size="small">
          {Object.entries(data).map(([key, value]) => (
            <Descriptions.Item key={key} label={key}>
              {typeof value === 'object' && value !== null ? (
                renderResult(value)
              ) : (
                <Text>{formatValue(key, value)}</Text>
              )}
            </Descriptions.Item>
          ))}
        </Descriptions>
      );
    }

    return <Text>{String(data)}</Text>;
  };

  // 格式化展示值
  const formatValue = (key: string, value: any): string => {
    if (typeof value === 'number') {
      // 百分比字段
      if (key.includes('pct') || key.includes('percent') || key.includes('premium') || key.includes('discount') || key.includes('upside')) {
        return `${value}%`;
      }
      // 金额字段
      if (key.includes('value') || key.includes('price') || key.includes('cost') || key.includes('cap')) {
        return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }
    }
    return String(value);
  };

  return (
    <div>
      <Title level={3}>插件分析</Title>

      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          closable
          onClose={() => setError('')}
          style={{ marginBottom: 16 }}
        />
      )}

      <SlashCommand onExecute={handleSlashCommand} />

      <Card loading={pluginsLoading} style={{ marginBottom: 16 }}>
        <PluginSelector
          plugins={plugins}
          onSelect={handleSelectPlugin}
          value={selectedPlugin || undefined}
        />

        <div style={{ marginBottom: 16 }}>
          <Text strong>股票代码</Text>
          <Input
            style={{ marginTop: 8 }}
            placeholder="输入股票代码，如 600519"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
        </div>
      </Card>

      {selectedPlugin && pluginInfo && (
        <ParameterForm
          parameters={pluginInfo.parameters}
          loading={loading}
          onSubmit={handleExecute}
        />
      )}

      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <Spin tip="正在执行分析..." />
          </div>
        </Card>
      )}

      {result && !loading && (
        <Card title="分析结果" style={{ marginTop: 16 }}>
          {renderResult(result)}
        </Card>
      )}
    </div>
  );
};

export default PluginAnalysis;
