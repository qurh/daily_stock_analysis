import type { ReactElement } from "react";

import { BacktestPage } from "../pages/BacktestPage";
import { ChatPage } from "../pages/ChatPage";
import { KnowledgePage } from "../pages/KnowledgePage";
import { StrategyPage } from "../pages/StrategyPage";
import { WorkflowPage } from "../pages/WorkflowPage";

export type AppRoute = {
  path: string;
  label: string;
  subtitle: string;
  element: ReactElement;
};

export const appRoutes: AppRoute[] = [
  {
    path: "/chat",
    label: "对话",
    subtitle: "RAG + 记忆多轮交互",
    element: <ChatPage />,
  },
  {
    path: "/knowledge",
    label: "知识库",
    subtitle: "Markdown 处理与检索",
    element: <KnowledgePage />,
  },
  {
    path: "/workflow",
    label: "编排",
    subtitle: "流程执行与追踪",
    element: <WorkflowPage />,
  },
  {
    path: "/strategy",
    label: "策略",
    subtitle: "蒸馏、提取、发布、绑定",
    element: <StrategyPage />,
  },
  {
    path: "/backtest",
    label: "回测",
    subtitle: "任务、记录与聚合指标",
    element: <BacktestPage />,
  },
];
