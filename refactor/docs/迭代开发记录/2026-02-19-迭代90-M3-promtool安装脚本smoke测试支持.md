# 迭代开发记录

迭代编号：`迭代90`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 为 `install-promtool.sh` 增加脚本级 smoke 测试支持。
2. 通过单测模拟不同架构分支，避免真实下载依赖。
3. 保持多架构映射与 checksum 逻辑稳定。

## 2. 计划范围（Plan）

1. 先补失败测试，要求脚本支持 dry-run 与架构覆盖。
2. 修改脚本并补齐校验逻辑。
3. 同步版本与文档。

## 3. 实际完成（Done）

1. 测试增强（先失败后通过）：
   - `test_promtool_installer_script_dry_run_auto_detects_x86_64`
   - `test_promtool_installer_script_dry_run_auto_detects_arm64`
   - `test_promtool_installer_script_fails_for_unsupported_arch`
2. 脚本增强：
   - `refactor/backend/scripts/install-promtool.sh`
   - 新增 `PROMTOOL_DRY_RUN=1`：仅解析平台并输出，跳过下载安装。
   - 新增 `PROMTOOL_MACHINE_ARCH`：用于覆盖 `uname -m`，便于测试分支。
   - 新增平台默认 checksum 映射（`linux-amd64` + `linux-arm64`）。
3. 版本升级：
   - `0.3.75-m3-promtool-installer-dryrun-smoke`

## 4. 未完成项（Not Done）

1. 暂未引入对更多平台 artifact 的自动映射。
2. 暂未将安装脚本独立纳入单独 CI job（当前由现有测试覆盖）。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/scripts/install-promtool.sh`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代90-M3-promtool安装脚本smoke测试支持.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 定向测试：通过（10 passed）
   - CI 脚本：通过
3. 是否达到验收标准：
   - 达到（脚本级 smoke 测试可覆盖多架构分支，且无需外部网络依赖）

## 7. 风险与问题

1. 风险描述：平台 checksum 需要随 promtool 版本升级同步维护。
2. 影响范围：安装脚本正确性与 CI 可用性。
3. 缓解措施：后续补版本升级清单与 checksum 更新流程。

## 8. 关键决策

1. 决策内容：通过 `PROMTOOL_DRY_RUN` 实现可测试分支，而非在单测中真实下载 artifact。
2. 决策原因：测试稳定、执行快、无外部依赖。
3. 影响模块：promtool 安装脚本测试策略与 CI 稳定性。

## 9. 下迭代计划

1. 评估将 promtool 版本与 checksum 维护抽取为集中配置文件。
2. 评估为安装脚本增加更细粒度错误码。
3. 持续推进 M3 治理链路稳定性提升。
