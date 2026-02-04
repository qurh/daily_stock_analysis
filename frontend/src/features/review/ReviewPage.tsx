'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  List,
  Tag,
  Space,
  Button,
  DatePicker,
  Tabs,
 Statistic,
  Row,
  Col,
  message,
  Modal,
  Form,
  Input,
  Checkbox,
} from 'antd'
import {
  CalendarOutlined,
  FileTextOutlined,
  BulbOutlined,
  WarningOutlined,
  PlusOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { reviewApi } from '@/services/api'
import { DailyReviewResponse } from '@/types'

const { RangePicker } = DatePicker
const { TextArea } = Input
const { TabPane } = Tabs

export default function ReviewPage() {
  const [reviews, setReviews] = useState<DailyReviewResponse[]>([])
  const [selectedReview, setSelectedReview] = useState<DailyReviewResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ])

  const [form] = Form.useForm()

  // Load reviews
  const loadReviews = useCallback(async () => {
    setLoading(true)
    try {
      const [start, end] = dateRange
      const response = await reviewApi.getDailyReviews({
        start_date: start.format('YYYY-MM-DD'),
        end_date: end.format('YYYY-MM-DD'),
        limit: 100,
      })
      setReviews(response.data || [])
    } catch (error) {
      console.error('Load reviews error:', error)
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  useEffect(() => {
    loadReviews()
  }, [loadReviews])

  // Generate daily review
  const handleGenerateReview = async () => {
    try {
      const values = await form.validateFields()

      await reviewApi.generateDailyReview({
        date: values.date.format('YYYY-MM-DD'),
        market_overview: values.market_overview,
        hot_sectors: [],
        winning_trades: [],
        losing_trades: [],
        lessons_learned: values.lessons || [],
        knowledge_gained: [],
        tomorrow_focus: values.focus || [],
      })

      message.success('复盘已保存')
      setCreateModalVisible(false)
      form.resetFields()
      loadReviews()
    } catch (error) {
      console.error('Generate review error:', error)
    }
  }

  const stats = [
    {
      title: '复盘次数',
      value: reviews.length,
      icon: <FileTextOutlined />,
    },
    {
      title: '盈利交易',
      value: reviews.reduce((sum, r) => sum + (r.winning_trades?.length || 0), 0),
      icon: <BulbOutlined />,
    },
    {
      title: '亏损交易',
      value: reviews.reduce((sum, r) => sum + (r.losing_trades?.length || 0), 0),
      icon: <WarningOutlined />,
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>每日复盘</h2>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setDateRange([dates[0], dates[1]])
              }
            }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建复盘
          </Button>
        </Space>
      </div>

      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {stats.map(s => (
          <Col span={8} key={s.title}>
            <Card>
              <Statistic
                title={s.title}
                value={s.value}
                prefix={s.icon}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Review List */}
      <Tabs defaultActiveKey="list">
        <TabPane
          tab={
            <span>
              <CalendarOutlined /> 复盘列表
            </span>
          }
          key="list"
        >
          <List
            dataSource={reviews}
            loading={loading}
            renderItem={(review) => (
              <List.Item
                actions={[
                  <Button
                    type="link"
                    icon={<EyeOutlined />}
                    onClick={() => setSelectedReview(review)}
                  >
                    查看
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{review.date}</span>
                      <Tag color={review.winning_trades?.length > review.losing_trades?.length ? 'green' : 'red'}>
                        {review.winning_trades?.length || 0} 胜 / {review.losing_trades?.length || 0} 负
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <p style={{ margin: '4px 0', color: '#666' }}>
                        {review.market_overview?.slice(0, 100) || '暂无概述'}...
                      </p>
                      {review.lessons_learned && review.lessons_learned.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                          {review.lessons_learned.slice(0, 2).map((lesson, i) => (
                            <Tag key={i} color="blue">{lesson}</Tag>
                          ))}
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
            pagination={{ pageSize: 10 }}
          />
        </TabPane>

        <TabPane
          tab={
            <span>
              <BulbOutlined /> 教训总结
            </span>
          }
          key="lessons"
        >
          <Card title="从历史复盘中提取的教训">
            <List
              size="small"
              dataSource={reviews.flatMap(r => r.lessons_learned || [])}
              renderItem={(lesson, index) => (
                <List.Item>
                  <List.Item.Meta
                    title={`${Math.floor(index / 3) + 1}. ${lesson}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Review Detail Modal */}
      <Modal
        title={`${selectedReview?.date} 复盘详情`}
        open={!!selectedReview}
        onCancel={() => setSelectedReview(null)}
        footer={[
          <Button key="close" onClick={() => setSelectedReview(null)}>
            关闭
          </Button>,
          <Button
            key="export"
            type="primary"
            onClick={() => {
              if (selectedReview) {
                message.success('已导出到知识库')
              }
            }}
          >
            导出到知识库
          </Button>,
        ]}
        width={800}
      >
        {selectedReview && (
          <div className="review-detail">
            <h4>市场概述</h4>
            <p>{selectedReview.market_overview || '暂无'}</p>

            <h4>热点板块</h4>
            <div>
              {selectedReview.hot_sectors?.map((sector, i) => (
                <Tag key={i} color="blue">{sector.sector}</Tag>
              ))}
            </div>

            <h4>盈利交易</h4>
            <List
              size="small"
              dataSource={selectedReview.winning_trades || []}
              renderItem={(trade: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={trade.code || '未记录代码'}
                    description={`盈亏: ${trade.profit || 0}%`}
                  />
                </List.Item>
              )}
            />

            <h4>亏损交易</h4>
            <List
              size="small"
              dataSource={selectedReview.losing_trades || []}
              renderItem={(trade: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={trade.code || '未记录代码'}
                    description={`盈亏: ${trade.loss || 0}%`}
                  />
                </List.Item>
              )}
            />

            <h4>今日教训</h4>
            <List
              size="small"
              dataSource={selectedReview.lessons_learned || []}
              renderItem={(lesson) => (
                <List.Item>
                  <Tag color="orange">lesson</Tag> {lesson}
                </List.Item>
              )}
            />

            <h4>明日重点</h4>
            <div>
              {(selectedReview.tomorrow_focus || []).map((focus, i) => (
                <Tag key={i}>{focus}</Tag>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* Create Review Modal */}
      <Modal
        title="新建复盘"
        open={createModalVisible}
        onOk={handleGenerateReview}
        onCancel={() => setCreateModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="date"
            label="复盘日期"
            rules={[{ required: true }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="market_overview" label="市场概述">
            <TextArea rows={4} placeholder="描述今日大盘走势" />
          </Form.Item>

          <Form.Item name="lessons" label="今日教训">
            <Checkbox.Group>
              <Checkbox value="纪律">严格执行止损</Checkbox>
              <Checkbox value="仓位">控制仓位</Checkbox>
              <Checkbox value="情绪">保持冷静</Checkbox>
              <Checkbox value="复盘">坚持复盘</Checkbox>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item name="focus" label="明日重点">
            <Input placeholder="明日需要关注的股票或板块" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
