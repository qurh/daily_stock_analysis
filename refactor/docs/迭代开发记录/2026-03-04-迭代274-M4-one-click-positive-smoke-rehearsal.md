# 2026-03-04 迭代274 - M4 One-Click Positive Smoke Rehearsal

迭代编号：`迭代274`  
日期：`2026-03-04`  
负责人：`Codex`

---

## 1. 本迭代目标

1. 提供一条可一键执行的正向联调链路命令。
2. 避免手工启动服务、拼接参数、清理临时数据。
3. 保留失败日志定位能力，提升回归效率。

## 2. 实施内容

1. 新增脚本：`refactor/backend/scripts/rehearse-m4-positive-flow.sh`
   - 加载 backend `.env` 白名单配置。
   - 默认隔离运行环境（临时 `DATABASE_URL` + `CHROMA_PATH`）。
   - 启动 uvicorn（默认 `127.0.0.1:18080`）并做 health 检查。
   - 调用 `smoke-positive-strategy-flow.py` 执行正向链路：
     - `publish -> bind -> rollback`
   - 自动清理临时运行目录（可通过 `KEEP_RUNTIME_ARTIFACTS=1` 保留）。
2. 文档同步：
   - `refactor/backend/README.md` 增加 one-click 用法与参数说明。
   - `refactor/docs/CHANGELOG.md` 增加版本记录。

## 3. 验证结果

1. RED 验证：
   - 实现前执行 `./scripts/rehearse-m4-positive-flow.sh`，确认脚本不存在失败。
2. GREEN 验证：
   - 执行 `./scripts/rehearse-m4-positive-flow.sh` 成功。
   - 输出包含：
     - `publish_status = 200`
     - `bindings_count = 1`
     - `rollback_status = rolled_back`

## 4. 变更文件

1. 代码：
   - `refactor/backend/scripts/rehearse-m4-positive-flow.sh`
   - `refactor/backend/src/app/main.py`
2. 文档：
   - `refactor/backend/README.md`
   - `refactor/docs/CHANGELOG.md`
   - `refactor/docs/plans/2026-03-04-m4-one-click-positive-smoke-rehearsal.md`

## 5. 结论

1. M4 正向联调已具备“一键执行”能力。
2. 后续可将该脚本加入发布前检查或 CI 手工触发任务。
