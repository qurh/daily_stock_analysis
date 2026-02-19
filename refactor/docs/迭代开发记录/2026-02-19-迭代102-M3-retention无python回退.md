# 迭代开发记录

迭代编号：`迭代102`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 修复 retention-days 清理对 python 解释器的硬依赖问题。
2. 在无 python 或 python 执行失败场景下，确保仍可完成按天清理。
3. 保持现有复合轮转能力与行为兼容。

## 2. 计划范围（Plan）

1. 先补失败测试，模拟 `python3/python` 不可用并验证清理仍成功。
2. 增强脚本的 cutoff 时间计算逻辑，加入 `date` fallback。
3. 同步版本、README、CHANGELOG 与迭代记录。

## 3. 实际完成（Done）

1. 测试增强：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
   - 新增用例：python 不可用时，retention-days 通过 `date` fallback 仍可生效。
2. 脚本增强：
   - `refactor/backend/scripts/validate-promtool-installer-config.sh`
   - retention-days cutoff 计算策略改为：
     - 优先 `python3/python`
     - 失败则回退 `date -d`（GNU）
     - 再回退 `date -v`（BSD）
   - 避免 python 命令存在但返回非零时触发脚本整体失败。
3. 文档与版本：
   - `refactor/backend/src/app/main.py` 版本升级：`0.3.87-m3-promtool-retention-fallback`
   - `refactor/backend/README.md` 增加 retention fallback 说明。
   - `refactor/docs/CHANGELOG.md` 增加本次变更记录。

## 4. 未完成项（Not Done）

1. 暂未对极端精简系统（python/date 都不可用）引入第三种时间计算后备方案。
2. 暂未对高频写入下轮转性能做基准测试。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/validate-promtool-installer-config.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代102-M3-retention无python回退.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 定向测试：通过（28 passed）
   - CI 脚本：通过
3. 是否达到验收标准：
   - 达到（retention-days 在无 python 场景可降级执行）

## 7. 风险与问题

1. 风险描述：`date` 在不同系统实现差异较大，已做 GNU/BSD 双分支兼容但仍需长期观察。
2. 影响范围：soft 审计 retention-days 的跨平台稳定性。
3. 缓解措施：继续通过 CI 与回归测试覆盖常见平台差异。

## 8. 关键决策

1. 决策内容：retention cutoff 采用“python优先 + date双实现回退”策略。
2. 决策原因：保证在更多执行环境下可用，降低软依赖导致的门禁失败。
3. 影响模块：promtool soft 审计复合轮转策略。

## 9. 下迭代计划

1. 评估在 `/api/v2/metrics` 侧加入轮转执行统计指标。
2. 评估将 soft 审计事件入库，降低文件解析与轮转复杂度。
3. 持续推进 M3 可观测性与治理稳定性。
