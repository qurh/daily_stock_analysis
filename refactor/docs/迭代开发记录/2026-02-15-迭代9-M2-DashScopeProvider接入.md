# 迭代开发记录

迭代编号：`迭代9`  
日期：`2026-02-15`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 按 DashScope SDK 接口接入千问模型调用能力。
2. 保持既有 mock/openai-compatible provider 可用，不引入回归。
3. 明确重构后端专用环境变量，避免与原项目 `.env` 混用。

## 2. 计划范围（Plan）

1. 扩展 LLM provider 工厂，新增 DashScope provider。
2. 补齐 DashScope 配置项并接入 `create_app()`。
3. 用单测覆盖 key 校验与 SDK 调用参数，跑全量回归。
4. 更新 README、CHANGELOG、`.env.example`。

## 3. 实际完成（Done）

1. 新增 `DashScopeLLMProvider`（SDK 方式）：
   - 使用 `dashscope.Generation.call(...)`
   - 支持 `enable_thinking`
   - 失败状态返回明确错误
2. `create_llm_provider(...)` 新增 provider：
   - `dashscope`
   - `dashscope-sdk`
3. 新增配置项：
   - `REF_DASHSCOPE_API_KEY`
   - `REF_DASHSCOPE_BASE_HTTP_API_URL`
   - `REF_DASHSCOPE_ENABLE_THINKING`
4. 新增单测：
   - DashScope key 缺失校验
   - DashScope SDK 调用参数与响应解析
5. `.env.example` 顶部新增重构后端 `REF_*` 模板段。

## 4. 未完成项（Not Done）

1. 未执行真实 DashScope API 的外网 smoke（需用户在 `.env` 填入有效 key）。
2. 未增加 DashScope SDK 特有错误码分类统计。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/llm/provider.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/tests/unit/test_llm_provider.py`
   - `refactor/backend/tests/integration/test_real_llm_smoke.py`
   - `refactor/backend/pyproject.toml`
   - `refactor/backend/requirements-dev.txt`
2. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/backend/.env.example`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-15-迭代9-M2-DashScopeProvider接入.md`

## 6. 验证记录

1. 执行命令：
   - `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_llm_provider.py`
   - `PYTHONPATH=refactor/backend/src python3 -m pytest refactor/backend/tests/unit`
   - `cd refactor/backend && ./scripts/ci.sh`
   - `cd refactor/backend && REF_ENABLE_REAL_LLM_SMOKE=0 ./scripts/smoke-real-llm.sh`
2. 结果摘要：
   - provider 单测：通过
   - 后端单测：`19 passed`
   - CI：通过
   - smoke（禁用外呼）：`skip`
3. 是否达到验收标准：
   - 达到（DashScope provider 集成完成，回归通过）

## 7. 风险与问题

1. 风险描述：DashScope SDK 版本升级可能导致返回结构细节变化。
2. 影响范围：`DashScopeLLMProvider.generate()` 的字段解析。
3. 缓解措施：后续增加真实集成测试与错误码快照监控。

## 8. 关键决策

1. 决策内容：优先接入 DashScope SDK，而非仅走 OpenAI-compatible URL。
2. 决策原因：与用户指定的官方接口示例一致，便于启用思考模式。
3. 影响模块：LLM 抽象层、配置管理、集成测试。

## 9. 下迭代计划

1. 执行真实 DashScope smoke 并留档。
2. 增加 provider 级重试与限流策略。
3. 增加结构化输出能力（JSON schema）支撑后续策略模块。
