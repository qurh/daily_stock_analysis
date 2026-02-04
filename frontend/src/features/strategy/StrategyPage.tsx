'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Tabs,
  Statistic,
  Row,
  Col,
  message,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import { strategyApi } from '@/services/api'
import { Strategy, SignalResponse } from '@/types'

const { TextArea } = Input
const { TabPane } = Tabs
const { Option } = Select

export default function StrategyPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)

  const [form] = Form.useForm()

  // Load strategies
  const loadStrategies = useCallback(async () => {
    setLoading(true)
    try {
      const response = await strategyApi.listStrategies({ limit: 100 })
      setStrategies(response.data.strategies || [])
    } catch (error) {
      console.error('Load strategies error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load signals
  const loadSignals = useCallback(async () => {
    try {
      const response = await strategyApi.getSignals({ limit: 50 })
      setSignals(response.data || [])
    } catch (error) {
      console.error('Load signals error:', error)
    }
  }, [])

  useEffect(() => {
    loadStrategies()
    loadSignals()
  }, [loadStrategies, loadSignals])

  // Create strategy
  const handleCreateStrategy = async () => {
    try {
      const values = await form.validateFields()

      await strategyApi.createStrategy({
        name: values.name,
        category: values.category,
        description: values.description,
        conditions: {
          ma_cross: values.ma_cross,
          volume_ratio: values.volume_ratio,
        },
        actions: {
          signal: values.action_signal,
          position_ratio: values.position_ratio,
        },
        risk_management: {
          stop_loss: values.stop_loss,
          take_profit: values.take_profit,
        },
      })

      message.success('策略已创建')
      setCreateModalVisible(false)
      form.resetFields()
      loadStrategies()
    } catch (error) {
      console.error('Create strategy error:', error)
    }
  }

  // Run backtest
  const handleBacktest = async (strategy: Strategy) => {
    Modal.info({
      title: '回测功能',
      content: `即将对策略 "${strategy.name}" 进行回测。此功能需要更多参数配置。`,
    })
  }

  // Delete strategy
  const handleDeleteStrategy = async (strategyId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个策略吗？',
      onOk: async () => {
        try {
          await strategyApi.deleteStrategy(strategyId)
          message.success('策略已删除')
          loadStrategies()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Strategy) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{record.description || '-'}</div>
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const colors: Record<string, string> = {
          trend: 'blue',
          value: 'green',
          breakout: 'orange',
          mean_reversion: 'purple',
        }
        return <Tag color={colors[category] || 'default'}>{category}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'active' ? 'success' : 'default'} text={status} />
      ),
    },
    {
      title: '验证次数',
      dataIndex: 'verification_count',
      key: 'verification_count',
    },
    {
      title: '胜率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: number) => rate ? `${rate}%` : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Strategy) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleBacktest(record)}
          >
            回测
          </Button>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedStrategy(record)
            }}
          />
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteStrategy(record.id)}
          />
        </Space>
      ),
    },
  ]

  const signalColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '股票',
      dataIndex: 'code',
      key: 'code',
      render: (code: string) => <Tag>{code}</Tag>,
    },
    {
      title: '策略',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
    },
    {
      title: '信号',
      dataIndex: 'signal_type',
      key: 'signal_type',
      render: (type: string) => {
        const color = type === 'buy' ? 'green' : type === 'sell' ? 'red' : 'orange'
        return <Tag color={color}>{type.toUpperCase()}</Tag>
      },
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (val: number) => `${(val * 100).toFixed(0)}%`,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '理由',
      dataIndex: 'reasoning',
      key: 'reasoning',
      ellipsis: true,
    },
  ]

  const stats = [
    { title: '策略总数', value: strategies.length },
    { title: '活跃策略', value: strategies.filter(s => s.status === 'active').length },
    { title: '今日信号', value: signals.filter(s => {
      const today = new Date().toDateString()
      return new Date(s.created_at).toDateString() === today
    }).length },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {stats.map(s => (
          <Col span={8} key={s.title}>
            <Card>
              <Statistic title={s.title} value={s.value} prefix={<ExperimentOutlined />} />
            </Card>
          </Col>
        ))}
      </Row>

      <Tabs defaultActiveKey="strategies">
        <TabPane tab="策略列表" key="strategies">
          <Card
            title="交易策略"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setSelectedStrategy(null)
                  form.resetFields()
                  setCreateModalVisible(true)
                }}
              >
                新建策略
              </Button>
            }
          >
            <Table
              dataSource={strategies}
              columns={strategyColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="交易信号" key="signals">
          <Card title="实时信号">
            <Table
              dataSource={signals}
              columns={signalColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Create Strategy Modal */}
      <Modal
        title="新建策略"
        open={createModalVisible}
        onOk={handleCreateStrategy}
        onCancel={() => setCreateModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="策略名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="输入策略名称" />
          </Form.Item>

          <Form.Item
            name="category"
            label="策略分类"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择分类">
              <Option value="trend">趋势跟踪</Option>
              <Option value="value">价值投资</Option>
              <Option value="breakout">突破交易</Option>
              <Option value="mean_reversion">均值回归</Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="策略描述">
            <TextArea rows={2} placeholder="描述策略逻辑" />
          </Form.Item>

          <Form.Item
            name="ma_cross"
            label="均线交叉条件"
            initialValue="ma5_cross_ma20"
          >
            <Select>
              <Option value="ma5_cross_ma20">MA5 上穿 MA20</Option>
              <Option value="ma10_cross_ma20">MA10 上穿 MA20</Option>
              <Option value="ma5_cross_ma60">MA5 上穿 MA60</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="volume_ratio"
            label="成交量要求"
            initialValue={1.5}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.5}
              max={5}
              step={0.1}
              precision={1}
            />
          </Form.Item>

          <Form.Item
            name="action_signal"
            label="信号类型"
            initialValue="buy"
          >
            <Select>
              <Option value="buy">买入</Option>
              <Option value="sell">卖出</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="stop_loss" label="止损比例" initialValue={5}>
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  max={50}
                  suffix="%"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="take_profit" label="止盈比例" initialValue={15}>
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  max={100}
                  suffix="%"
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}
