# Codex Skills / Codex 技能仓库

本仓库保存一组面向 Codex 的本地技能与全局路由说明，用于把常用工程约束、编码规范、版本控制流程和多 Agent 协作协议沉淀为可复用的 `SKILL.md`。

This repository stores local Codex skills and routing instructions. It turns recurring engineering rules, coding conventions, version-control workflows, and multi-agent coordination protocols into reusable `SKILL.md` packages.

## Contents / 内容

| Skill / 技能 | Purpose / 用途 | License source / 许可来源 |
| --- | --- | --- |
| `algorithmic-art` | Seeded p5.js generative art, flow fields, particle systems, and interactive visual parameter exploration. / 用于基于 p5.js 的生成艺术、流场、粒子系统和交互式参数探索。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |
| `brand-guidelines` | Applies Anthropic brand colors, typography, and visual style to artifacts. / 为制品应用 Anthropic 品牌色、字体和视觉风格。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |
| `canvas-design` | Creates visual art, posters, PDFs, and static design outputs. / 创建视觉艺术、海报、PDF 和静态设计输出。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |
| `code-comment` | Enforces Chinese code-comment quality gates for generated, modified, reviewed, or documented code. / 为代码生成、修改、审查和文档化执行中文注释质量闸门。 | Repository license unless otherwise stated / 未另行声明时适用仓库许可 |
| `encoding-guardian` | Protects mixed-encoding legacy files, especially GBK/ANSI and UTF-8-BOM source trees. / 保护混合编码旧工程文件，尤其是 GBK/ANSI 与 UTF-8-BOM 源码。 | Repository license unless otherwise stated / 未另行声明时适用仓库许可 |
| `frontend-design` | Creates production-grade frontend interfaces and visual web artifacts. / 创建生产级前端界面和视觉 Web 制品。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |
| `svn-workflow` | Maps Git habits to SVN-safe workflows for projects that use Subversion or mixed SVN/Git. / 为 SVN 或 SVN/Git 混合项目提供安全工作流。 | Repository license unless otherwise stated / 未另行声明时适用仓库许可 |
| `theme-factory` | Applies preset themes, color systems, and typography to slides, docs, reports, and HTML artifacts. / 为幻灯片、文档、报告和 HTML 制品应用主题、配色和字体系统。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |
| `vibe-kanban-agent-protocol` | Defines issue topology, workspace usage, integration, cleanup, and leadership rules for Vibe Kanban multi-agent work. / 定义 Vibe Kanban 多 Agent 协作中的任务关系、工作区、集成、清理和负责人规则。 | Repository license unless otherwise stated / 未另行声明时适用仓库许可 |
| `web-artifacts-builder` | Builds complex HTML artifacts with React, Tailwind CSS, shadcn/ui, routing, and state management. / 使用 React、Tailwind CSS、shadcn/ui、路由和状态管理构建复杂 HTML 制品。 | See skill-local `LICENSE.txt` / 见技能目录内 `LICENSE.txt` |

## Repository Layout / 仓库结构

```text
.
├── AGENTS.md
├── LICENSE
├── README.md
├── sync-codex-global.ps1
├── algorithmic-art/
├── brand-guidelines/
├── canvas-design/
├── code-comment/
├── encoding-guardian/
├── frontend-design/
├── svn-workflow/
├── theme-factory/
├── vibe-kanban-agent-protocol/
└── web-artifacts-builder/
```

Each skill directory contains a `SKILL.md`. Some skills also include `agents/`, `references/`, `scripts/`, `templates/`, `themes/`, fonts, or skill-local license files.

每个技能目录都包含 `SKILL.md`。部分技能还包含 `agents/`、`references/`、`scripts/`、`templates/`、`themes/`、字体或技能目录内许可文件。

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
powershell -NoProfile -File .\sync-codex-global.ps1 -WhatIf
```

Sync without pushing:

同步但不推送：

```powershell
powershell -NoProfile -File .\sync-codex-global.ps1 -SkipPush
```

Warning: the script uses a force push when pushing to the remote default branch. Review the staged diff before running it without `-WhatIf` or `-SkipPush`.

注意：该脚本推送时会对远端默认分支执行 force push。不带 `-WhatIf` 或 `-SkipPush` 运行前，请先审查暂存差异。

## Licensing / 许可说明

This repository uses a proprietary root `LICENSE` for Minghou-Lei's original materials, repository-level documentation, routing rules, sync scripts, selection, and arrangement.

本仓库根目录 `LICENSE` 对 Minghou-Lei 的原创材料、仓库级文档、路由规则、同步脚本、选编与编排适用专有许可。

Some skill directories may contain Third-Party Components, including third-party or open-source materials. Those materials remain governed by their own license notices, license files, headers, and upstream terms. The root `LICENSE` does not remove, replace, sublicense, or restrict rights that a third-party open-source license grants for that third-party component.

部分技能目录可能包含第三方或开源材料。这些材料仍受其自身许可声明、许可文件、文件头和上游条款约束。根目录 `LICENSE` 不会移除、替换、再授权或限制第三方开源许可证对对应第三方组件授予的权利。

When adding open-source skills, keep the original `LICENSE`, `LICENSE.txt`, `NOTICE`, copyright notices, attribution text, and source references with the imported skill.

添加开源技能时，请保留导入技能自带的 `LICENSE`、`LICENSE.txt`、`NOTICE`、版权声明、署名文本和来源引用。

This README is a practical repository note, not legal advice. For distribution, commercial use, or mixed-license reuse, review each component's license and consult qualified counsel when needed.

本 README 只是仓库使用说明，不构成法律意见。涉及分发、商用或混合许可证复用时，请逐项审查组件许可证，并在需要时咨询专业法律人士。

## Requirements / 环境要求

- Windows PowerShell or PowerShell 7.
- Git CLI.
- GitHub CLI (`gh`) when remote/default-branch detection and push are needed.
- A configured Codex global skills directory at `C:\Users\KSG\.codex\skills`.

- Windows PowerShell 或 PowerShell 7。
- Git 命令行。
- 需要识别远端仓库、默认分支或推送时，需要 GitHub CLI (`gh`)。
- 已配置的 Codex 全局技能目录：`C:\Users\KSG\.codex\skills`。
