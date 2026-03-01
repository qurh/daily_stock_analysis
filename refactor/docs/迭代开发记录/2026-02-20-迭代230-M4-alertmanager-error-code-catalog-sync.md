# 迭代开发记录

迭代编号：`迭代230`  
日期：`2026-02-20`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 将 `validate-alertmanager-route-consistency.py` 的错误码纳入统一 `validator-error-codes` 治理链路。
2. 保持 `--strict-descriptions` 门禁通过，避免新分组引入占位描述。

## 2. 计划范围（Plan）

1. 按 TDD 新增 catalog 覆盖测试并先跑 RED。
2. 扩展 `sync-validator-error-codes.py` 注册表，加入 alertmanager 路由一致性校验器。
3. 补齐 schema、metadata overrides、README、CHANGELOG、版本号并完成回归验证。

## 3. 实际完成（Done）

1. 测试先行（RED->GREEN）：
   - 新增 `test_validator_error_code_catalog_covers_alertmanager_route_consistency_codes`，
     初始失败（catalog 缺少该分组），实现后通过。
2. 治理链路打通：
   - `sync-validator-error-codes.py` 新增分组注册：
     `alertmanager_route_consistency -> validate-alertmanager-route-consistency.py`。
   - `validator-error-codes.schema.json` 将 `alertmanager_route_consistency` 纳入 required。
   - `validator-error-codes.json` 同步生成全部 `alertmanager_route_consistency_*` 条目。
3. 严格描述门禁修复：
   - `validator-error-code-metadata-overrides.json` 补齐 `alertmanager_route_consistency_*`
     的 description/severity/remediation，确保通过 `--strict-descriptions`。
4. 文档与版本：
   - `refactor/backend/README.md` 补充新分组说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.4.14` 条目。
   - `refactor/backend/src/app/main.py` 版本升级为
     `0.4.14-m4-alertmanager-error-code-catalog-sync`。

## 4. 未完成项（Not Done）

1. `validate-notification-retry-runbook.py` 尚未接入统一 `VALIDATOR_ERROR_CODES + --json-errors` 合同。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/sync-validator-error-codes.py`
   - `refactor/backend/config/schemas/validator-error-codes.schema.json`
   - `refactor/backend/config/validator-error-codes.json`
   - `refactor/backend/config/validator-error-code-metadata-overrides.json`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-20-迭代230-M4-alertmanager-error-code-catalog-sync.md`

## 6. 验证记录

1. RED：
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "covers_alertmanager_route_consistency_codes"`
   - 结果：失败（预期，catalog 缺分组）。
2. GREEN 与回归：
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --strict-descriptions`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_ci_prometheus_rules_check.py -k "validator_error_code_catalog_exists_and_has_prefix_groups or validator_error_code_catalog_schema_exists_and_has_required_fields or validator_scripts_expose_error_code_registries or validator_error_code_catalog_covers_all_script_error_codes or covers_alertmanager_route_consistency_codes"`
   - `cd refactor/backend && PYTHONPATH=src python3 -m pytest -q tests/unit/test_alertmanager_route_consistency.py tests/unit/test_ci_prometheus_rules_check.py`
   - `cd refactor/backend && python3 -m py_compile scripts/sync-validator-error-codes.py tests/unit/test_ci_prometheus_rules_check.py scripts/validate-alertmanager-route-consistency.py`
   - `cd refactor/backend && python3 scripts/sync-validator-error-codes.py --check --strict-descriptions`
   - `cd refactor/backend && python3 scripts/validate-validator-error-code-catalog.py && python3 scripts/validate-validator-error-code-metadata-overrides.py`
   - 结果：通过。

## 7. 风险与问题

1. 风险描述：新增分组依赖 metadata overrides 质量；若文案回退到占位符会触发 CI 严格门禁失败。
2. 缓解措施：继续使用 `sync-validator-error-codes.py --check --strict-descriptions` 作为固定门禁。

## 8. 关键决策

1. 决策内容：先将 alertmanager 路由一致性校验器并入统一 error-code catalog，再扩展其他 M4 校验器。
2. 决策原因：该校验器已具备 `VALIDATOR_ERROR_CODES` 与 `--json-errors` 能力，接入成本最低、收益立即可见。
3. 影响模块：CI 校验链路、错误码治理与运维自动化消费路径。

## 9. 下迭代计划

1. 评估并实现 `validate-notification-retry-runbook.py` 的错误码注册与 `--json-errors`。
2. 将其并入 `validator-error-codes` catalog，保持治理链路一致。
