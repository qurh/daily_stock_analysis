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
  Switch,
  Tabs,
  message,
  InputNumber,
  Divider,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  BellOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { configApi } from '@/services/api'
import { ModelInfo } from '@/types'

const { TabPane } = Tabs
const { Option } = Select

export default function SettingsPage() {
  const [models, setModels] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modelModalVisible, setModelModalVisible] = useState(false)
  const [editingModel, setEditingModel] = useState<any>(null)

  const [form] = Form.useForm()

  // Load models
  const loadModels = useCallback(async () => {
    setLoading(true)
    try {
      const response = await configApi.getModels({})
      setModels(response.data || [])
    } catch (error) {
      console.error('Load models error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadModels()
  }, [loadModels])

  // Save model
  const handleSaveModel = async () => {
    try {
      const values = await form.validateFields()

      if (editingModel) {
        await configApi.updateModel(editingModel.id, values)
        message.success('模型已更新')
      } else {
        await configApi.createModel(values)
        message.success('模型已添加')
      }

      setModelModalVisible(false)
      setEditingModel(null)
      form.resetFields()
      loadModels()
    } catch (error) {
      console.error('Save model error:', error)
    }
  }

  // Test model
  const handleTestModel = async (modelId: number) => {
    try {
      const response = await configApi.testModel(modelId)
      if (response.data.success) {
        message.success('连接测试成功')
      } else {
        message.error('连接测试失败')
      }
    } catch (error) {
      message.error('连接测试失败')
    }
  }

  // Delete model
  const handleDeleteModel = async (modelId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个模型配置吗？',
      onOk: async () => {
        try {
          await configApi.deleteModel(modelId)
          message.success('模型已删除')
          loadModels()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const modelColumns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => {
        const providers: Record<string, { name: string; color: string }> = {
          google: { name: 'Google', color: 'blue' },
          openai: { name: 'OpenAI', color: 'green' },
          tongyi: { name: '阿里云', color: 'orange' },
          deepseek: { name: 'DeepSeek', color: 'purple' },
        }
        const p = providers[provider] || { name: provider, color: 'default' }
        return <Tag color={p.color}>{p.name}</Tag>
      },
    },
    {
      title: '模型 ID',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'default'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<ApiOutlined />}
            onClick={() => handleTestModel(record.id)}
          >
            测试
          </Button>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingModel(record)
              form.setFieldsValue({
                name: record.name,
                provider: record.provider,
                model: record.model,
                api_key: '',
                enabled: record.enabled,
                priority: record.priority,
              })
              setModelModalVisible(true)
            }}
          />
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteModel(record.id)}
          />
        </Space>
      ),
    },
  ]

  const providerOptions = [
    { value: 'google', label: 'Google Gemini' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'tongyi', label: '阿里云通义千问' },
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'doubao', label: '字节跳动豆包' },
    { value: 'ERNIE', label: '百度文心一言' },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Tabs defaultActiveKey="models">
        <TabPane
          tab={
            <span>
              <ApiOutlined /> AI 模型配置
            </span>
          }
          key="models"
        >
          <Card
            title="AI 模型管理"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditingModel(null)
                  form.resetFields()
                  setModelModalVisible(true)
                }}
              >
                添加模型
              </Button>
            }
          >
            <Table
              dataSource={models}
              columns={modelColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />

            <Divider />

            <h4>快速配置指南</h4>
            <Card size="small" style={{ marginBottom: 16 }}>
              <h5>Google Gemini</h5>
              <p>1. 访问 Google AI Studio: https://aistudio.google.com/</p>
              <p>2. 创建 API Key</p>
              <p>3. 在环境变量中设置 <code>GEMINI_API_KEY</code></p>
            </Card>

            <Card size="small" style={{ marginBottom: 16 }}>
              <h5>OpenAI / GPT-4</h5>
              <p>1. 访问 OpenAI Platform: https://platform.openai.com/</p>
              <p>2. 创建 API Key</p>
              <p>3. 设置 <code>OPENAI_API_KEY</code></p>
            </Card>

            <Card size="small">
              <h5>阿里云通义千问</h5>
              <p>1. 访问阿里云控制台: https://dashscope.console.aliyun.com/</p>
              <p>2. 创建 DashScope API Key</p>
              <p>3. 设置 <code>DASHSCOPE_API_KEY</code></p>
            </Card>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BellOutlined /> 通知设置
            </span>
          }
          key="notifications"
        >
          <Card title="通知渠道配置">
            <Form layout="vertical">
              <Form.Item label="企业微信">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Input placeholder="Corp ID" />
                  <Input.Password placeholder="Secret" />
                  <Input placeholder="Agent ID" />
                </Space>
              </Form.Item>

              <Form.Item label="Telegram">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Input placeholder="Bot Token" />
                  <Input placeholder="Chat ID" />
                </Space>
              </Form.Item>

              <Form.Item label="邮件">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Input placeholder="SMTP Host" />
                  <InputNumber placeholder="Port" style={{ width: '100%' }} />
                  <Input placeholder="Username" />
                  <Input.Password placeholder="Password" />
                </Space>
              </Form.Item>

              <Button type="primary">保存设置</Button>
            </Form>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <SafetyCertificateOutlined /> 系统设置
            </span>
          }
          key="system"
        >
          <Card title="系统配置">
            <Form layout="vertical">
              <Form.Item label="默认 AI 模型">
                <Select defaultValue="gemini-2.0-flash" style={{ width: 200 }}>
                  {models.filter(m => m.enabled).map(m => (
                    <Option key={m.id} value={m.id}>{m.name}</Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label="启用 RAG">
                <Switch defaultChecked />
                <span style={{ marginLeft: 8, color: '#999' }}>
                  启用后将自动检索知识库
                </span>
              </Form.Item>

              <Form.Item label="风险偏好">
                <Select defaultValue="moderate" style={{ width: 200 }}>
                  <Option value="conservative">保守</Option>
                  <Option value="moderate">中性</Option>
                  <Option value="aggressive">激进</Option>
                </Select>
              </Form.Item>

              <Form.Item label="每日复盘时间">
                <Input type="time" defaultValue="16:00" style={{ width: 150 }} />
              </Form.Item>

              <Button type="primary">保存设置</Button>
            </Form>
          </Card>
        </TabPane>
      </Tabs>

      {/* Model Modal */}
      <Modal
        title={editingModel ? '编辑模型' : '添加模型'}
        open={modelModalVisible}
        onOk={handleSaveModel}
        onCancel={() => {
          setModelModalVisible(false)
          setEditingModel(null)
          form.resetFields()
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="模型名称"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: Gemini 2.0 Flash" />
          </Form.Item>

          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择提供商" options={providerOptions} />
          </Form.Item>

          <Form.Item
            name="model"
            label="模型 ID"
            rules={[{ required: true }]}
          >
            <Input placeholder="如: gemini-2.0-flash" />
          </Form.Item>

          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder="留空则使用环境变量" />
          </Form.Item>

          <Form.Item name="priority" label="优先级" initialValue={100}>
            <InputNumber min={1} max={999} />
          </Form.Item>

          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
