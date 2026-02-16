# 迭代开发记录

迭代编号：`迭代7`  
日期：`2026-02-15`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 在保留 prompt 绑定机制前提下接入真实 LLM provider。
2. 保持默认 `mock-llm` 路径不变，避免影响本地离线开发与测试。
3. 为后续多 provider 扩展补齐基础运行时配置。

## 2. 计划范围（Plan）

1. 扩展 `app/llm/provider.py` 支持 OpenAI-compatible provider。
2. 补齐配置项并在 `create_app()` 注入 provider 参数。
3. 使用新增单测覆盖 API key 校验与请求载荷，回归全量单测。

## 3. 实际完成（Done）

1. 新增 `OpenAICompatibleLLMProvider`，支持 `/chat/completions` 调用与响应解析。
2. 扩展 `create_llm_provider(...)`：
   - 支持 `openai-compatible` / `openai`
   - 增加 `api_key/base_url/timeout_sec` 参数
   - 缺少 API key 时抛出明确异常
3. 扩展运行时配置：
   - `REF_LLM_API_KEY`
   - `REF_LLM_BASE_URL`
   - `REF_LLM_TIMEOUT_SEC`
4. `create_app()` 增加 provider 参数透传，默认 mock 路径保持不变。
5. 新增测试文件 `test_llm_provider.py` 并通过回归。

## 4. 未完成项（Not Done）

1. 外部 LLM 调用重试、退避、限流与熔断策略尚未接入。
2. 多 provider（如本地模型/第三方代理）适配器尚未实现。
3. 真实调用链路的观测字段（request id、latency buckets）尚未标准化。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/llm/provider.py`
   - `refactor/backend/src/app/core/settings.py`
   - `refactor/backend/src/app/main.py`
   - `refactor/backend/tests/unit/test_llm_provider.py`
2. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-15-迭代7-M2-真实LLMProvider接入.md`
3. 接口/配置变更：
   - 新增环境变量：`REF_LLM_API_KEY`、`REF_LLM_BASE_URL`、`REF_LLM_TIMEOUT_SEC`
   - 应用版本更新：`0.2.3-m2-llm-provider`

## 6. 验证记录

1. 执行命令：
   - `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_llm_provider.py`
   - `PYTHONPATH=refactor/backend/src python3 -m pytest refactor/backend/tests/unit`
   - `cd refactor/backend && ./scripts/ci.sh`
2. 结果摘要：
   - provider 专项测试：通过
   - 后端单测全量：`16 passed`
   - CI：`black + isort + flake8 + pytest` 全通过
3. 是否达到验收标准：
   - 本迭代目标达到（真实 provider 基础接入完成，默认 mock 行为保持稳定）

## 7. 风险与问题

1. 风险描述：真实调用仍为单请求直连模式，暂未覆盖网络抖动和速率限制场景。
2. 影响范围：在高并发或外部 API 波动时可能出现响应不稳定。
3. 缓解措施：下一迭代优先加入超时分类、重试策略与降级回退。

## 8. 关键决策

1. 决策内容：优先接入 OpenAI-compatible 标准协议，而非绑定单一云厂商 SDK。
2. 决策原因：统一协议便于后续替换与多 provider 并存。
3. 影响模块：配置管理、LLM 抽象层、Chat 生成链路。

## 9. 下迭代计划

1. 增加 provider 调用重试、限流、错误分类与降级策略。
2. 增加端到端真实 provider 集成测试（可选环境变量控制）。
3. 抽象工具调用与 structured output 能力，为分析流程编排做准备。
