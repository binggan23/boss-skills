# Command Contracts / 命令契约

## `/boss:init`

Use `/boss:init` to create a new formal archive and optionally ingest the first evidence batch.

使用 `/boss:init` 创建一个新的正式老板档案，并可在同一步导入首批材料。

Required identifiers / 必填标识:

- `slug`
- `display_name`
- `boss_type`

Allowed ingestion inputs / 允许的导入输入:

- inline text
- file path
- image path

- 行内文本
- 文件路径
- 图片路径

Outputs / 输出结果:

- archive created under `bosses/<slug>/`
- `manifest.json`
- `analysis/coverage.json`
- `analysis/router.json`
- version snapshot in `versions/`

- 在 `bosses/<slug>/` 下创建档案
- `manifest.json`
- `analysis/coverage.json`
- `analysis/router.json`
- `versions/` 中的版本快照

## `/boss:update-boss {slug}`

Use `/boss:update-boss {slug}` to add evidence or add a formal correction to a ready archive.

使用 `/boss:update-boss {slug}` 为既有档案补充材料，或为 `ready` 档案写入正式纠正。

Allowed corrections / 允许的纠正目标:

- `voice`
- `operator`
- `boundary`

Never allow corrections on a `collecting` archive.

`collecting` 状态下禁止写入纠正。

## `/boss:{slug}`, `/boss:{slug}-operator`, `/boss:{slug}-voice`, `/boss:pua {slug}`

These commands require `status == ready`.

这些调用命令要求 `status == ready`。

Mode mapping / 模式映射:

- `full` -> boundary + operating system + voice
- `operator` -> boundary + operating system
- `voice` -> boundary + voice
- `pua` -> boundary + operating system + voice + pressure overlay

- `full` -> 边界审查 + 决策系统 + 表达风格
- `operator` -> 边界审查 + 决策系统
- `voice` -> 边界审查 + 表达风格
- `pua` -> 边界审查 + 决策系统 + 表达风格 + 高压推进覆盖层

Use `/boss:pua {slug}` to render a work-focused, high-pressure boss mode that challenges vague plans, excuses, missed commitments, and soft prioritization.

使用 `/boss:pua {slug}` 输出面向工作的高压老板模式，用于持续质疑模糊方案、借口、失约和软弱优先级。

## `/boss:boss-rollback {slug} {version}`

Restore the archive to a prior snapshot, then create a new snapshot of the restored state.

将档案恢复到指定历史快照，然后为恢复后的状态再创建一个新快照。

## `/boss:delete-boss {slug}`

Delete the archive only when the user explicitly requests deletion.

只有在用户明确要求删除时才允许删除档案。
