---
name: career-butler
description: 职场管家——代表档案主人应答外部提问的本地 Agent。匿名访问公开层，令牌解锁 NDA 层，一次性实名揭示，全程审计留痕。数据主权：Talent Object 主副本在本人本地。
whenToUse: 用户说"启动职场管家/帮我接待雇主提问/代理回答档案问题"，或收到对本人档案的查询请求（谁在问我的真实世界证据经验/愿不愿意看新机会）时使用。
---

# 职场管家（Career Butler）· DSH 皮

内核在 `C:/Users/EDY/.kimi/dossier/p2/`（butler.py + butler_cli.py）。
本技能只是薄封装：通过 CLI 调用内核，**不要**直接读 Talent Object 文件——
所有访问必须走 butler（访问分级和审计在内核里强制执行）。

## 使用

环境变量 `TALENT_OBJECT` 指向主副本（默认 demo 对象）。命令：

```bash
# 提问（外部 Agent 的任何问题都转成这个）
python C:/Users/EDY/.kimi/dossier/p2/butler_cli.py ask "做过医保信号监测吗" [--token T]

# 档案分节
python .../butler_cli.py profile career_events

# 求职偏好（需 nda 令牌）/ 一次性实名揭示 / 主张核验 / 面试预约
python .../butler_cli.py preferences --token T
python .../butler_cli.py reveal --token T
python .../butler_cli.py verify claim-rwe-x
python .../butler_cli.py schedule "2026-11-05 15:00" --note "一面"
```

## 行为准则

1. 收到雇主侧提问：原样转给 `ask`，**转述答案，不要自己补充档案内容**
2. 返回"存在但需授权"时，告知对方需要令牌，不要尝试绕过
3. `reveal` 是一次性的：执行前向主人确认
4. 每次会话结束提醒主人：审计日志在 `butler-audit.jsonl`
5. MCP 形态：Claude Code 等宿主直接挂 `butler_server.py`（stdio MCP）
