# Codex Skills / Codex 技能仓库

本仓库保存一组面向 Codex 的本地技能与全局路由说明，用于把常用工程约束、编码规范、版本控制流程和多 Agent 协作协议沉淀为可复用的 `SKILL.md`。

This repository stores a curated set of local Codex skills and routing instructions. It turns recurring engineering rules, coding conventions, version-control workflows, and multi-agent coordination protocols into reusable `SKILL.md` packages.

## Contents / 内容

| Skill / 技能 | Purpose / 用途 |
| --- | --- |
| `karpathy-guidelines` | Reduces common AI coding mistakes through explicit assumptions, simple designs, surgical edits, and verifiable success criteria. / 通过明确假设、保持简单、控制改动范围和定义可验证目标，降低 AI 编码常见失误。 |
| `code-comment` | Enforces Chinese code-comment quality gates for generated, modified, reviewed, or documented code. / 为代码生成、修改、审查和文档化执行中文注释质量闸门。 |
| `encoding-guardian` | Protects mixed-encoding legacy files, especially GBK/ANSI and UTF-8-BOM source trees. / 保护混合编码旧工程文件，尤其是 GBK/ANSI 与 UTF-8-BOM 源码。 |
| `svn-workflow` | Maps Git habits to SVN-safe workflows for projects that use Subversion. / 为 SVN 项目提供替代 Git 习惯的安全工作流。 |
| `vibe-kanban-agent-protocol` | Defines issue topology, workspace usage, integration, cleanup, and leadership rules for Vibe Kanban multi-agent work. / 定义 Vibe Kanban 多 Agent 协作中的任务关系、工作区、集成、清理和负责人规则。 |

## Repository Layout / 仓库结构

```text
.
├── AGENTS.md
├── sync-codex-global.ps1
├── code-comment/
├── encoding-guardian/
├── karpathy-guidelines/
├── svn-workflow/
└── vibe-kanban-agent-protocol/
```

Each skill directory contains a `SKILL.md`. Some skills also include `agents/`, `references/`, or `scripts/` for supporting material.

每个技能目录都包含 `SKILL.md`。部分技能还包含 `agents/`、`references/` 或 `scripts/`，用于存放辅助材料。

## Usage / 使用方式

Codex discovers local skills from:

Codex 从以下目录发现本地技能：

```text
C:\Users\KSG\.codex\skills
```

To use a skill globally, place the whole skill directory under that path. The active skill entrypoint is the directory content itself, not plugin packaging metadata.

如需全局启用某个技能，把完整技能目录放入上述路径。Codex 使用的是技能目录本身，而不是插件打包层的元数据。

## Sync Script / 同步脚本

`sync-codex-global.ps1` exports the current global Codex setup into this repository:

`sync-codex-global.ps1` 用于把当前全局 Codex 配置导出到本仓库：

- copies `AGENTS.md` from the user Codex config;
- copies installed skill directories from `C:\Users\KSG\.codex\skills`;
- keeps repository-local files listed in the script's preserve list, including `LICENSE` and this `README.md`;
- stages and commits changes with Git;
- pushes to the remote default branch unless `-SkipPush` is used.

- 从用户 Codex 配置复制 `AGENTS.md`；
- 从 `C:\Users\KSG\.codex\skills` 复制已安装技能目录；
- 保留脚本内保留名单中的仓库本地文件，包括 `LICENSE` 和本 `README.md`；
- 使用 Git 暂存并提交变更；
- 默认推送到远端默认分支，除非传入 `-SkipPush`。

Recommended dry run:

建议先执行预演：

```powershell
pwsh -NoProfile -File .\sync-codex-global.ps1 -WhatIf
```

Sync without pushing:

同步但不推送：

```powershell
pwsh -NoProfile -File .\sync-codex-global.ps1 -SkipPush
```

Warning: the script uses a force push when pushing to the remote default branch. Review the staged diff before running it without `-WhatIf` or `-SkipPush`.

注意：该脚本推送时会对远端默认分支执行 force push。不带 `-WhatIf` 或 `-SkipPush` 运行前，请先审查暂存差异。

## Requirements / 环境要求

- Windows PowerShell or PowerShell 7.
- Git CLI.
- GitHub CLI (`gh`) when remote/default-branch detection and push are needed.
- A configured Codex global skills directory at `C:\Users\KSG\.codex\skills`.

- Windows PowerShell 或 PowerShell 7。
- Git 命令行。
- 需要识别远端仓库、默认分支或推送时，需要 GitHub CLI (`gh`)。
- 已配置的 Codex 全局技能目录：`C:\Users\KSG\.codex\skills`。

## License / 许可

This repository is proprietary and all rights are reserved. See `LICENSE`. No use, copying, modification, distribution, commercial use, service hosting, or model-training use is allowed without prior written permission.

本仓库采用专有许可并保留全部权利。详见 `LICENSE`。未经事先书面授权，不允许使用、复制、修改、分发、商用、托管为服务或用于模型训练。
