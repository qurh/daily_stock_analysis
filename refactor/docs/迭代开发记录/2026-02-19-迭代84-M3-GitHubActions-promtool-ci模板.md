# 迭代开发记录

迭代编号：`迭代84`  
日期：`2026-02-19`  
负责人：`Codex + qrh`

---

## 1. 本迭代目标

1. 补齐 CI 平台级示例配置（安装 `promtool` + 运行 `scripts/ci.sh`）。
2. 将模板路径与启用方式同步到 `README`。
3. 用单测锁定模板关键步骤，防止后续回退。

## 2. 计划范围（Plan）

1. 先新增失败测试，约束示例 workflow 必须包含 `promtool` 安装与 `ci.sh` 执行。
2. 新增 GitHub Actions 模板文件。
3. 更新版本与文档。

## 3. 实际完成（Done）

1. 新增 GitHub Actions 示例模板：
   - `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
2. 新增测试：
   - `test_github_actions_refactor_ci_example_includes_promtool_install_and_ci_run`
3. 文档更新：
   - `README` 增加模板路径与启用说明。
4. 版本升级：
   - `0.3.69-m3-github-actions-promtool-ci-template`

## 4. 未完成项（Not Done）

1. 暂未将该模板直接落地为根目录可执行 workflow（当前为示例文件，需按需复制）。
2. 暂未覆盖其他 CI 平台（如 GitLab CI）模板。

## 5. 代码与文档变更

1. 代码路径：
   - `refactor/backend/ci/github-actions/refactor-backend-ci.example.yml`
   - `refactor/backend/src/app/main.py`
2. 测试路径：
   - `refactor/backend/tests/unit/test_ci_prometheus_rules_check.py`
3. 文档路径：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/迭代开发记录/2026-02-19-迭代84-M3-GitHubActions-promtool-ci模板.md`

## 6. 验证记录

1. 执行命令：
   - `cd refactor/backend && pytest tests/unit/test_ci_prometheus_rules_check.py -q`
   - `cd refactor/backend && bash scripts/ci.sh`
2. 结果摘要：
   - 定向测试：通过（先失败后通过）
   - CI 脚本：通过
3. 是否达到验收标准：
   - 达到（示例模板与文档可用，关键步骤有测试约束）

## 7. 风险与问题

1. 风险描述：示例模板中的 `apt-get install prometheus` 会受基础镜像可用性影响。
2. 影响范围：CI 初始化阶段稳定性。
3. 缓解措施：后续可切换为固定版本二进制下载安装方式。

## 8. 关键决策

1. 决策内容：本轮先交付“可复制模板 + 自动化测试”而非直接改主仓 workflow。
2. 决策原因：避免影响现有主线 CI，同时满足“平台级示例配置”目标。
3. 影响模块：CI 规范文档与质量门禁模板。

## 9. 下迭代计划

1. 评估将模板升级为根目录正式 workflow 并按路径过滤触发。
2. 评估 `promtool` 固定版本安装脚本，降低包仓库波动风险。
3. 继续完善 M3 治理链路的可观测指标与告警模板联动。
