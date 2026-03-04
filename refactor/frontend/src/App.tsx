import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./app/layout/AppLayout";
import { appRoutes } from "./app/router";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate replace to="/chat" />} />
        {appRoutes.map((route) => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}
        <Route path="*" element={<Navigate replace to="/chat" />} />
      </Routes>
    </AppLayout>
  );
}
