import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Stock Analysis System',
  description: 'AI-driven stock analysis and knowledge management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  )
}
