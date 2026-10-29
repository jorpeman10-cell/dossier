# P0 转化器 — 最小链路

上传简历 → Talent Object JSON（投影B） → 可视化页面（投影A：V1轨迹/V3图谱/V4证据卡）。

## 用法

```bash
python convert.py <简历.(txt|md|docx|pdf)> [-o 输出目录] [--backend auto|anthropic|mock]
```

- `auto`：有 `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY`（含自定义 `ANTHROPIC_BASE_URL` 代理）就走真实 LLM，否则 mock
- 输出：`talent-object.json`（机器可读）+ `page.html`（浏览器直接打开）
- 校验 fail-closed：schema 不合法直接退出码 1，不产出半成品

## 已验证（2026-10-29）

- 富样本（陈之遥，虚构）：3 段经历、11 个证据数字全保真、推断诚实申报、页面渲染零 JS 错误
- 薄样本（李慕白，虚构）：正确降级——空轨迹提示"需访谈补充"、证据区提示"建议访谈补数"，不硬造内容
- docx/pdf 路径已接（python-docx/PyMuPDF/pypdf），未实弹测

## 边界（P0 不做）

工作流推断（V2/P1）、验证核验（全部 ○ 自述水位 V1）、Relay/签名（P2）。

真实简历测试集待补：建议从顾问常投的真实简历里挑 10-20 份脱敏后放入 `samples/`，
按 PRD §6 验收线跑（五元组准确率 ≥85%）。
