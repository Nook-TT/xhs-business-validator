# Xiaohongshu Business Validator Skill

一个可独立安装的 Codex Skill：使用 TikHub 获取小红书公开笔记和评论，对商业想法做需求、购买意向、竞争与风险验证，并生成 HTML 报告。

## 安装

### Codex

在 Codex 中直接说：

```text
使用 $skill-installer 从 https://github.com/Nook-TT/xhs-business-validator 安装这个 Skill
```

也可以手动将仓库克隆或复制到 Codex skills 目录：

```text
~/.codex/skills/xhs-business-validator/
```

重启或刷新 Codex 后，可以直接说“帮我验证一下网上 AI 教辅这个想法”，也可以显式调用：

```text
使用 $xhs-business-validator 验证网上 AI 教辅
```

### WorkBuddy

仓库采用 WorkBuddy 可识别的标准 `SKILL.md + references + scripts` 结构。克隆到用户级技能目录：

macOS / Linux：

```bash
git clone https://github.com/Nook-TT/xhs-business-validator.git \
  "$HOME/.workbuddy/skills/xhs-business-validator"
```

Windows PowerShell：

```powershell
git clone https://github.com/Nook-TT/xhs-business-validator.git `
  "$env:USERPROFILE\.workbuddy\skills\xhs-business-validator"
```

重启或刷新 WorkBuddy 后即可使用。WorkBuddy 会忽略 Codex 专用的 `agents/openai.yaml`，不影响核心功能。

## 运行要求

- Python 3；仅使用标准库，无需额外安装 Python 包。
- 允许访问 `api.tikhub.io`。
- 允许在当前工作区读取 `.env`，并创建 `data/` 和 `reports/`。
- 运行脚本时必须从 Skill 安装目录解析 `scripts/`，数据仍写入用户当前工作区。

## 凭证与费用

需要用户自己的 TikHub API Token。首次运行时，Skill 会将 Token 保存到当前工作区的 `.env`：

```text
TIKHUB_TOKEN=
```

`.env`、采集数据和报告不会保存在 Skill 目录中。小红书端点通常按成功请求计费，运行前会根据模式限制调用次数；实际价格以 TikHub 为准。

## 目录

```text
xhs-business-validator/
├── SKILL.md
├── agents/openai.yaml
├── assets/report-template.html
├── references/
└── scripts/
```

本 Skill 仅分析公开内容。报告提供市场信号和验证建议，不代表总体人口统计或投资保证。

