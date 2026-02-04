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
  InputNumber,
  Statistic,
  Row,
  Col,
  Progress,
  message,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RiseOutlined,
  FallOutlined,
  WalletOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { portfolioApi, marketApi } from '@/services/api'
import { Portfolio, Position } from '@/types'

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(false)
  const [addModalVisible, setAddModalVisible] = useState(false)
  const [editPosition, setEditPosition] = useState<Position | null>(null)

  const [form] = Form.useForm()

  // Load portfolio
  const loadPortfolio = useCallback(async () => {
    setLoading(true)
    try {
      const response = await portfolioApi.getPortfolio()
      setPortfolio(response.data)
    } catch (error) {
      console.error('Load portfolio error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPortfolio()
  }, [loadPortfolio])

  // Add position
  const handleAddPosition = async () => {
    try {
      const values = await form.validateFields()

      await portfolioApi.addPosition({
        code: values.code,
        name: values.name,
        quantity: values.quantity,
        avg_cost: values.avg_cost,
        notes: values.notes,
      })

      message.success('持仓已添加')
      setAddModalVisible(false)
      form.resetFields()
      loadPortfolio()
    } catch (error) {
      console.error('Add position error:', error)
    }
  }

  // Update position
  const handleUpdatePosition = async () => {
    if (!editPosition) return

    try {
      const values = await form.validateFields()

      await portfolioApi.updatePosition(editPosition.id, {
        quantity: values.quantity,
        avg_cost: values.avg_cost,
        notes: values.notes,
      })

      message.success('持仓已更新')
      setEditPosition(null)
      form.resetFields()
      loadPortfolio()
    } catch (error) {
      console.error('Update position error:', error)
    }
  }

  // Delete position
  const handleDeletePosition = async (positionId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个持仓吗？',
      onOk: async () => {
        try {
          await portfolioApi.deletePosition(positionId)
          message.success('持仓已删除')
          loadPortfolio()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const columns = [
    {
      title: '股票',
      key: 'stock',
      render: (_: any, record: Position) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.code}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{record.name || '-'}</div>
        </div>
      ),
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (val: number) => val.toLocaleString(),
    },
    {
      title: '成本价',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (val: number) => `¥${val.toFixed(2)}`,
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (val: number) => `¥${val.toFixed(2)}`,
    },
    {
      title: '浮动盈亏',
      key: 'profit_loss',
      render: (_: any, record: Position) => (
        <span style={{ color: record.profit_loss >= 0 ? '#ff4d4f' : '#52c41a' }}>
          {record.profit_loss >= 0 ? '+' : ''}{record.profit_loss.toLocaleString()}
        </span>
      ),
    },
    {
      title: '收益率',
      key: 'profit_pct',
      render: (_: any, record: Position) => (
        <Tag color={record.profit_pct >= 0 ? 'red' : 'green'}>
          {record.profit_pct >= 0 ? <RiseOutlined /> : <FallOutlined />}
          {record.profit_pct.toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '仓位占比',
      dataIndex: 'position_ratio',
      key: 'position_ratio',
      render: (val: number, record: Position) => (
        <Tooltip title={`市值: ¥${(record.current_price * record.quantity).toLocaleString()}`}>
          <Progress
            percent={Number(val.toFixed(1))}
            size="small"
            status={record.profit_loss >= 0 ? 'success' : 'exception'}
            showInfo={false}
          />
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Position) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setEditPosition(record)
              form.setFieldsValue({
                quantity: record.quantity,
                avg_cost: record.avg_cost,
                notes: record.notes,
              })
            }}
          />
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeletePosition(record.id)}
          />
        </Space>
      ),
    },
  ]

  const summary = portfolio?.summary

  return (
    <div style={{ padding: 24 }}>
      {/* Summary Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总资产"
              value={summary?.total_value || 0}
              prefix={<DollarOutlined />}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="浮动盈亏"
              value={summary?.total_profit || 0}
              prefix={summary?.total_profit >= 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{ color: summary?.total_profit >= 0 ? '#ff4d4f' : '#52c41a' }}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="收益率"
              value={summary?.total_profit_pct || 0}
              suffix="%"
              valueStyle={{ color: summary?.total_profit_pct >= 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="持仓数量"
              value={summary?.position_count || 0}
              prefix={<WalletOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Holdings Table */}
      <Card
        title="当前持仓"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditPosition(null)
              form.resetFields()
              setAddModalVisible(true)
            }}
          >
            添加持仓
          </Button>
        }
      >
        <Table
          dataSource={portfolio?.positions || []}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Add/Edit Position Modal */}
      <Modal
        title={editPosition ? '编辑持仓' : '添加持仓'}
        open={addModalVisible || editPosition !== null}
        onOk={editPosition ? handleUpdatePosition : handleAddPosition}
        onCancel={() => {
          setAddModalVisible(false)
          setEditPosition(null)
          form.resetFields()
        }}
      >
        <Form form={form} layout="vertical">
          {!editPosition && (
            <>
              <Form.Item
                name="code"
                label="股票代码"
                rules={[{ required: true, message: '请输入股票代码' }]}
              >
                <Input placeholder="如: 600519" />
              </Form.Item>

              <Form.Item name="name" label="股票名称">
                <Input placeholder="如: 贵州茅台" />
              </Form.Item>
            </>
          )}

          <Form.Item
            name="quantity"
            label="持仓数量"
            rules={[{ required: true, message: '请输入持仓数量' }]}
          >
            <InputNumber style={{ width: '100%' }} min={1} placeholder="股数" />
          </Form.Item>

          <Form.Item
            name="avg_cost"
            label="平均成本"
            rules={[{ required: true, message: '请输入成本价' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              precision={2}
              prefix="¥"
              placeholder="平均成本价"
            />
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
