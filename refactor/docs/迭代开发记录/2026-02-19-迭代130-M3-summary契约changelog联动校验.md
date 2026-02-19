# 迭代开发记录

迭代编号：`迭代130`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 建立 summary 契约与 changelog 的联动校验。
2. 确保发布记录中显式声明当前 `schema_version`。

## 2. 计划范围（Plan）

1. 先补失败测试，定义 changelog 联动校验行为。
2. 新增校验脚本并接入 `scripts/ci.sh`。
3. 同步 README / CHANGELOG / 版本号。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败场景：
     - CI 必须包含 `validate-summary-contract-changelog.py`
     - 脚本默认文件必须通过
     - 缺失 schema version note 时必须失败
2. TDD Green：
   - 新增脚本：
     - `refactor/backend/scripts/validate-summary-contract-changelog.py`
   - 校验项：
     - latest changelog 版本号 == `src/app/main.py` 版本号
     - latest changelog entry 必须包含 `Summary schema version: <version>`
     - 版本值来自 `strict-gate-summary.schema.json` 的 `schema_version.const`
   - CI 接入：
     - `refactor/backend/scripts/ci.sh` 新增执行该脚本
3. 文档与版本：
   - `refactor/backend/README.md` 增加 changelog 联动校验命令说明。
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.115-m3-summary-contract-changelog-link`。
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.115-m3-summary-contract-changelog-link`。

## 4. 未完成项（Not Done）

1. 暂未自动检查 changelog 日期格式与时区。
2. 暂未增加 changelog entry 模板自动生成。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-summary-contract-changelog.py`
   - `refactor/backend/scripts/ci.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代130-M3-summary契约changelog联动校验.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "summary_contract_changelog_validator_script or ci_script_invokes_prometheus_rules_check" -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 联动校验新增用例通过
   - 后端全量 CI 通过
3. 是否达到验收标准：
   - 达到（schema_version 与 changelog 发布记录建立强关联）

## 7. 风险与问题

1. 风险描述：changelog 文案格式若变更，脚本匹配规则可能失效。
2. 影响范围：CI 可用性。
3. 缓解措施：固定 `Summary schema version:` 关键短语并通过测试保护。

## 8. 关键决策

1. 决策内容：采用“固定标记行”而不是自由文本解析。
2. 决策原因：可维护、可测试、可自动化。
3. 影响模块：发布记录规范与 CI 契约门禁。

## 9. 下迭代计划

1. 增加 changelog 版本语义校验（#patch/#minor/#major 标签一致性）。
2. 增加 summary example 自动刷新命令。
3. 将契约校验结果输出到 CI artifact。
