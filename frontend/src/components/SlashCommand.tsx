import React, { useState, useRef } from 'react';
import { Input, List, Tag, Typography, Card } from 'antd';
import { CommandOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface Command {
  name: string;
  description: string;
  plugin: string;
  usage: string;
}

interface SlashCommandProps {
  onExecute: (plugin: string, params: any) => void;
}

const COMMANDS: Command[] = [
  { name: 'dcf', description: 'DCF 估值分析', plugin: 'dcf_valuation', usage: '/dcf <股票代码>' },
  { name: 'comps', description: '可比公司分析', plugin: 'comparable_analysis', usage: '/comps <股票代码> <同行代码>' },
  { name: 'screen', description: '股票筛选', plugin: 'stock_screening', usage: '/screen <筛选条件>' },
  { name: 'earnings', description: '财报分析', plugin: 'earnings_analysis', usage: '/earnings <股票代码> <期间>' },
  { name: 'lbo', description: 'LBO 分析', plugin: 'lbo_analysis', usage: '/lbo <股票代码>' },
  { name: 'ddm', description: 'DDM 估值', plugin: 'ddm_valuation', usage: '/ddm <股票代码>' },
  { name: 'onepager', description: '公司简介', plugin: 'company_one_pager', usage: '/onepager <股票代码>' },
];

const SlashCommand: React.FC<SlashCommandProps> = ({ onExecute }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Command[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<any>(null);

  const handleInputChange = (value: string) => {
    setQuery(value);
    if (value.startsWith('/')) {
      const command = value.slice(1).split(' ')[0].toLowerCase();
      const matching = COMMANDS.filter(c => c.name.startsWith(command));
      setSuggestions(matching);
      setShowSuggestions(matching.length > 0 && command.length > 0);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleCommandSelect = (command: Command) => {
    const args = query.slice(command.name.length + 2).trim();
    const parts = args.split(/\s+/);
    const symbol = parts[0] || '';

    const params: Record<string, any> = {};
    if (command.name === 'comps' && parts.length > 1) {
      params.peer_codes = parts.slice(1);
    }

    onExecute(command.plugin, { symbol, ...params });
    setQuery('');
    setShowSuggestions(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && suggestions.length > 0 && showSuggestions) {
      handleCommandSelect(suggestions[0]);
    }
  };

  return (
    <Card
      size="small"
      title={<><CommandOutlined /> 快捷命令</>}
      style={{ marginBottom: 16 }}
    >
      <div style={{ position: 'relative' }}>
        <Input
          ref={inputRef}
          prefix="/"
          placeholder="输入命令... (如 /dcf 600519)"
          value={query}
          onChange={e => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.startsWith('/') && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        />
        {showSuggestions && (
          <div style={{
            position: 'absolute',
            zIndex: 1000,
            background: 'white',
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            marginTop: 4,
            width: '100%',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            <List
              size="small"
              dataSource={suggestions}
              renderItem={item => (
                <List.Item
                  style={{ cursor: 'pointer', padding: '8px 12px' }}
                  onClick={() => handleCommandSelect(item)}
                >
                  <Tag color="blue">/{item.name}</Tag>
                  <Text>{item.description}</Text>
                  <Text type="secondary" style={{ marginLeft: 'auto', fontSize: 12 }}>
                    {item.usage}
                  </Text>
                </List.Item>
              )}
            />
          </div>
        )}
      </div>
    </Card>
  );
};

export default SlashCommand;
