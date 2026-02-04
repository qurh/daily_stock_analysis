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
  Switch,
  message,
  Tabs,
  Badge,
  Statistic,
  Row,
  Col,
  Timeline,
} from 'antd'
import {
  PlusOutlined,
  BellOutlined,
  SettingOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { monitorApi, marketApi } from '@/services/api'
import { Alert } from '@/types'

const { Search } = Input
const { TabPane } = Tabs
const { Option } = Select

export default function MonitorPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [selectedCodes, setSelectedCodes] = useState<string[]>([])
  const [quotes, setQuotes] = useState<Record<string, any>>({})

  const [form] = Form.useForm()

  // Load alerts
  const loadAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const response = await monitorApi.listAlerts({ active_only: false })
      setAlerts(response.data.alerts || [])
    } catch (error) {
      console.error('Load alerts error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load alert history
  const loadHistory = useCallback(async () => {
    try {
      const response = await monitorApi.getHistory({ limit: 50 })
      setHistory(response.data.history || [])
    } catch (error) {
      console.error('Load history error:', error)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
    loadHistory()
  }, [loadAlerts, loadHistory])

  // Load quotes for alert stocks
  useEffect(() => {
    const codes = alerts.filter(a => a.code).map(a => a.code!)
    if (codes.length > 0 && JSON.stringify(codes) !== JSON.stringify(selectedCodes)) {
      setSelectedCodes(codes)
      loadQuotes(codes)
    }
  }, [alerts])

  const loadQuotes = async (codes: string[]) => {
    try {
      const response = await marketApi.getQuotes(codes)
      const quotesMap: Record<string, any> = {}
      response.data.forEach((q: any) => {
        quotesMap[q.code] = q
      })
      setQuotes(quotesMap)
    } catch (error) {
      console.error('Load quotes error:', error)
    }
  }

  // Create alert
  const handleCreateAlert = async () => {
    try {
      const values = await form.validateFields()

      await monitorApi.createAlert({
        code: values.code || null,
        alert_type: values.alert_type,
        threshold: values.threshold,
        direction: values.direction,
        enabled: values.enabled,
        notify_channels: values.notify_channels || [],
      })

      message.success('告警已创建')
      setCreateModalVisible(false)
      form.resetFields()
      loadAlerts()
    } catch (error) {
      console.error('Create alert error:', error)
    }
  }

  // Toggle alert
  const handleToggleAlert = async (alert: Alert) => {
    try {
      await monitorApi.updateAlert(alert.id, { enabled: !alert.enabled })
      message.success(alert.enabled ? '告警已禁用' : '告警已启用')
      loadAlerts()
    } catch (error) {
      message.error('操作失败')
    }
  }

  // Delete alert
  const handleDeleteAlert = async (alertId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个告警吗？',
      onOk: async () => {
        try {
          await monitorApi.deleteAlert(alertId)
          message.success('告警已删除')
          loadAlerts()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const alertColumns = [
    {
      title: '股票',
      dataIndex: 'code',
      key: 'code',
      render: (code: string) => code || '全市场',
    },
    {
      title: '类型',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (type: string) => {
        const config: Record<string, { text: string; color: string }> = {
          price_above: { text: '价格高于', color: 'red' },
          price_below: { text: '价格低于', color: 'green' },
          pct_chg_above: { text: '涨跌幅超过', color: 'orange' },
        }
        const c = config[type] || { text: type, color: 'default' }
        return <Tag color={c.color}>{c.text}</Tag>
      },
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (val: number, record: Alert) => (
        <span>
          {val}{record.alert_type === 'pct_chg_above' ? '%' : '¥'}
        </span>
      ),
    },
    {
      title: '当前价格',
      key: 'current_price',
      render: (_: any, record: Alert) => {
        if (!record.code) return '-'
        const quote = quotes[record.code]
        return quote ? (
          <span style={{ color: quote.pct_chg >= 0 ? '#ff4d4f' : '#52c41a' }}>
            ¥{quote.price.toFixed(2)}
          </span>
        ) : '-'
      },
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Badge status={enabled ? 'success' : 'default'} text={enabled ? '启用' : '禁用'} />
      ),
    },
    {
      title: '触发次数',
      dataIndex: 'trigger_count',
      key: 'trigger_count',
    },
    {
      title: '最后触发',
      dataIndex: 'last_triggered',
      key: 'last_triggered',
      render: (time: string) => time ? new Date(time).toLocaleString() : '从未',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Alert) => (
        <Space>
          <Switch
            size="small"
            checked={record.enabled}
            onChange={() => handleToggleAlert(record)}
          />
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteAlert(record.id)}
          />
        </Space>
      ),
    },
  ]

  const alertStats = [
    { title: '活跃告警', value: alerts.filter(a => a.enabled).length, color: '#1890ff' },
    { title: '今日触发', value: history.filter(h => {
      const today = new Date().toDateString()
      return new Date(h.triggered_at).toDateString() === today
    }).length, color: '#52c41a' },
    { title: '总触发次数', value: alerts.reduce((sum, a) => sum + a.trigger_count, 0), color: '#faad14' },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {alertStats.map(stat => (
          <Col span={8} key={stat.title}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Tabs defaultActiveKey="alerts">
        <TabPane
          tab={
            <span>
              <BellOutlined /> 告警列表
            </span>
          }
          key="alerts"
        >
          <Card
            title="价格告警"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                新建告警
              </Button>
            }
          >
            <Table
              dataSource={alerts}
              columns={alertColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <SettingOutlined /> 告警历史
            </span>
          }
          key="history"
        >
          <Card title="最近触发记录">
            <Timeline
              items={history.map(h => ({
                color: h.alert_type === 'price_above' ? 'red' : 'green',
                children: (
                  <div>
                    <p style={{ margin: 0, fontWeight: 500 }}>
                      {h.code || '全市场'} - {h.alert_type}
                    </p>
                    <p style={{ margin: 0, color: '#999' }}>
                      {h.message}
                    </p>
                    <p style={{ margin: 0, fontSize: 12, color: '#999' }}>
                      {new Date(h.triggered_at).toLocaleString()}
                    </p>
                  </div>
                ),
              }))}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Create Alert Modal */}
      <Modal
        title="新建告警"
        open={createModalVisible}
        onOk={handleCreateAlert}
        onCancel={() => setCreateModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="股票代码">
            <Input placeholder="留空表示监控全市场" />
          </Form.Item>

          <Form.Item
            name="alert_type"
            label="告警类型"
            rules={[{ required: true }]}
            initialValue="price_above"
          >
            <Select>
              <Option value="price_above">价格高于</Option>
              <Option value="price_below">价格低于</Option>
              <Option value="pct_chg_above">涨跌幅超过 X%</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="threshold"
            label="阈值"
            rules={[{ required: true }]}
          >
            <InputNumber style={{ width: '100%' }} precision={2} />
          </Form.Item>

          <Form.Item
            name="direction"
            label="方向"
            initialValue="above"
          >
            <Select>
              <Option value="above">高于</Option>
              <Option value="below">低于</Option>
            </Select>
          </Form.Item>

          <Form.Item name="notify_channels" label="通知渠道">
            <Select mode="multiple" placeholder="选择通知方式">
              <Option value="wechat">企业微信</Option>
              <Option value="telegram">Telegram</Option>
              <Option value="email">邮件</Option>
            </Select>
          </Form.Item>

          <Form.Item name="enabled" label="启用状态" valuePropName="checked" initialValue>
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
