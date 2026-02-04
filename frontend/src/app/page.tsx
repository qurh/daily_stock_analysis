'use client'

import React, { useState } from 'react'
import { Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  MessageOutlined,
  FileTextOutlined,
  StockOutlined,
  BellOutlined,
  PieChartOutlined,
  SettingOutlined,
  BookOutlined,
} from '@ant-design/icons'
import ChatPage from '@/features/chat/ChatPage'
import KnowledgePage from '@/features/knowledge/KnowledgePage'
import MarketPage from '@/features/market/MarketPage'
import PortfolioPage from '@/features/portfolio/PortfolioPage'
import MonitorPage from '@/features/monitor/MonitorPage'
import StrategyPage from '@/features/strategy/StrategyPage'
import ReviewPage from '@/features/review/ReviewPage'
import SettingsPage from '@/features/settings/SettingsPage'

const { Header, Sider, Content } = Layout

export default function Home() {
  const [activeKey, setActiveKey] = useState('chat')
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: 'chat', icon: <MessageOutlined />, label: 'AI 对话' },
    { key: 'knowledge', icon: <FileTextOutlined />, label: '知识库' },
    { key: 'market', icon: <StockOutlined />, label: '行情' },
    { key: 'portfolio', icon: <StockOutlined />, label: '持仓' },
    { key: 'monitor', icon: <BellOutlined />, label: '盯盘' },
    { key: 'strategy', icon: <PieChartOutlined />, label: '策略' },
    { key: 'review', icon: <BookOutlined />, label: '复盘' },
    { key: 'settings', icon: <SettingOutlined />, label: '设置' },
  ]

  const renderContent = () => {
    switch (activeKey) {
      case 'dashboard':
        return (
          <div style={{ padding: 24 }}>
            <h1>欢迎使用 AI 股票分析系统</h1>
            <p>选择左侧菜单开始使用...</p>
          </div>
        )
      case 'chat':
        return <ChatPage />
      case 'knowledge':
        return <KnowledgePage />
      case 'market':
        return <MarketPage />
      case 'portfolio':
        return <PortfolioPage />
      case 'monitor':
        return <MonitorPage />
      case 'strategy':
        return <StrategyPage />
      case 'review':
        return <ReviewPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <ChatPage />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={false}
        theme="light"
        width={200}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          AI 股票分析
        </div>
        <Menu
          mode="inline"
          selectedKeys={[activeKey]}
          onClick={({ key }) => setActiveKey(key)}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <h2 style={{ margin: 0, lineHeight: '64px' }}>
            {menuItems.find((item) => item.key === activeKey)?.label}
          </h2>
        </Header>
        <Content style={{ margin: 0, overflow: 'auto' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  )
}
