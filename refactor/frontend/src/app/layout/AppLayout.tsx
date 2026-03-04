import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { appRoutes } from "../router";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const currentRoute = appRoutes.find((route) => location.pathname.startsWith(route.path));

  return (
    <div className="app-shell">
      <header className="shell-header">
        <div className="brand-zone">
          <p className="eyebrow">每日股票分析重构版</p>
          <h1>M4 前端控制台</h1>
          <p className="header-subtitle">
            面向个人交易研究的统一工作台，覆盖对话、知识沉淀、流程编排、策略生命周期与回测闭环。
          </p>
          <div className="header-tags">
            <span>记忆增强对话</span>
            <span>知识库迭代</span>
            <span>策略与回测联动</span>
          </div>
        </div>
        <div className="route-pill">
          <span>当前模块</span>
          <strong>{currentRoute?.label ?? "控制台"}</strong>
          <small>{currentRoute?.subtitle ?? "统一工作台"}</small>
        </div>
      </header>

      <nav className="primary-nav" aria-label="主导航">
        {appRoutes.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          >
            <span>{route.label}</span>
            <small>{route.subtitle}</small>
          </NavLink>
        ))}
      </nav>

      <main className="page-frame">{children}</main>
    </div>
  );
}
