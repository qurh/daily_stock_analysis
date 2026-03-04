import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "./App";

describe("App shell", () => {
  it("renders Chinese console title and primary navigation", () => {
    render(
      <MemoryRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText(/M4 前端控制台/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /对话/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /知识库/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /编排/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /策略/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /回测/i })).toBeInTheDocument();
  });
});
