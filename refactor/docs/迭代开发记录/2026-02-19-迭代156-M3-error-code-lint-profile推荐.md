# 迭代开发记录

迭代编号：`迭代156`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 当 lint profile 拼写错误时提供推荐 profile，缩短排障时间。
2. 保持 lint 校验器与 overrides 校验器错误输出格式一致。
3. 不改变现有错误码，只增强错误上下文信息。

## 2. 计划范围（Plan）

1. 先补失败测试：两个校验器在 typo profile 场景返回 `suggested_profiles`。
2. 引入模糊匹配逻辑并写入 JSON 错误上下文。
3. 更新 README、CHANGELOG、版本号和迭代记录。

## 3. 实际完成（Done）

1. TDD Red：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增失败约束：
     - lint 校验器未知 profile 时返回 `suggested_profiles`
     - overrides 校验器未知 profile 时返回 `suggested_profiles`
2. TDD Green：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
     - 新增 `difflib.get_close_matches` 推荐逻辑
     - `error_code_metadata_lint_profile_not_found` 上下文新增：
       - `available_profiles`
       - `suggested_profiles`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
     - 同步推荐逻辑与上下文字段
3. 文档与版本：
   - `refactor/backend/README.md` 增加推荐字段说明
   - `refactor/docs/CHANGELOG.md` 新增 `0.3.141-m3-error-code-lint-profile-suggestion`
   - `refactor/backend/src/app/main.py` 版本升级至 `0.3.141-m3-error-code-lint-profile-suggestion`

## 4. 未完成项（Not Done）

1. 推荐逻辑当前仅基于字符串相似度，未引入业务优先级。
2. 尚未将推荐结果接入 chatbot 交互提示层。

## 5. 代码与文档变更

1. 脚本：
   - `refactor/backend/scripts/validate-validator-error-code-metadata-lint.py`
   - `refactor/backend/scripts/validate-validator-error-code-metadata-overrides.py`
2. 测试：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代156-M3-error-code-lint-profile推荐.md`
4. 版本：
   - `refactor/backend/src/app/main.py`

## 6. 验证记录

1. Red 阶段：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -k "suggests_nearby_profile or suggests_nearby_lint_profile" -q`
   - 结果：预期失败（无 `suggested_profiles` 字段）。
2. Green 阶段：
   - 同命令回归。
   - 结果：通过。
3. 回归验证：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
4. 是否达到验收标准：
   - 达到（未知 profile 报错可给出可执行推荐）。

## 7. 风险与问题

1. 风险描述：模糊匹配可能在 profile 名称非常接近时给出多个候选。
2. 影响范围：错误提示可读性。
3. 缓解措施：保留 `available_profiles` 全量列表供人工确认。

## 8. 关键决策

1. 决策内容：不新增错误码，仅增强 `context` 字段。
2. 决策原因：保持上游错误码兼容，降低集成改造成本。
3. 影响模块：两类校验器 JSON 错误消费方。

## 9. 下迭代计划

1. 在错误消息中直接附带推荐 profile（human-readable 文本）。
2. 增加 profile 拼写修复建议的 CLI 输出模式。
3. 评估将推荐逻辑抽取为共用工具模块，减少脚本重复。
