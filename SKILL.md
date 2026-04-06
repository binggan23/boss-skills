---
name: boss-skills
description: "Build and maintain an evidence-backed boss archive and guarded boss simulation for Codex, Claude Code, or OpenClaw. Use when an agent needs to initialize a boss archive with /boss:init, ingest text or files, analyze decision patterns and communication style, update or rollback a boss instance, or answer as a ready boss through full, operator, voice, or /boss:pua pressure mode without implying real authority. / 为 Codex、Claude Code 或 OpenClaw 构建基于真实材料的老板档案与受约束模拟。用于通过 /boss:init 建档、导入文本或文件、分析决策与表达风格、更新或回滚老板实例，以及在 ready 状态下通过 full、operator、voice 或 /boss:pua 高压模式进行受约束响应而不冒充真实授权。"
---

# Boss Skills

> **Language / 语言**: Support both English and Chinese. Detect the user's language from the first substantial user message and keep the same language throughout the workflow unless the user explicitly switches.
>
> 本 Skill 同时支持中文和英文。根据用户第一条有效消息判断语言，并在整个流程中保持同一种语言；只有用户明确切换时才跟着切换。

## Overview / 概览

Create and maintain a formal boss archive from real evidence. The archive has only two valid states: `collecting` and `ready`.

基于真实材料创建并维护一个正式的老板档案。档案只允许两种状态：`collecting` 和 `ready`。

Use this skill only for a specific boss identity backed by imported materials. Do not invent a boss persona, create sample bosses, or make a callable boss while the archive is still `collecting`.

本 Skill 只用于有真实材料支撑的特定老板身份。不要凭空虚构老板人格，不要生成示例老板，也不要在 `collecting` 状态下产出可调用的老板分身。

## Runtime Compatibility / 运行时兼容性

This skill is designed to work across `Codex`, `Claude Code`, and `OpenClaw`.

本 Skill 设计为同时支持 `Codex`、`Claude Code` 和 `OpenClaw`。

Compatibility rules:

- Resolve `SKILL_DIR` as the directory that contains this `SKILL.md`.
- Resolve `PY_RUNNER` in this order:
  1. `python3`
  2. `python`
  3. `py -3.12` on Windows when `python3` is unavailable
- Do not assume slash commands are natively registered by the runtime.
- Treat slash commands as public command names. If the runtime does not support slash commands, map the same user intent to the equivalent CLI call.
- Use the runtime's shell tool:
  - Codex: shell / terminal tool
  - Claude Code: Bash / shell tool
  - OpenClaw: Bash / shell tool

兼容规则：

- 将 `SKILL_DIR` 解析为当前 `SKILL.md` 所在目录。
- 按以下顺序选择 `PY_RUNNER`：
  1. `python3`
  2. `python`
  3. Windows 上若没有 `python3`，使用 `py -3.12`
- 不要假设运行时天然支持 slash 命令。
- 将 slash 命令视为公开命令名；如果当前运行时不支持 slash 语法，就把相同意图映射到对应 CLI。
- 使用各运行时自带的 shell 工具：
  - Codex: shell / terminal
  - Claude Code: Bash / shell
  - OpenClaw: Bash / shell

Recommended install targets:

- Codex: `~/.codex/skills/boss-skills/`
- Claude Code: `.claude/skills/boss-skills/` in the repo root, or `~/.claude/skills/boss-skills/`
- OpenClaw: `~/.openclaw/workspace/skills/boss-skills/`

推荐安装路径：

- Codex：`~/.codex/skills/boss-skills/`
- Claude Code：仓库根目录下的 `.claude/skills/boss-skills/`，或 `~/.claude/skills/boss-skills/`
- OpenClaw：`~/.openclaw/workspace/skills/boss-skills/`

## Trigger Conditions / 触发条件

Activate this skill when the user says any of the following or expresses equivalent intent:

- `/boss:init`
- `/boss:update-boss {slug}`
- `/boss:list-bosses`
- `/boss:{slug}`
- `/boss:{slug}-operator`
- `/boss:{slug}-voice`
- `/boss:boss-rollback {slug} {version}`
- `/boss:delete-boss {slug}`
- `/boss:pua {slug}`
- "help me create a boss skill"
- "initialize my boss archive"
- "import boss materials"
- "update this boss profile"
- "put me under boss pressure"

当用户说出以下任一命令，或表达等价意图时，启用本 Skill：

- `/boss:init`
- `/boss:update-boss {slug}`
- `/boss:list-bosses`
- `/boss:{slug}`
- `/boss:{slug}-operator`
- `/boss:{slug}-voice`
- `/boss:boss-rollback {slug} {version}`
- `/boss:delete-boss {slug}`
- `/boss:pua {slug}`
- “帮我创建一个老板 skill”
- “初始化我的老板档案”
- “导入老板材料”
- “更新这个老板画像”

## Command Map / 命令映射

Public commands:

- `/boss:init`
- `/boss:update-boss {slug}`
- `/boss:list-bosses`
- `/boss:{slug}`
- `/boss:{slug}-operator`
- `/boss:{slug}-voice`
- `/boss:boss-rollback {slug} {version}`
- `/boss:delete-boss {slug}`
- `/boss:pua {slug}`

公开命令：

- `/boss:init`
- `/boss:update-boss {slug}`
- `/boss:list-bosses`
- `/boss:{slug}`
- `/boss:{slug}-operator`
- `/boss:{slug}-voice`
- `/boss:boss-rollback {slug} {version}`
- `/boss:delete-boss {slug}`
- `/boss:pua {slug}`

CLI mapping:

- `/boss:init` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py init ...`
- `/boss:update-boss {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py update-boss ...`
- `/boss:list-bosses` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py list-bosses`
- `/boss:{slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode full`
- `/boss:{slug}-operator` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode operator`
- `/boss:{slug}-voice` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode voice`
- `/boss:boss-rollback {slug} {version}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py boss-rollback --slug <slug> --version <version>`
- `/boss:delete-boss {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py delete-boss --slug <slug> --yes`
- `/boss:pua {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py pua --slug <slug>`

CLI 对应关系：

- `/boss:init` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py init ...`
- `/boss:update-boss {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py update-boss ...`
- `/boss:list-bosses` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py list-bosses`
- `/boss:{slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode full`
- `/boss:{slug}-operator` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode operator`
- `/boss:{slug}-voice` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py render --slug <slug> --mode voice`
- `/boss:boss-rollback {slug} {version}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py boss-rollback --slug <slug> --version <version>`
- `/boss:delete-boss {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py delete-boss --slug <slug> --yes`
- `/boss:pua {slug}` -> `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py pua --slug <slug>`

Use `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py status --slug <slug>` as the internal inspection command during `/boss:init` and `/boss:update-boss`.

在 `/boss:init` 和 `/boss:update-boss` 过程中，内部状态检查统一使用 `${PY_RUNNER} {SKILL_DIR}/scripts/boss_archive.py status --slug <slug>`。

## Main Workflow / 主流程

### `/boss:init`

Execute the archive workflow in this order:

1. Establish boss identity.
   Required fields: `slug`, `display_name`, `boss_type`.
2. Choose exactly one ingestion path for the current step.
   Supported v1 paths: inline description, pasted chat or annotation text, file import, screenshot OCR import.
3. Normalize imported material into `bosses/<slug>/records/*.jsonl`.
4. Recompute routing and coverage.
   Read `prompts/evidence_router.md` and `prompts/coverage_reporter.md`.
5. Stop at `collecting` unless the ready gate is fully satisfied.

按以下顺序执行档案初始化流程：

1. 建立老板身份。
   必填字段：`slug`、`display_name`、`boss_type`。
2. 为当前步骤选择且只选择一种导入路径。
   v1 支持：口述描述、粘贴聊天/批注文本、文件导入、截图 OCR 导入。
3. 将导入材料标准化写入 `bosses/<slug>/records/*.jsonl`。
4. 重新计算路由与覆盖率。
   需要读取 `prompts/evidence_router.md` 和 `prompts/coverage_reporter.md`。
5. 除非完全满足 ready gate，否则保持在 `collecting`。

Ready gate / 就绪门槛：

- at least two distinct non-correction `source_type` values
- at least one direct-expression record
- at least one decision or management-action record

- 至少两种不同的、非 correction 的 `source_type`
- 至少一条老板直接表达材料
- 至少一条决策或管理动作材料

If the gate is not met, report `missing_evidence` and do not create `operating-system.md`, `voice.md`, `boundary.md`, or `corrections.md`.

如果门槛未满足，必须返回 `missing_evidence`，并且不得生成 `operating-system.md`、`voice.md`、`boundary.md`、`corrections.md`。

### `/boss:update-boss {slug}`

Use this command to add new evidence or apply formal corrections.

- For new evidence, use the same ingestion paths as `/boss:init`.
- Allow corrections only on a `ready` archive.
- Allowed correction targets: `operator`, `voice`, `boundary`.
- Recompute routing and coverage after every update.
- If the archive is already `ready`, regenerate only the affected layer documents unless the state changed or a rollback occurred.

用这个命令追加新材料或写入正式纠正。

- 新材料的导入路径与 `/boss:init` 完全一致。
- 只有 `ready` 状态档案允许纠正。
- 允许的纠正目标：`operator`、`voice`、`boundary`。
- 每次更新后都要重算路由与覆盖率。
- 如果档案已经是 `ready`，则只重生成受影响层，除非状态变化或发生回滚。

Before revising a ready archive, read:

- `prompts/operator_analyzer.md`
- `prompts/voice_analyzer.md`
- `prompts/boundary_analyzer.md`
- `prompts/merger.md`

在修改 `ready` 档案前，读取：

- `prompts/operator_analyzer.md`
- `prompts/voice_analyzer.md`
- `prompts/boundary_analyzer.md`
- `prompts/merger.md`

## Invocation Rules / 调用规则

Before responding through `/boss:{slug}`, `/boss:{slug}-operator`, `/boss:{slug}-voice`, or `/boss:pua {slug}`:

1. Run the `render` command for the requested mode.
2. Confirm that archive status is `ready`.
3. Read the returned prompt pack and generated markdown files.
4. Keep `Boundary` ahead of every answer.

在通过 `/boss:{slug}`、`/boss:{slug}-operator`、`/boss:{slug}-voice` 或 `/boss:pua {slug}` 回答前：

1. 先运行对应模式的 `render` 命令。
2. 确认档案状态为 `ready`。
3. 读取返回的 prompt pack 与已生成 markdown 文件。
4. 所有输出都必须先经过 `Boundary`。

Mode rules / 模式规则：

- `/boss:{slug}` -> `Boundary` -> `Operating System` -> `Voice`
- `/boss:{slug}-operator` -> `Boundary` -> `Operating System`
- `/boss:{slug}-voice` -> `Boundary` -> `Voice`
- `/boss:pua {slug}` -> `Boundary` -> `Operating System` -> `Voice` -> pressure overlay

If the archive is not `ready`, refuse invocation and report `missing_evidence`.

如果档案还不是 `ready`，必须拒绝调用，并返回 `missing_evidence`。

## Evidence Rules / 证据规则

Follow:

- `references/evidence-schema.md`
- `references/command-contracts.md`

遵循：

- `references/evidence-schema.md`
- `references/command-contracts.md`

Normalization rules:

- Preserve timestamps when present.
- Preserve the original speaker when discoverable.
- Keep `source_type` explicit.
- Use `layer_hint` only as a routing hint, never as proof.
- Treat corrections as operational metadata, not as ready-gate evidence.

标准化规则：

- 能保留时间戳就保留。
- 能识别原始说话人就保留。
- `source_type` 必须显式写出。
- `layer_hint` 只能作为路由提示，不能当成证据本身。
- `correction` 只算运维元数据，不计入 ready gate。

Supported v1 imports:

- Plain text: `.txt`, `.md`, `.log`
- Structured exports: `.json`, `.jsonl`, `.csv`
- Documents: `.docx`, `.eml`, `.html`, `.htm`
- Optional PDF extraction when `pypdf` is installed
- Optional screenshot OCR when `rapidocr-onnxruntime` is installed

v1 支持导入：

- 纯文本：`.txt`、`.md`、`.log`
- 结构化导出：`.json`、`.jsonl`、`.csv`
- 文档：`.docx`、`.eml`、`.html`、`.htm`
- 如已安装 `pypdf`，支持 PDF 文本提取
- 如已安装 `rapidocr-onnxruntime`，支持截图 OCR

## Safety Rules / 安全规则

Read `references/safety-policy.md` before answering as a boss.

在以老板身份响应前，先读取 `references/safety-policy.md`。

Always refuse or downgrade requests that require:

- impersonating the real boss for approvals, signatures, or authorizations
- making HR, legal, finance, or compensation decisions as if they are binding
- issuing commitments to external parties
- presenting weak evidence as certain personality truth
- using `/boss:pua` to attack identity, dignity, personal relationships, or mental health instead of work execution

以下请求必须拒绝，或至少降级为模拟建议：

- 冒充真实老板做审批、签字或授权
- 像真实决定一样给出 HR、法务、财务或薪酬结论
- 对外做正式承诺
- 用薄弱材料输出确定性人格判断
- 把 `/boss:pua` 用成人格打击、尊严贬损、私人关系攻击或心理状态施压，而不是用于工作推进

Never state or imply that the simulated boss actually approved, rejected, signed, authorized, or instructed a real-world action.

永远不要声称或暗示这个模拟老板已经真实批准、否决、签字、授权或指示了现实世界中的动作。

## Resources / 资源

- `scripts/boss_archive.py`: local command runner for archive creation, ingestion, coverage, rendering, rollback, and deletion
- `tools/`: extraction, routing, coverage, rendering, and archive management modules
- `prompts/`: analyzer and workflow prompts loaded only when needed
- `references/evidence-schema.md`: record contract
- `references/command-contracts.md`: command semantics
- `references/safety-policy.md`: hard boundaries

- `scripts/boss_archive.py`：本地命令执行器，负责建档、导入、覆盖率、渲染、回滚、删除
- `tools/`：提取、路由、覆盖率、渲染、归档管理模块
- `prompts/`：按需加载的分析与流程提示
- `references/evidence-schema.md`：记录格式约束
- `references/command-contracts.md`：命令语义约束
- `references/safety-policy.md`：硬边界
