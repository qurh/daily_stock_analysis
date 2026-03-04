# 2026-03-04 迭代275 - M4 CI Optional Positive Rehearsal Stage

迭代编号：`迭代275`  
日期：`2026-03-04`  
负责人：`Codex`

---

## 1. 本迭代目标

1. 在不改变默认 CI 时长的前提下，提供可选的 M4 正向联调阶段。
2. 将 one-click 正向演练脚本接入 `ci.sh`，通过环境变量显式启用。

## 2. 实施内容

1. 修改 `refactor/backend/scripts/ci.sh`：
   - 新增开关：
     - `CI_RUN_M4_POSITIVE_REHEARSAL=1`
   - 开启时，在单测后执行：
     - `./scripts/rehearse-m4-positive-flow.sh`
2. 同步文档：
   - `refactor/backend/README.md` 增加可选 CI stage 用法说明。
   - `refactor/docs/CHANGELOG.md` 增加版本记录。
3. 版本更新：
   - `refactor/backend/src/app/main.py`
   - `0.4.57-m4-ci-optional-positive-rehearsal-stage`

## 3. 验证记录

1. RED：
   - 修改前检索 `CI_RUN_M4_POSITIVE_REHEARSAL` 无命中（确认功能尚未接入）。
2. GREEN：
   - 修改后检索命中 `ci.sh` 新增分支。
3. 脚本校验：
   - `bash -n refactor/backend/scripts/ci.sh` 通过。
   - `bash -n refactor/backend/scripts/rehearse-m4-positive-flow.sh` 通过。
   - `python3 -m py_compile refactor/backend/src/app/main.py` 通过。
4. 功能相关回归：
   - one-click 脚本 `rehearse-m4-positive-flow.sh` 已在上一迭代成功实跑（publish/bind/rollback 全通过）。

## 4. 结论

1. M4 正向演练已可按需接入 CI 链路。
2. 默认 CI 行为不变，只有显式设置 `CI_RUN_M4_POSITIVE_REHEARSAL=1` 才会执行额外联调阶段。
