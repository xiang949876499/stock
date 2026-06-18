import { useEffect, useState } from 'react'
import { Table, Tag, Space, Button, Input, Select, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { StarOutlined, StarFilled } from '@ant-design/icons'
import { useStockStore } from '../stores/stock'

const { Search } = Input
const { Option } = Select

const StockList = () => {
  const { stocks, loading, fetchStocks } = useStockStore()
  const navigate = useNavigate()
  const [market, setMarket] = useState<string>('')
  const [searchText, setSearchText] = useState('')
  const [watchlist, setWatchlist] = useState<string[]>([])

  useEffect(() => {
    fetchStocks()
    // 加载自选股
    const saved = localStorage.getItem('watchlist')
    if (saved) {
      setWatchlist(JSON.parse(saved))
    }
  }, [])

  const toggleWatchlist = (symbol: string) => {
    let newList = [...watchlist]
    if (newList.includes(symbol)) {
      newList = newList.filter(s => s !== symbol)
      message.success('已从自选股移除')
    } else {
      newList.push(symbol)
      message.success('已添加到自选股')
    }
    setWatchlist(newList)
    localStorage.setItem('watchlist', JSON.stringify(newList))
  }

  const filteredStocks = stocks.filter(stock => {
    const matchMarket = !market || stock.market === market
    const matchSearch = !searchText ||
      stock.symbol.includes(searchText) ||
      stock.name.includes(searchText)
    return matchMarket && matchSearch
  })

  const columns = [
    {
      title: '',
      key: 'watch',
      width: 40,
      render: (_: any, record: any) => (
        <Button
          type="text"
          icon={watchlist.includes(record.symbol) ?
            <StarFilled style={{ color: '#faad14' }} /> :
            <StarOutlined />
          }
          onClick={(e) => {
            e.stopPropagation()
            toggleWatchlist(record.symbol)
          }}
        />
      ),
    },
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '市场',
      dataIndex: 'market',
      key: 'market',
      width: 80,
      render: (market: string) => (
        <Tag color={market === 'A' ? 'blue' : 'green'}>
          {market === 'A' ? 'A股' : '港股'}
        </Tag>
      ),
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '正常' : '停牌'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            onClick={() => navigate(`/stocks/${record.symbol}`)}
          >
            详情
          </Button>
          <Button
            type="link"
            onClick={() => navigate(`/analysis?symbol=${record.symbol}`)}
          >
            分析
          </Button>
          <Button
            type="link"
            onClick={() => navigate(`/news?symbol=${record.symbol}`)}
          >
            新闻
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2>股票列表</h2>

      <Space style={{ marginBottom: 16 }}>
        <Search
          placeholder="搜索代码或名称"
          style={{ width: 250 }}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />
        <Select
          value={market}
          onChange={setMarket}
          style={{ width: 120 }}
          allowClear
          placeholder="全部市场"
        >
          <Option value="">全部</Option>
          <Option value="A">A股</Option>
          <Option value="HK">港股</Option>
        </Select>
        <Button
          onClick={() => {
            fetchStocks()
            message.success('刷新成功')
          }}
        >
          刷新
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={filteredStocks}
        rowKey="symbol"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 800 }}
      />
    </div>
  )
}

export default StockList
