# 2026-03-04 迭代268 - M4 前端五大页面首版

迭代编号：`迭代268`  
日期：`2026-03-04`  
负责人：`Codex`

---

## 1. 本迭代目标

1. 完成 M4 要求的五大前端页面首版。
2. 打通前端与 `refactor/backend` `/api/v2` 核心接口联调能力。
3. 建立前端测试基线，覆盖关键交互路径。

## 2. 计划范围（Plan）

1. 重建应用壳层与路由：`Chat/Knowledge/Workflow/Strategy/Backtest`。
2. 建立统一 API 客户端与业务服务层，页面不直接拼接请求细节。
3. 补充页面交互测试与构建验证，更新 README 与 CHANGELOG。

## 3. 实际完成（Done）

1. 新增路由壳层与导航布局，完成五大页面首版 UI 与响应式适配。
2. 新增 API 基础层：`api.ts`、`types.ts`、`services/*`。
3. 完成页面级表单交互：
   - Chat：创建会话、发送消息、拉取消息
   - Knowledge：上传、优化、入库、查询、删除、检索
   - Workflow：启动、查询、取消、Trace 展示
   - Strategy：认知提炼/审核、策略提炼、发布/绑定/回滚、版本与绑定查询
   - Backtest：任务创建、详情查询、结果列表、聚合指标
4. 建立 Vitest + RTL 测试基线并通过。

## 4. 未完成项（Not Done）

1. 前端未接入 Agent 工具自动编排可视化能力（FR-AGT）。
2. 尚未补充更高层级的 E2E 联调自动化（当前以单测 + 手工联调为主）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/frontend/src/App.tsx`
   - `refactor/frontend/src/app/layout/AppLayout.tsx`
   - `refactor/frontend/src/app/router.tsx`
   - `refactor/frontend/src/pages/*.tsx`
   - `refactor/frontend/src/lib/api.ts`
   - `refactor/frontend/src/lib/services/*.ts`
   - `refactor/frontend/src/lib/types.ts`
   - `refactor/frontend/src/styles.css`
   - `refactor/frontend/src/**/*.test.tsx`
2. 文档路径：
   - `refactor/frontend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-frontend-five-pages.md`
3. 接口/配置变更：
   - 前端新增环境变量：`VITE_API_BASE_URL`（默认 `http://localhost:18000/api/v2`）。
   - 前端新增测试依赖：Vitest / Testing Library / jsdom。

## 6. 验证记录

1. 执行命令：
   - `cd refactor/frontend && npm test -- --run`
   - `cd refactor/frontend && npm run build`
2. 结果摘要：
   - 测试通过：`4 files, 7 tests passed`
   - 构建通过：`vite build success`
3. 是否达到验收标准：
   - 是。M4 前端五大页面首版与后端 API 联调入口已落地。

## 7. 风险与问题

1. 风险描述：Strategy 页面能力点较多，后续需要按真实业务流程补更细粒度权限与状态约束。
2. 影响范围：复杂操作链（发布闸门、绑定策略）在异常路径上的引导仍偏技术化。
3. 缓解措施：下一迭代补用户导向文案、错误分级展示、关键动作二次确认。

## 8. 关键决策

1. 决策内容：采用“统一 API 客户端 + 页面服务层”而非页面内直接 fetch。
2. 决策原因：降低页面耦合，便于后续替换 Agent 编排与鉴权逻辑。
3. 影响模块：`src/lib/api.ts`、`src/lib/services/*.ts`、所有页面组件。

## 9. 下迭代计划

1. 补 Agent 工具编排前端入口与可观测展示（对齐 FR-AGT）。
2. 增加 Workflow/Strategy/Backtest 页面关键流程测试用例。
3. 组织一次前后端联调验收并回写需求完成度文档。
