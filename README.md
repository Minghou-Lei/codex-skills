# Codex Skills

本仓库保存本机 Codex 技能、全局 Agent 约束和同步脚本。它的目标不是发布应用，而是把常用工程方法、文档规范、调试流程、前端设计、浏览器验证、多 Agent 协作等工作方式沉淀为可复用的 `SKILL.md` 目录。

## 当前状态

- 技能目录：33 个，且每个目录都包含 `SKILL.md`。
- 根目录文件：`.gitignore`、`AGENTS.md`、`LICENSE`、`README.md`、`sync-codex-global.ps1`。
- 同步方向：从 `C:\Users\KSG\.codex` 导出到本仓库。
- 主要入口：Codex 通过技能目录内的 `SKILL.md` 识别和加载技能。

## 技能目录

| 技能 | 用途 | 附带资源 | 许可 |
| --- | --- | --- | --- |
| `algorithmic-art` | 使用 p5.js 创建带随机种子和交互参数的生成艺术。 | `templates/` | 技能内许可 |
| `api-and-interface-design` | 设计稳定的 API、模块边界和公共接口。 | - | 仓库许可 |
| `brand-guidelines` | 将 Anthropic 品牌色、字体和视觉风格应用到制品。 | - | 技能内许可 |
| `browser-testing-with-devtools` | 在真实浏览器中测试、检查和调试页面。 | - | 仓库许可 |
| `canvas-design` | 创建 PNG、PDF、海报和静态视觉设计输出。 | - | 技能内许可 |
| `ci-cd-and-automation` | 设计和维护 CI/CD 与自动化流水线。 | - | 仓库许可 |
| `code-comment` | 为代码生成、修改、重构、审查和文档化提供中文注释规范。 | `references/` | 仓库许可 |
| `code-review-and-quality` | 从缺陷、质量、风险和测试角度进行代码审查。 | - | 仓库许可 |
| `code-simplification` | 简化代码结构，提高可读性和维护性。 | - | 仓库许可 |
| `context-engineering` | 优化 Agent 上下文组织、材料选择和任务输入。 | - | 仓库许可 |
| `debugging-and-error-recovery` | 使用系统化方法定位根因并恢复错误状态。 | - | 仓库许可 |
| `deprecation-and-migration` | 管理废弃、迁移和兼容性过渡。 | - | 仓库许可 |
| `documentation-and-adrs` | 编写项目文档，记录架构决策和工程背景。 | - | 仓库许可 |
| `encoding-guardian` | 保护和恢复 GBK、ANSI、UTF-8-BOM 等混合编码文件。 | `agents/`、`scripts/` | 仓库许可 |
| `frontend-design` | 创建具有高设计质量的生产级前端界面。 | - | 技能内许可 |
| `frontend-ui-engineering` | 构建生产质量的 UI、状态和交互。 | - | 仓库许可 |
| `git-workflow-and-versioning` | 组织分支、提交、版本控制和协作流程。 | - | 仓库许可 |
| `idea-refine` | 通过发散与收敛流程迭代打磨想法。 | `scripts/` | 仓库许可 |
| `incremental-implementation` | 将改动拆成可验证的小步交付。 | - | 仓库许可 |
| `pdf` | 阅读、创建或审查需要渲染和版式判断的 PDF。 | `agents/`、`assets/` | 技能内许可 |
| `performance-optimization` | 定位并优化性能瓶颈、加载时间和核心指标。 | - | 仓库许可 |
| `planning-and-task-breakdown` | 将规格或需求拆解成有序、可执行的任务。 | - | 仓库许可 |
| `playwright` | 用真实浏览器执行导航、表单、截图、抽取和 UI 调试。 | `agents/`、`assets/`、`references/`、`scripts/` | 技能内许可 |
| `security-and-hardening` | 加固输入处理、认证、存储和外部集成等安全面。 | - | 仓库许可 |
| `shipping-and-launch` | 准备生产发布、监控、灰度和回滚策略。 | - | 仓库许可 |
| `source-driven-development` | 让实现决策基于官方文档和权威来源。 | - | 仓库许可 |
| `spec-driven-development` | 在编码前先澄清规格、需求和验收标准。 | - | 仓库许可 |
| `svn-workflow` | 为 SVN 或 Git/SVN 混合仓库提供状态、差异、提交和冲突处理流程。 | `agents/` | 仓库许可 |
| `test-driven-development` | 用测试驱动功能实现和缺陷修复。 | - | 仓库许可 |
| `theme-factory` | 为幻灯片、文档、报告和 HTML 制品应用主题系统。 | `themes/` | 技能内许可 |
| `using-agent-skills` | 发现、选择并调用合适的 Agent 技能。 | - | 仓库许可 |
| `vibe-kanban-agent-protocol` | 约定 Vibe Kanban 多 Agent 的任务关系、工作区和集成流程。 | `agents/`、`references/` | 仓库许可 |
| `web-artifacts-builder` | 使用现代前端技术构建复杂 HTML 制品。 | `scripts/` | 技能内许可 |

## 仓库结构

```text
.
├── AGENTS.md
├── LICENSE
├── README.md
├── sync-codex-global.ps1
├── <skill-name>/
│   └── SKILL.md
└── ...
```

每个技能目录至少包含一个 `SKILL.md`。部分技能还会附带 `agents/`、`assets/`、`references/`、`scripts/`、`templates/` 或 `themes/`，用于保存子 Agent、参考材料、自动化脚本、模板和主题资源。

## 使用方式

Codex 从以下全局目录发现本地技能：

```text
C:\Users\KSG\.codex\skills
```

要全局启用某个技能，需要把完整技能目录放入该路径。技能目录本身就是入口，不依赖额外的打包元数据。

## 同步脚本

`sync-codex-global.ps1` 用于把当前全局 Codex 配置导出到本仓库：

- 从 `C:\Users\KSG\.codex\AGENTS.md` 复制全局 Agent 指令。
- 从 `C:\Users\KSG\.codex\skills` 复制已安装技能目录。
- 保留仓库本地文件：`.git`、`.gitignore`、`LICENSE`、`README.md`、`sync-codex-global.ps1`。
- 使用 Git 暂存并提交变更。
- 默认推送到远端默认分支；传入 `-SkipPush` 时只在本地提交。
- 传入 `-WhatIf` 时预览同步计划，不实际提交或推送。

建议先预演：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1 -WhatIf
```

只提交不推送：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1 -SkipPush
```

完整同步：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1
```

## 维护约定

- 新增技能时，为目录添加 `SKILL.md`，并在本 README 的技能目录表中登记。
- 如果技能包含第三方来源或独立许可，在技能目录内保留对应 `LICENSE.txt` 或等效说明。
- 修改 `AGENTS.md` 或全局技能后，使用同步脚本把当前状态导出到仓库。
- 保持技能说明短而具体：说明触发时机、工作流程、输入输出和重要限制。

## 许可

仓库整体许可见 `LICENSE`。部分技能目录包含独立 `LICENSE.txt`，这些目录以技能内许可为准。
