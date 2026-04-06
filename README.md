<div align="center">

# 老板.skill / boss-skills

> *"你们搞大模型的就是码奸，你们已经害死前端兄弟了，还要害死后端兄弟，测试兄弟，运维兄弟，害死网安兄弟，害死ic兄弟，最后害死自己害死全人类"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

<br>
**本项目纯属娱乐，请勿带入现实**
你的老板总能在 30 秒内否掉一个方案，  
但没人能准确说清楚他到底在看什么。

提供老板的聊天记录、批注、邮件、会议纪要、截图和你的补充说明，  
生成一个专属于你的赛博老板。

[支持的数据源](#支持的数据源) · [安装](#安装) · [使用](#使用) · [命令](#命令) · [项目结构](#项目结构) · [安全边界](#安全边界) · [致敬与引用](#致敬与引用)

</div>

---

## 这是什么

`boss-skills` 是一个正式版 Agent Skill。

它不是简单模仿老板口头禅，也不是塞一段 prompt 冒充老板，而是把老板拆成三个层次：

| 层 | 作用 | 产物 |
|------|------|------|
| `Operating System` | 目标排序、审批阈值、风险偏好、汇报偏好、升级路径 | `operating-system.md` |
| `Voice` | 语气、压缩度、常用句式、催办方式、批评方式 | `voice.md` |
| `Boundary` | 不能伪造的授权、人事、法务、财务、对外承诺边界 | `boundary.md` |

整个 repo 本身就是一个 skill 目录，遵循 [AgentSkills](https://agentskills.io) 的开放组织方式。

和很多“先做个角色再说”的项目不同，`boss-skills` 只允许两种正式状态：

- `collecting`：持续导入材料、计算覆盖率、查缺补漏
- `ready`：证据门槛达标后，开放老板调用模式

未进入 `ready` 之前，不会生成可调用的半成品老板。

---

## 为什么要做这个

- 闲的
- 由同事.skills启发
- 给每一位赛博员工配备赛博老板

---

## 支持的数据源

当前仓库交付的是正式可用的离线导入链路，不包含半接通的自动采集器。

| 来源 | 当前支持 | 说明 | 备注 |
|------|:-------:|------|------|
| 直接口述 / 描述 | ✅ | 初始化老板档案 | 适合先建档 |
| 粘贴聊天 / 批注文本 | ✅ | 进入 `records/*.jsonl` | 适合 Voice / Operator |
| `.txt` / `.md` / `.log` | ✅ | 纯文本导入 | |
| `.json` / `.jsonl` / `.csv` | ✅ | 结构化导出导入 | |
| `.docx` / `.html` / `.htm` / `.eml` | ✅ | 文档和邮件导入 | |
| `.pdf` | ✅ | 需安装 `pypdf` | 可选依赖 |
| 图片 / 截图 | ✅ | 需安装 `rapidocr-onnxruntime` | 可选依赖 |
| 飞书 / 钉钉 / Slack 自动采集 | ❌ | 本版不交付 | 为避免开源仓库里出现半成品连接器 |

Ready gate 固定为：

- 至少两种不同的、非 correction 的 `source_type`
- 至少一条老板直接表达材料
- 至少一条决策或管理动作材料

---

## 安装

### 运行时目录

将本仓库放到以下目录之一即可被相应运行时发现：

- Codex：`~/.codex/skills/boss-skills/`
- Claude Code：`.claude/skills/boss-skills/` 或 `~/.claude/skills/boss-skills/`
- OpenClaw：`~/.openclaw/workspace/skills/boss-skills/`

### 依赖

如果需要 OCR 或 PDF 导入，安装依赖即可。普通文本导入不依赖额外模型服务。

Windows + Python 3.12：

```powershell
py -3.12 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

通用 Python：

```bash
python -m pip install -r requirements.txt
```

---

## 使用

### 第一步：初始化老板档案

在支持 slash command 的运行时里输入：

```text
/boss:init
```

如果当前运行时不支持 slash command，就把相同意图映射到 CLI：

```powershell
py -3.12 scripts/boss_archive.py init --slug founder-alpha --display-name "Founder Alpha" --boss-type founder
```

### 第二步：导入材料

支持四类正式导入路径：

- describe：直接口述老板特征
- paste-chat：粘贴聊天记录或批注
- import-file：导入文档、导出文件、邮件
- import-image：导入截图并 OCR

### 第三步：达到 ready 后再调用

达到门槛后，可以使用：

- `/boss:{slug}`：完整老板模式
- `/boss:{slug}-operator`：只看判断逻辑和管理动作
- `/boss:{slug}-voice`：只看表达风格
- `/boss:pua {slug}`：工作高压模式，强调执行、清晰度、速度、owner 和优先级

---

## 命令

| 命令 | 说明 |
|------|------|
| `/boss:init` | 初始化老板档案并导入首批材料 |
| `/boss:update-boss {slug}` | 追加材料或对 `ready` 档案写入正式纠正 |
| `/boss:list-bosses` | 列出所有老板档案 |
| `/boss:{slug}` | 完整老板模式 |
| `/boss:{slug}-operator` | 只输出 `Operating System` |
| `/boss:{slug}-voice` | 只输出 `Voice` |
| `/boss:pua {slug}` | 输出工作高压模式，不绕过边界 |
| `/boss:boss-rollback {slug} {version}` | 回滚到历史版本 |
| `/boss:delete-boss {slug}` | 删除老板档案 |

CLI 入口统一在：

```powershell
py -3.12 scripts/boss_archive.py
```

例如：

```powershell
py -3.12 scripts/boss_archive.py pua --slug founder-alpha
```

---

## 调用效果

> 输入：`/boss:founder-alpha-operator`

```text
先给我结论，再给我三件事：
1. 这件事为什么现在做
2. 不做的代价是什么
3. 谁负责，什么时间给结果

如果没有 owner、deadline、风险说明，这不是方案，只是描述。
```

> 输入：`/boss:pua founder-alpha`

```text
别跟我讲过程感受，讲结果。
你现在的问题不是不努力，是没有优先级、没有 owner、没有时间点。
今天给我一个版本：谁做、做到哪一步、卡点是什么、如果失败怎么止损。
今晚之前回我。
```

`/boss:pua` 的定义是“工作高压推进模式”，不是人格打击模式。

---

## 项目结构

```text
boss-skills/
├── SKILL.md
├── README.md
├── .gitignore
├── agents/
│   └── openai.yaml
├── prompts/
│   ├── init_wizard.md
│   ├── evidence_router.md
│   ├── operator_analyzer.md
│   ├── voice_analyzer.md
│   ├── boundary_analyzer.md
│   ├── coverage_reporter.md
│   └── merger.md
├── references/
│   ├── evidence-schema.md
│   ├── command-contracts.md
│   └── safety-policy.md
├── scripts/
│   └── boss_archive.py
├── tools/
│   ├── archive.py
│   ├── evidence.py
│   ├── extractors.py
│   ├── ocr.py
│   └── renderers.py
├── tests/
└── bosses/
```

说明：

- `prompts/`：初始化、路由、分析、合并流程
- `references/`：结构契约和安全边界
- `scripts/`：统一 CLI 入口
- `tools/`：归档、提取、OCR、覆盖率和渲染逻辑
- `bosses/`：本地生成的老板档案，默认不提交

---

## 安全边界
**请勿擅自对skill.md中的以下内容进行更改或删除部分，若因此出现skills失控问题，请上报issues**
本项目默认拒绝或降级以下请求：

- 冒充真实老板做审批、签字或授权
- 给出真实生效的人事、法务、财务、薪酬结论
- 对外作出正式承诺
- 用薄弱证据输出确定性人格判断

`/boss:pua` 也不例外。

它可以压执行、压速度、压 owner、压优先级，但不能：

- 压人格
- 压尊严
- 压私人关系
- 压心理状态
- 伪造惩罚、威胁或现实世界权威

---

## 开源说明

这个仓库默认不携带任何示例老板数据，也不提交本地生成档案。

`.gitignore` 已忽略：

- `bosses/*`
- `tests/.tmp/`
- `__pycache__/`
- `.vendor/`

也就是说，公开仓库只包含 skill 框架、提示词、脚本和测试，不包含任何真实老板材料。

---

## 致敬与引用

本项目的开源包装方式、repo-as-skill 组织方式，以及 README 的公开呈现思路，参考并致敬：

- [titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)
- [therealXiaomanChu/ex-skill](https://github.com/therealXiaomanChu/ex-skill)

---

如果你想把“老板”变成一个正式、可维护、可回滚、可纠正的 Skill，  
`boss-skills` 就是那个适合开源出来的骨架。
