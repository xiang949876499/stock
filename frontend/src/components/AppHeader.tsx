import { Layout, theme, Avatar, Dropdown } from 'antd'
import { UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons'

const { Header } = Layout

const AppHeader = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const items = [
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出',
    },
  ]

  return (
    <Header
      style={{
        padding: '0 24px',
        background: colorBgContainer,
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
      }}
    >
      <Dropdown menu={{ items }} placement="bottomRight">
        <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
      </Dropdown>
    </Header>
  )
}

export default AppHeader
