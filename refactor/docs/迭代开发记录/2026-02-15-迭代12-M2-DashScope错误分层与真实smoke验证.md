# 迭代开发记录

迭代编号：`迭代12`  
日期：`2026-02-15`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 对 DashScope 调用失败进行错误码分层处理。
2. 在 Chat API 层返回结构化 LLM 错误信息。
3. 完成真实 DashScope smoke 验证并记录结果。

## 2. 计划范围（Plan）

1. 新增 provider 级结构化异常。
2. 新增 DashScope 错误分类映射。
3. 在 chat route 增加异常映射。
4. 增加单测并执行回归与真实 smoke。

## 3. 实际完成（Done）

1. 新增 `LLMProviderError`：
   - 字段：`provider/status_code/error_code/error_message/category/retryable`
2. DashScope provider 增加分层函数：
   - `rate_limit`
   - `upstream`
   - `auth`
   - `model_config`
   - `invalid_request`
   - `unknown`
3. Chat API 增加 provider 异常映射：
   - `rate_limit` -> HTTP `429`
   - 其他 -> HTTP `502`
   - detail 含 provider 错误码、分类、是否可重试
4. 真实 smoke 问题排查并修复：
   - 模型名修正为 `qwen-plus`
   - 脚本改为白名单加载 `.env` 关键键
   - 最终真实 smoke 通过

## 4. 未完成项（Not Done）

1. 暂未引入自动重试策略（当前仅分层与透传）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/src/app/llm/provider.py`
   - `refactor/backend/src/app/api/routes/chat.py`
   - `refactor/backend/scripts/smoke-real-llm.sh`
   - `refactor/backend/tests/unit/test_llm_provider.py`
   - `refactor/backend/tests/unit/test_chat_service.py`
   - `refactor/backend/tests/unit/test_smoke_script_env.py`
2. 文档路径：
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-15-迭代12-M2-DashScope错误分层与真实smoke验证.md`

## 6. 验证记录

1. 执行命令：
   - `PYTHONPATH=refactor/backend/src python3 -m pytest -q refactor/backend/tests/unit/test_llm_provider.py refactor/backend/tests/unit/test_chat_service.py`
   - `PYTHONPATH=refactor/backend/src python3 -m pytest refactor/backend/tests/unit`
   - `cd refactor/backend && ./scripts/ci.sh`
   - `cd refactor/backend && ./scripts/smoke-real-llm.sh`
2. 结果摘要：
   - 错误分层相关单测：通过
   - 后端单测：`23 passed`
   - CI：通过
   - 真实 smoke：通过
3. 是否达到验收标准：
   - 达到

## 7. 风险与问题

1. 风险描述：分类规则仍基于当前 DashScope 错误码模式，后续若平台调整命名需同步更新。
2. 缓解措施：已通过单测覆盖关键分类，后续可加生产日志监控异常码分布。

## 8. 关键决策

1. 决策内容：先做错误分层与透传，不立即引入自动重试。
2. 决策原因：先保证可观测与可判定，再做重试策略更稳妥。
3. 影响模块：LLM provider、Chat API、集成验证脚本。

## 9. 下迭代计划

1. 基于 `retryable` 引入 provider 级有限重试。
2. 增加 DashScope 错误码统计与告警。
