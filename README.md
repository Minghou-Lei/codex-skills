# codex-skills

个人 Codex 技能仓库，用于备份、整理和同步基于 `SKILL.md` 的可复用 agent 工作流。

这个仓库不是应用项目，不需要安装依赖后运行服务。它保存的是 Codex 的全局执行约束、任务技能、工程流程、脚本、模板、参考资料和少量资源文件。

## 仓库内容

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 全局 Codex 执行契约，定义协作方式、安全边界、验证标准和输出格式。 |
| `README.md` | 当前仓库说明、技能索引和维护流程。 |
| `sync-codex-global.ps1` | Windows PowerShell 同步脚本，把本机 Codex 全局配置导出到本仓库。 |
| `<skill-name>/SKILL.md` | 单个技能的入口说明，包含触发条件、工作流和约束。 |
| `<skill-name>/agents/` | 某些技能附带的 agent 配置。 |
| `<skill-name>/assets/` | 某些技能附带的图片、图标或示例资源。 |
| `<skill-name>/references/` | 某些技能附带的参考文档。 |
| `<skill-name>/scripts/` | 某些技能附带的辅助脚本。 |
| `<skill-name>/templates/` | 某些技能附带的模板文件。 |
| `<skill-name>/themes/` | 某些技能附带的主题定义。 |

典型结构：

```text
.
├── AGENTS.md
├── LICENSE
├── README.md
├── sync-codex-global.ps1
├── <skill-name>/
│   └── SKILL.md
├── oh-my-mermaid/
│   ├── omm-push/
│   │   └── SKILL.md
│   ├── omm-scan/
│   │   └── SKILL.md
│   └── omm-view/
│       └── SKILL.md
└── ...
```

## 使用方式

Codex 从本机全局技能目录发现技能：

```text
C:\Users\KSG\.codex\skills
```

把一个技能目录复制到该路径即可启用。示例：

```powershell
Copy-Item -LiteralPath ".\rdc-cli" -Destination "$env:USERPROFILE\.codex\skills\rdc-cli" -Recurse -Force
```

分组技能需要保持目录结构。示例：

```powershell
Copy-Item -LiteralPath ".\oh-my-mermaid" -Destination "$env:USERPROFILE\.codex\skills\oh-my-mermaid" -Recurse -Force
```

启用后，在 Codex 会话中直接描述任务或点名技能即可触发。技能是否触发由 `SKILL.md` 中的 `description` 和正文规则决定。

## 同步模型

当前仓库的主要数据流是：

```text
C:\Users\KSG\.codex  ->  C:\Users\KSG\codex-skills  ->  Git remote
```

也就是说，本仓库主要作为本机 Codex 全局配置的导出、备份和版本化位置。仓库内目前只有导出脚本，没有对另一台机器的一键导入脚本。

### 同步脚本

`sync-codex-global.ps1` 会从本机全局 Codex 配置导出内容到仓库：

1. 读取 `C:\Users\KSG\.codex\AGENTS.md`，不存在时回退到 `C:\Users\KSG\AGENTS.md`。
2. 读取 `C:\Users\KSG\.codex\skills` 下的技能目录。
3. 保留仓库顶层的 `.git`、`.gitignore`、`LICENSE`、`README.md`、`sync-codex-global.ps1`。
4. 删除其他顶层条目，再复制当前全局技能目录。
5. 使用 `git add -A` 暂存改动。
6. 如果有暂存改动，则创建提交：`sync: export codex global agents and skills`。
7. 默认执行 `git push --force origin HEAD:<defaultBranch>`，除非使用 `-SkipPush`。

脚本依赖 `git` 和 `gh`，并通过 `gh repo view` 解析远程仓库和默认分支。

先预览，不改文件：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1 -WhatIf
```

只导出并本地提交，不推送：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1 -SkipPush
```

导出、提交并强制推送到远程默认分支：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1
```

同步脚本会重建仓库顶层技能目录，并且默认强制推送。执行真实同步前优先使用 `-WhatIf`；需要人工审查时使用 `-SkipPush`。

## 技能索引

### 工程执行

| 技能 | 用途 |
| --- | --- |
| `api-and-interface-design` | 设计稳定 API、模块边界、前后端契约和公共接口。 |
| `ci-cd-and-automation` | 配置和维护 CI/CD、质量门禁、测试运行器和部署自动化。 |
| `code-comment` | 创建、修改或审查代码注释、文档注释、API 文档和文件头。 |
| `code-review-and-quality` | 从缺陷、风险、可维护性和测试性角度做代码审查。 |
| `code-simplification` | 在不改变行为的前提下简化代码结构。 |
| `debugging-and-error-recovery` | 系统化定位测试失败、构建失败和异常行为的根因。 |
| `deprecation-and-migration` | 管理废弃、迁移、兼容层和过渡计划。 |
| `git-workflow-and-versioning` | 处理分支、提交、版本、diff、冲突和协作流程。 |
| `incremental-implementation` | 把较大实现拆成小的、可回退、可验证步骤。 |
| `performance-optimization` | 定位和优化性能瓶颈、加载时间和关键指标。 |
| `security-and-hardening` | 加固输入、认证、存储、依赖和外部集成面。 |
| `shipping-and-launch` | 准备发布、灰度、监控、回滚和上线检查。 |
| `source-driven-development` | 基于官方文档和权威来源做实现决策。 |
| `svn-workflow` | 处理 SVN 或 Git/SVN 混合仓库中的状态、diff、提交、冲突、编码和 externals。 |
| `test-driven-development` | 用测试驱动功能实现、缺陷修复和行为变更。 |

### 规划、文档与上下文

| 技能 | 用途 |
| --- | --- |
| `context-engineering` | 优化 agent 上下文、证据选择、规则文件和任务输入组织。 |
| `documentation-and-adrs` | 编写工程文档、ADR、背景说明和决策记录。 |
| `idea-refine` | 用发散和收敛流程打磨想法。 |
| `planning-and-task-breakdown` | 把规格或需求拆成有序、可执行的任务。 |
| `spec-driven-development` | 在编码前澄清规格、需求和验收标准。 |
| `using-agent-skills` | 发现、选择并调用合适的 agent 技能。 |

### 前端、浏览器与可视化产物

| 技能 | 用途 |
| --- | --- |
| `algorithmic-art` | 用 p5.js、随机种子和交互参数创建原创生成艺术。 |
| `brand-guidelines` | 将 Anthropic 风格的颜色、字体和视觉规范应用到产物。 |
| `browser-testing-with-devtools` | 使用真实浏览器、DOM、控制台、网络和性能数据测试页面。 |
| `canvas-design` | 创建 PNG、PDF、海报和静态视觉设计。 |
| `frontend-design` | 设计高质量、可交付的网页、组件、页面和应用界面。 |
| `frontend-ui-engineering` | 构建生产质量的 UI 状态、组件、布局、交互和集成逻辑。 |
| `pdf` | 读取、创建或审查需要渲染和版面判断的 PDF。 |
| `playwright` | 通过 Playwright 自动化真实浏览器，完成导航、表单、截图、抽取和 UI 调试。 |
| `theme-factory` | 为 slides、docs、reports、HTML 等产物应用预设或生成主题。 |
| `web-artifacts-builder` | 使用 React、Tailwind CSS、shadcn/ui 构建复杂 HTML artifacts。 |

### 图形、引擎与本地工具

| 技能 | 用途 |
| --- | --- |
| `encoding-guardian` | 保护和恢复 GBK、ANSI、UTF-8-BOM、UTF-16、Big5、Shift-JIS 等遗留源码编码。 |
| `hatch-pet` | 创建、修复、验证、预览和打包 Codex 动画宠物 spritesheet。 |
| `rdc-cli` | 分析 RenderDoc `.rdc` 捕获、draw call、pipeline state、shader、资源和 render target。 |

### 多 agent 与编排

| 技能 | 用途 |
| --- | --- |
| `paseo` | 管理 agents 和 worktrees 的基础参考。 |
| `paseo-advisor` | 启动单个 advisor agent 获取第二意见。 |
| `paseo-committee` | 组织两个高推理 agent 做根因分析和方案审查。 |
| `paseo-epic` | 面向大任务的研究、计划、对抗审查、分阶段实现、审计和交付流程。 |
| `paseo-handoff` | 将当前任务和上下文移交给另一个 agent。 |
| `paseo-loop` | 运行 agent 循环，直到满足退出条件。 |
| `paseo-orchestrate` | 已废弃，重定向到 `paseo-epic`。 |
| `vibe-kanban-agent-protocol` | 约定 Vibe Kanban 多 agent 的 issue 关系、workspace、集成和清理流程。 |

### oh-my-mermaid

| 技能 | 用途 |
| --- | --- |
| `oh-my-mermaid/omm-scan` | 扫描代码库并生成或更新 `.omm/` 架构文档。 |
| `oh-my-mermaid/omm-view` | 启动本地 oh-my-mermaid Web 查看器。 |
| `oh-my-mermaid/omm-push` | 登录、关联项目并推送 `.omm/` 架构文档到 oh-my-mermaid 云端。 |

## 新增或维护技能

新增技能时建议保持以下约定：

1. 每个技能目录自包含，入口文件固定为 `SKILL.md`。
2. `SKILL.md` 写清楚触发条件、适用场景、工作流、输入、输出和约束。
3. 脚本放在 `scripts/`，参考资料放在 `references/`，模板放在 `templates/`，资源放在 `assets/`。
4. 第三方资源或字体的许可证放在对应技能目录内。
5. 不把本机 token、cookie、私有 endpoint、账号配置、临时缓存或大体积生成输出提交到仓库。
6. 修改技能后同步更新本 README 的索引。

提交前至少检查：

```powershell
git status --short
```

如果修改了同步脚本，先运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\sync-codex-global.ps1 -WhatIf
```

## 安全说明

- `AGENTS.md` 是 agent 执行契约，不是普通说明文档；改动会影响后续会话行为。
- `SKILL.md` 是行为配置；改动触发条件或流程前应确认不会误触发。
- 同步脚本会删除仓库顶层非保留条目，并可能强制推送远程默认分支。
- 导入外部技能前先审查脚本、命令、权限请求、网络行为和 license。
- 含有遗留编码文件时优先使用 `encoding-guardian` 的 snapshot / restore 流程。

## License

仓库级许可证见 `LICENSE`。

部分技能目录包含独立的 `LICENSE.txt` 或资源许可证说明。对这些目录，其技能级许可证优先适用于该目录内的材料。
