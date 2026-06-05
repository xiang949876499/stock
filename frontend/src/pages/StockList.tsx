import { useEffect } from 'react'
import { Table, Tag, Space, Button, Input } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useStockStore } from '../stores/stock'

const { Search } = Input

const StockList = () => {
  const { stocks, loading, fetchStocks } = useStockStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchStocks()
  }, [])

  const columns = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '市场',
      dataIndex: 'market',
      key: 'market',
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
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '正常' : '停牌'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" onClick={() => navigate(`/analysis?symbol=${record.symbol}`)}>
            分析
          </Button>
          <Button type="link" onClick={() => navigate(`/stocks/${record.symbol}`)}>
            详情
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
          placeholder="搜索股票代码或名称"
          style={{ width: 300 }}
          onSearch={(value) => fetchStocks(value)}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={stocks}
        rowKey="symbol"
        loading={loading}
      />
    </div>
  )
}

export default StockList
