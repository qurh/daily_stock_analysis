'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, Select, Tooltip, Modal, message } from 'antd'
import {
  SendOutlined,
  ClearOutlined,
  BulbOutlined,
  DatabaseOutlined,
  ImportOutlined,
} from '@ant-design/icons'
import { useChatStore } from '@/stores/chatStore'
import { chatApi } from '@/services/api'
import { ModelInfo } from '@/types'

const { TextArea } = Input

export default function ChatPage() {
  const {
    messages,
    currentModel,
    isLoading,
    useRag,
    sendMessage,
    setModel,
    toggleRag,
    clearHistory,
  } = useChatStore()

  const [inputValue, setInputValue] = useState('')
  const [models, setModels] = useState<ModelInfo[]>([])
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [selectedMessageId, setSelectedMessageId] = useState<string>('')
  const [importTitle, setImportTitle] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadModels()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadModels = async () => {
    try {
      const response = await chatApi.getModels()
      setModels(response.data)
    } catch (error) {
      console.error('Load models error:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const message = inputValue.trim()
    setInputValue('')
    await sendMessage(message)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleImport = async () => {
    if (!importTitle.trim()) {
      message.warning('请输入标题')
      return
    }

    try {
      await chatApi.importToKnowledge({
        content: messages.find(m => m.id === selectedMessageId)?.content,
        title: importTitle,
      })
      message.success('已导入知识库')
      setImportModalVisible(false)
      setImportTitle('')
    } catch (error) {
      message.error('导入失败')
    }
  }

  const openImportModal = (messageId: string) => {
    setSelectedMessageId(messageId)
    setImportModalVisible(true)
  }

  const modelOptions = models.map(m => ({
    label: m.name,
    value: m.id,
    disabled: !m.enabled,
  }))

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <h2 className="text-lg font-semibold m-0">AI 对话</h2>
        <div className="flex items-center gap-2">
          <Select
            value={currentModel}
            onChange={setModel}
            options={modelOptions}
            style={{ width: 180 }}
            placeholder="选择模型"
          />
          <Tooltip title={useRag ? 'RAG 已启用' : 'RAG 已禁用'}>
            <Button
              type={useRag ? 'primary' : 'default'}
              icon={<DatabaseOutlined />}
              onClick={toggleRag}
            >
              RAG
            </Button>
          </Tooltip>
          <Tooltip title="清空对话">
            <Button
              icon={<ClearOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: '确认清空',
                  content: '确定要清空所有对话吗？',
                  onOk: clearHistory,
                })
              }}
            >
              清空
            </Button>
          </Tooltip>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <BulbOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>开始输入，与 AI 助手对话</p>
            <p className="text-sm">支持询问股票分析、市场观点、策略建议等</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>

              {message.role === 'assistant' && (
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                  <span>{message.model}</span>
                  <Button
                    type="text"
                    size="small"
                    icon={<ImportOutlined />}
                    onClick={() => openImportModal(message.id)}
                  >
                    导入知识库
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <span className="animate-pulse">AI 思考中...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="flex-1"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading}
            disabled={!inputValue.trim()}
          >
            发送
          </Button>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          按 Enter 发送，Shift+Enter 换行 |{' '}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              setInputValue('帮我分析一下贵州茅台最近的趋势')
            }}
          >
            分析贵州茅台
          </a>
          {' | '}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              setInputValue('什么是均线金叉？')
            }}
          >
            什么是均线金叉？
          </a>
        </div>
      </div>

      {/* Import Modal */}
      <Modal
        title="导入知识库"
        open={importModalVisible}
        onOk={handleImport}
        onCancel={() => setImportModalVisible(false)}
      >
        <div className="space-y-4">
          <div>
            <label className="block mb-2">标题</label>
            <Input
              value={importTitle}
              onChange={(e) => setImportTitle(e.target.value)}
              placeholder="输入文档标题"
            />
          </div>
          <p className="text-sm text-gray-500">
            内容将从对话中自动提取
          </p>
        </div>
      </Modal>
    </div>
  )
}
