'use client'

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Input,
  Table,
  Tag,
  Space,
  Button,
  Spin,
  Statistic,
} from 'antd'
import {
  SearchOutlined,
  StockOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import { marketApi } from '@/services/api'
import { Quote, OHLCV } from '@/types'

const { Search } = Input

export default function MarketPage() {
  const [loading, setLoading] = useState(false)
  const [quotes, setQuotes] = useState<Quote[]>([])
  const [watchlist, setWatchlist] = useState<string[]>([
    '600519', '000001', '000300', '399001', '399006',
  ])
  const [searchCode, setSearchCode] = useState('')
  const [selectedStock, setSelectedStock] = useState<string | null>(null)
  const [history, setHistory] = useState<OHLCV[]>([])

  // Load watchlist quotes
  const loadQuotes = async () => {
    setLoading(true)
    try {
      const response = await marketApi.getQuotes(watchlist)
      setQuotes(response.data || [])
    } catch (error) {
      console.error('Load quotes error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQuotes()
    // Refresh every 60 seconds
    const interval = setInterval(loadQuotes, 60000)
    return () => clearInterval(interval)
  }, [watchlist])

  // Load stock history when selected
  useEffect(() => {
    if (selectedStock) {
      loadHistory(selectedStock)
    }
  }, [selectedStock])

  const loadHistory = async (code: string) => {
    try {
      const response = await marketApi.getHistory({
        code,
        period: 'daily',
        limit: 30,
      })
      setHistory(response.data.data || [])
    } catch (error) {
      console.error('Load history error:', error)
    }
  }

  const handleSearch = (value: string) => {
    if (value.trim()) {
      setSelectedStock(value.trim())
    }
  }

  const columns = [
    {
      title: '代码',
      dataIndex: 'code',
      key: 'code',
      render: (code: string) => (
        <Button type="link" onClick={() => setSelectedStock(code)}>
          {code}
        </Button>
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => (
        <span style={{ fontWeight: 500 }}>¥{price.toFixed(2)}</span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_chg',
      key: 'pct_chg',
      render: (pct: number) => (
        <Tag color={pct >= 0 ? 'red' : 'green'}>
          {pct >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          {Math.abs(pct).toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      render: (rate: number) => `${rate?.toFixed(2)}%`,
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* Search */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Search
            placeholder="输入股票代码或名称"
            allowClear
            onSearch={handleSearch}
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
          />
          <Button onClick={() => loadQuotes()}>刷新</Button>
        </Space>
      </Card>

      {/* Selected Stock Detail */}
      {selectedStock && (
        <Card title={`${selectedStock} 详情`} style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            {quotes
              .filter((q) => q.code === selectedStock)
              .map((quote) => (
                <React.Fragment key={quote.code}>
                  <Col span={6}>
                    <Statistic
                      title="当前价格"
                      value={quote.price}
                      precision={2}
                      prefix="¥"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="涨跌幅"
                      value={quote.pct_chg}
                      precision={2}
                      valueStyle={{
                        color: quote.pct_chg >= 0 ? '#ff4d4f' : '#52c41a',
                      }}
                      prefix={
                        quote.pct_chg >= 0 ? (
                          <ArrowUpOutlined />
                        ) : (
                          <ArrowDownOutlined />
                        )
                      }
                      suffix="%"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="成交量"
                      value={quote.volume || 0}
                      valueStyle={{ fontSize: 16 }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="换手率"
                      value={quote.turnover_rate}
                      precision={2}
                      suffix="%"
                    />
                  </Col>
                </React.Fragment>
              ))}
          </Row>

          {/* Simple K-line visualization */}
          <div style={{ marginTop: 24 }}>
            <h4>最近30日走势</h4>
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                height: 100,
                gap: 2,
              }}
            >
              {history.slice(-30).map((item, i) => {
                const max = Math.max(...history.map((h) => h.close))
                const min = Math.min(...history.map((h) => h.close))
                const range = max - min || 1
                const height = ((item.close - min) / range) * 100
                const color = item.pct_chg >= 0 ? '#ff4d4f' : '#52c41a'

                return (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      height: `${height}%`,
                      background: color,
                      minWidth: 4,
                      maxWidth: 20,
                    }}
                    title={`${item.date}: ¥${item.close.toFixed(2)}`}
                  />
                )
              })}
            </div>
          </div>
        </Card>
      )}

      {/* Market Overview */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="上证指数"
              value={3250.25}
              precision={2}
              prefix={<StockOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#52c41a' }}>
                  <ArrowDownOutlined /> 0.25%
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="深证成指"
              value={11500.80}
              precision={2}
              prefix={<StockOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#ff4d4f' }}>
                  <ArrowUpOutlined /> 0.45%
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="创业板指"
              value={2350.50}
              precision={2}
              prefix={<StockOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#ff4d4f' }}>
                  <ArrowUpOutlined /> 0.82%
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="科创50"
              value={1050.30}
              precision={2}
              prefix={<StockOutlined />}
              suffix={
                <span style={{ fontSize: 14, color: '#52c41a' }}>
                  <ArrowDownOutlined /> 0.15%
                </span>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Watchlist */}
      <Card title="自选股">
        <Spin spinning={loading}>
          <Table
            dataSource={quotes}
            columns={columns}
            rowKey="code"
            pagination={false}
            size="small"
          />
        </Spin>
      </Card>
    </div>
  )
}
