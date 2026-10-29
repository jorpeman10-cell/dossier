# P2 · 职场管家（Career Butler）

一个内核、两个薄前端、一份 skill 皮——Talent Object 主副本留在人才本地，
访问分级与审计在内核强制执行（PRD v0.2 三条产品定律的代码化）。

```
butler.py        内核：访问分级(public/community/nda) / ask证据引用 /
                 一次性reveal / verify签名主张 / 审计日志(永不记NDA内容)
butler_server.py MCP stdio 前端（零依赖 JSON-RPC）
butler_cli.py    CLI 前端（无 MCP 的 harness 用）
skill-dsh/       DSH 技能皮
demo/            虚构演示对象（含 grants/preferences/签名主张）
butler_test.py   17项测试：访问模型 + MCP 握手
```

## 快速开始

```bash
python butler_test.py                          # 17/17 应全绿
python butler_cli.py ask "做过医保信号监测吗"     # 匿名提问（公开层）
python butler_cli.py ask "求职偏好" --token grant-employer-001   # NDA层
python butler_cli.py reveal --token grant-reveal-001             # 一次性揭示
```

## 挂进 Claude Code（MCP）

```json
"mcpServers": { "career-butler": {
  "command": "python",
  "args": ["C:/Users/EDY/.kimi/dossier/p2/butler_server.py"],
  "env": { "TALENT_OBJECT": "C:/path/to/me/talent-object.json" } } }
```

## 隐私模型（实测覆盖）

- 匿名 → 只读公开层；问 NDA 话题回"存在，需授权"（不否认存在=不泄露存在性）
- `grant-*` 令牌 → 按 grants 声明的级别解锁
- `reveal` 一次性，用过作废并持久化
- 审计日志记录所有调用，但**永不写入 NDA 内容本身**（有测试断言）

## P2 剩余（未含本切片）

Relay 中继（离线存储转发）、登记处真实签名（现为演示签名）、试点 10 人。
