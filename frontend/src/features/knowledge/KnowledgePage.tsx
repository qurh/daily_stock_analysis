'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Layout,
  Tree,
  Button,
  Input,
  Card,
  Tag,
  Space,
  Modal,
  Form,
  message,
  Dropdown,
  Tabs,
} from 'antd'
import {
  PlusOutlined,
  FolderOutlined,
  FileOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  EyeOutlined,
  ImportOutlined,
} from '@ant-design/icons'
import { knowledgeApi } from '@/services/api'
import { Document, Category } from '@/types'

const { Sider, Content } = Layout
const { Search } = Input
const { TabPane } = Tabs

interface TreeNode {
  key: string
  title: string
  children?: TreeNode[]
  isCategory?: boolean
  categoryId?: number
  docId?: number
}

export default function KnowledgePage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [editorVisible, setEditorVisible] = useState(false)
  const [currentDoc, setCurrentDoc] = useState<Document | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)

  const [form] = Form.useForm()

  // Load categories and documents
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const docsRes = await knowledgeApi.listDocs({ limit: 1000 })

      // Build category tree from documents
      const catsMap = new Map<number, Category>()

      docsRes.data.documents.forEach((doc: Document) => {
        if (doc.category_id && !catsMap.has(doc.category_id)) {
          catsMap.set(doc.category_id, {
            id: doc.category_id,
            name: `分类 ${doc.category_id}`,
            slug: `category-${doc.category_id}`,
          })
        }
      })

      setCategories(Array.from(catsMap.values()))
      setDocuments(docsRes.data.documents)
    } catch (error) {
      console.error('Load data error:', error)
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Build tree data
  const treeData: TreeNode[] = useMemo(() => {
    const uncategorizedDocs = documents.filter(d => !d.category_id)
    return [
      {
        key: 'all',
        title: '全部文档',
        isCategory: false,
      },
      {
        key: 'uncategorized',
        title: '未分类',
        children: uncategorizedDocs.map(doc => ({
          key: `doc-${doc.id}`,
          title: doc.title,
          isCategory: false,
          docId: doc.id,
        })),
      },
      ...categories.map(cat => ({
        key: `cat-${cat.id}`,
        title: cat.name,
        isCategory: true,
        categoryId: cat.id,
        children: documents
          .filter(d => d.category_id === cat.id)
          .map(doc => ({
            key: `doc-${doc.id}`,
            title: doc.title,
            isCategory: false,
            docId: doc.id,
          })),
      })),
    ]
  }, [documents, categories])

  const handleSelect = (keys: React.Key[]) => {
    setSelectedNode(keys[0] as string)
  }

  const handleCreateDoc = () => {
    setCurrentDoc(null)
    form.resetFields()
    setEditorVisible(true)
  }

  const handleEditDoc = (doc: Document) => {
    setCurrentDoc(doc)
    form.setFieldsValue({
      title: doc.title,
      content: doc.content,
      tags: doc.tags,
    })
    setEditorVisible(true)
  }

  const handleSaveDoc = async () => {
    try {
      const values = await form.validateFields()

      if (currentDoc) {
        await knowledgeApi.updateDoc(currentDoc.id, values)
        message.success('文档已更新')
      } else {
        await knowledgeApi.createDoc({
          ...values,
          category_id: selectedCategory,
        })
        message.success('文档已创建')
      }

      setEditorVisible(false)
      loadData()
    } catch (error) {
      console.error('Save error:', error)
    }
  }

  const handleDeleteDoc = async (docId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这篇文档吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await knowledgeApi.deleteDoc(docId)
          message.success('文档已删除')
          loadData()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const handleSearch = async (value: string) => {
    setSearchQuery(value)
    if (!value.trim()) {
      loadData()
      return
    }

    try {
      const response = await knowledgeApi.search({ query: value })
      // Show search results
      message.info(`找到 ${response.data.results.length} 条结果`)
    } catch (error) {
      message.error('搜索失败')
    }
  }

  const selectedDoc = selectedNode?.startsWith('doc-')
    ? documents.find(d => d.id === parseInt(selectedNode.replace('doc-', '')))
    : null

  return (
    <Layout style={{ height: '100%' }}>
      {/* Sidebar */}
      <Sider width={280} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Search
              placeholder="搜索知识库..."
              allowClear
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 500 }}>文档分类</span>
              <Button type="text" size="small" icon={<PlusOutlined />}>
                新建分类
              </Button>
            </div>

            <Tree
              treeData={treeData}
              onSelect={handleSelect}
              selectedKeys={selectedNode ? [selectedNode] : []}
              showIcon
              blockNode
            />
          </Space>
        </div>
      </Sider>

      {/* Content */}
      <Content style={{ padding: '0 24px', overflow: 'auto' }}>
        {selectedDoc ? (
          <div className="document-viewer">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>{selectedDoc.title}</h2>
              <Space>
                <Button icon={<EditOutlined />} onClick={() => handleEditDoc(selectedDoc)}>
                  编辑
                </Button>
                <Dropdown
                  menu={{
                    items: [
                      { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
                    ],
                    onClick: ({ key }) => {
                      if (key === 'delete') handleDeleteDoc(selectedDoc.id)
                    },
                  }}
                >
                  <Button icon={<MoreOutlined />} />
                </Dropdown>
              </Space>
            </div>

            <div style={{ marginBottom: 16 }}>
              {selectedDoc.tags.map(tag => (
                <Tag key={tag}>{tag}</Tag>
              ))}
            </div>

            <div className="document-content" style={{ lineHeight: 1.8 }}>
              {selectedDoc.content}
            </div>
          </div>
        ) : (
          <div style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3>最近文档</h3>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateDoc}>
                新建文档
              </Button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
              {documents.slice(0, 10).map(doc => (
                <Card
                  key={doc.id}
                  hoverable
                  onClick={() => setSelectedNode(`doc-${doc.id}`)}
                  actions={[
                    <EditOutlined key="edit" onClick={(e) => { e.stopPropagation(); handleEditDoc(doc); }} />,
                    <DeleteOutlined key="delete" onClick={(e) => { e.stopPropagation(); handleDeleteDoc(doc.id); }} />,
                  ]}
                >
                  <Card.Meta
                    title={doc.title}
                    description={
                      <div>
                        <p style={{ color: '#999', fontSize: 12 }}>
                          更新于 {new Date(doc.updated_at || doc.created_at).toLocaleDateString()}
                        </p>
                        <div>
                          {doc.tags.slice(0, 3).map(tag => (
                            <Tag key={tag} color="blue">{tag}</Tag>
                          ))}
                        </div>
                      </div>
                    }
                  />
                </Card>
              ))}
            </div>
          </div>
        )}
      </Content>

      {/* Editor Modal */}
      <Modal
        title={currentDoc ? '编辑文档' : '新建文档'}
        open={editorVisible}
        onOk={handleSaveDoc}
        onCancel={() => setEditorVisible(false)}
        width={900}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="输入文档标题" />
          </Form.Item>

          <Form.Item name="content" label="内容">
            <Input.TextArea rows={15} placeholder="使用 Markdown 格式编写内容..." />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Input placeholder="用逗号分隔多个标签" />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  )
}
