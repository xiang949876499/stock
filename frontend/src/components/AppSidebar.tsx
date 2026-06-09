import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  StockOutlined,
  LineChartOutlined,
  BellOutlined,
  FundOutlined,
  FileTextOutlined,
  StarOutlined,
  AppstoreOutlined,
  ExperimentOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '工作台',
  },
  {
    key: '/stocks',
    icon: <StockOutlined />,
    label: '股票列表',
  },
  {
    key: '/recommend',
    icon: <StarOutlined />,
    label: '股票推荐',
  },
  {
    key: '/analysis',
    icon: <LineChartOutlined />,
    label: '分析报告',
  },
  {
    key: '/signals',
    icon: <BellOutlined />,
    label: '信号管理',
  },
  {
    key: '/portfolio',
    icon: <FundOutlined />,
    label: '持仓管理',
  },
  {
    key: '/news',
    icon: <FileTextOutlined />,
    label: '新闻舆情',
  },
  {
    key: '/plugins',
    icon: <AppstoreOutlined />,
    label: '插件分析',
  },
  {
    key: '/backtest',
    icon: <ExperimentOutlined />,
    label: '回测管理',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '设置',
  },
]

const AppSidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const onClick = (e: { key: string }) => {
    navigate(e.key)
  }

  return (
    <Sider collapsible>
      <div
        style={{
          height: 32,
          margin: 16,
          background: 'rgba(255, 255, 255, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 'bold',
          fontSize: 16,
        }}
      >
        Stock Hub
      </div>
      <Menu
        theme="dark"
        selectedKeys={[location.pathname]}
        mode="inline"
        items={menuItems}
        onClick={onClick}
      />
    </Sider>
  )
}

export default AppSidebar
