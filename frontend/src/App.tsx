import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Dashboard from './pages/Dashboard'
import StockList from './pages/StockList'
import StockDetail from './pages/StockDetail'
import Analysis from './pages/Analysis'
import Signals from './pages/Signals'
import Portfolio from './pages/Portfolio'
import News from './pages/News'
import Recommend from './pages/Recommend'
import Settings from './pages/Settings'
import PluginAnalysis from './pages/PluginAnalysis'
import AppHeader from './components/AppHeader'
import AppSidebar from './components/AppSidebar'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppSidebar />
      <Layout>
        <AppHeader />
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stocks" element={<StockList />} />
            <Route path="/stocks/:symbol" element={<StockDetail />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/news" element={<News />} />
            <Route path="/recommend" element={<Recommend />} />
            <Route path="/plugins" element={<PluginAnalysis />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
