import { create } from 'zustand'
import { chatApi, chatApi as api } from '@/services/api'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  model?: string
  sources?: any[]
  timestamp: number
}

interface ChatState {
  messages: Message[]
  currentModel: string
  isLoading: boolean
  useRag: boolean

  // Actions
  sendMessage: (content: string) => Promise<void>
  setModel: (model: string) => void
  toggleRag: () => void
  clearHistory: () => void
  importToKnowledge: (messageId: string, title: string) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  currentModel: 'gemini-2.0-flash',
  isLoading: false,
  useRag: true,

  sendMessage: async (content: string) => {
    const { messages, currentModel, useRag } = get()

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }

    set({ messages: [...messages, userMessage], isLoading: true })

    try {
      const response = await chatApi.send({
        message: content,
        context: messages.slice(-10).map(m => ({
          role: m.role,
          content: m.content,
        })),
        use_rag: useRag,
        model: currentModel,
      })

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.data.response.message.content,
        model: response.data.model,
        sources: response.data.sources,
        timestamp: Date.now(),
      }

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }))
    } catch (error) {
      console.error('Send message error:', error)
      set({ isLoading: false })

      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        timestamp: Date.now(),
      }

      set((state) => ({
        messages: [...state.messages, errorMessage],
      }))
    }
  },

  setModel: (model: string) => {
    set({ currentModel: model })
  },

  toggleRag: () => {
    set((state) => ({ useRag: !state.useRag }))
  },

  clearHistory: () => {
    set({ messages: [] })
  },

  importToKnowledge: async (messageId: string, title: string) => {
    const message = get().messages.find(m => m.id === messageId)
    if (!message) return

    try {
      await chatApi.importToKnowledge({
        content: message.content,
        title,
      })
    } catch (error) {
      console.error('Import error:', error)
      throw error
    }
  },
}))
