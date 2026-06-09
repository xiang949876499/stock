import React from 'react';
import { Select, Typography } from 'antd';

const { Text } = Typography;

interface Plugin {
  name: string;
  description: string;
}

interface PluginSelectorProps {
  plugins: Plugin[];
  onSelect: (pluginName: string) => void;
  value?: string;
}

const PluginSelector: React.FC<PluginSelectorProps> = ({ plugins, onSelect, value }) => {
  return (
    <div style={{ marginBottom: 16 }}>
      <Text strong>选择分析插件</Text>
      <Select
        style={{ width: '100%', marginTop: 8 }}
        placeholder="选择插件"
        onChange={onSelect}
        value={value}
        options={plugins.map(p => ({
          label: `${p.name} - ${p.description}`,
          value: p.name,
          title: p.description
        }))}
      />
    </div>
  );
};

export default PluginSelector;
