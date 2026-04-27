---
name: vibe-kanban-agent-protocol
description: Use when multiple Vibe Kanban agents need a shared protocol for issue topology, `Relationships` such as `Blocks`, `Blocked by`, `Related to`, and `Duplicate of`, issue-linked `workspace` usage, staged integration to `main`, safe cleanup across planner, executor, reviewer, integrator, and cleanup roles, or when a user explicitly appoints an agent as the project leader.
---

# Vibe Kanban Agent Protocol

## Overview

这个 skill 定义的是所有 Vibe Kanban agents 共用的操作协议，不是某一种 agent 的专属流程。

中心原则只有四个：

- issue 是执行、审查、集成和清理的最小责任单元
- agent 的差异在职责，不在协议
- `Relationships`、issue-linked `workspace`、以及 staged integration 是事实来源
- 如果当前 issue 拓扑已经不再可独立审查、可安全合并或可清晰归属，就停止执行并重塑结构

## When to Use / When Not to Use

在以下场景使用：

- 多个 Vibe Kanban agents 需要围绕同一组 issues 协作
- 需要定义 issue topology、ownership、blocking 关系、批次边界和集成路径
- 需要从 issue 创建并追踪 `workspace`
- 需要把真实依赖显式落到 `Relationships`
- 需要约束 staged integration、`main` 回并和安全 cleanup
- 用户明确任命某个 agent 为“领导者”或项目领导，并期望它承担治理、调度、追踪和决策责任，而不是亲自实现代码

在以下场景不要使用：

- 工作本身只是单分支、小范围修改，不需要 issue topology 或多 agent 协作
- 当前项目没有 issue-linked `workspace` 或 `vk/*` 分支语义
- 用户只是在问某个项目特有的桌面交付、Tauri、Rust、README 发布细节

## Leader Appointment Semantics

当用户明确说“你现在是这个项目的领导者”或等价表达时，这不是一句口头称呼，而是角色切换。

默认语义：

- 被任命为领导者的 agent 默认停留在治理层，而不是执行层
- 领导者默认承担 planner + coordinator 的职责组合，而不是 executor
- 领导者应维护 parent batch / child issue 的推进顺序、ownership、relationship、workspace linkage、status 和下一步决策
- 领导者可以使用 Vibe Kanban 启动、复用、命名和跟踪 issue-linked `workspace` / session，但不应把自己变成实际编码的人

领导者在默认情况下应该做：

- 判断当前应推进哪个 parent issue / child issue
- 决定是 `keep-single-issue`、`split-into-peer-issues` 还是 `promote-to-new-batch`
- 明确哪些 child issue 可以进入 `In progress`
- 从正确的 child issue 创建或复用 `workspace`
- 向 executor 下发边界清晰的执行指令，并持续追踪执行状态
- 汇总 blocker、风险、验收状态和是否具备进入下一 child issue / 下一 batch 的条件

领导者在默认情况下不应做：

- 直接在当前仓库里开始实现代码
- 因为用户说“执行某个 issue”就把自己切成 executor
- 跳过 issue-linked `workspace` / session，直接在 parent issue 视角下手改实现
- 在未明确建模 `parallel-safe` 的情况下并行启动多个 child issue

如果用户在任命领导者之后又说“执行 MIN-105”之类的话，默认解释应是：

- 由领导者使用 Vibe Kanban 推进该 issue 的执行
- 选择当前应进入执行态的 child issue
- 启动或复用对应的 issue-linked `workspace` / session
- 派发 executor 执行并跟踪结果

只有在用户明确改口，例如“领导者本人亲自实现”或明确撤销领导者语义时，领导者才应转入 executor 行为。

## Task Assignment Contract

只要 leader、planner 或其他上游 agent 向下游 agent 派发一个具体任务，委派消息都必须显式写出以下两项，不能让接收方自己猜：

- 要求目标 agent 使用 `C:\Users\KSG\.codex\skills\vibe-kanban-agent-protocol\SKILL.md`
- 明确指派目标 agent 在本次任务中的协议角色：`leader`、`planner`、`executor`、`reviewer`、`integrator`、`cleanup` 之一

最小委派格式至少应覆盖：

- 当前 issue / task scope
- assigned role = `<role>`
- required skill = `C:\Users\KSG\.codex\skills\vibe-kanban-agent-protocol\SKILL.md`
- blocker / dependency / workspace 边界
- 期望产出或回报方式

如果委派消息没有显式包含 skill 或 role，默认应视为不完整委派。发送方应补发清晰委派，而不是让接收方自行推断自己是否需要使用该 protocol、或应扮演哪个角色。



## Subagent Coordination Discipline

这部分规则适用于 leader、planner 或任何会派发 child / worker / executor 的上游 agent。目标是避免主 agent 因急躁、误判或 ownership 失控而过早打断、接管或关闭仍在正常推进的子 agent。

### Default Collaboration Mode = `trust-first`

默认协作模式不是抢占式调度，而是 `trust-first`：

- 只要 child 未报告阻塞、未超过检查点窗口、未发生明确冲突，就默认视为正常工作中
- 暂时没有代码落地，不等于没有进展
- 主 agent 不得把自己的焦虑感、推进压力或“怕撞文件”的担心，当作打断或接管依据
- 优先等待 child 完成一个自然工作单元，再决定是否重分配、集成或回收 ownership

### What Counts as Normal Progress

以下情况都视为“正常工作中”，主 agent 不得接管：

- child 刚收到任务，正在阅读代码、确认入口、梳理实现边界
- child 尚未提交文件修改，但未报告阻塞
- child 正在运行测试、复现失败、整理结果或准备一次性回报
- child 尚未主动回报，但仍处于约定检查点窗口内
- child 正在按既定 scope 推进，且没有越界修改、ownership 冲突或 blocker 漏建模

默认解释必须是：

- no landed code != no progress
- no immediate reply != blocked
- no diff yet != reclaimable

### Waiting Windows and Checkpoints

分配 child 任务后，主 agent 必须先给出观察窗口，而不是立即追问。

推荐默认：

- 只读分析 / grep / 入口定位类任务：`2 + 2` 分钟两阶段观察
- 小型实现任务：`5 + 5` 分钟两阶段观察
- 多文件实现 + 测试 / 调试任务：`5 + 10` 分钟两阶段观察

行为规则：

1. 第一观察窗口：
   - 静默等待
   - 不催办
   - 不打断
   - 不接管
   - 不修改 child-owned 文件

2. 第一观察窗口结束后：
   - 如无阻塞信号，只允许发送一次软检查点消息
   - 不得要求 child 立即停止、立即回复或立即交还任务

3. 第二观察窗口：
   - 继续等待 child 在自然检查点回报
   - 仍不得因为“尚未落代码”而接管

4. 第二观察窗口结束后：
   - 只可进入“接管评估”
   - 不能自动等价成“主 agent 现在可以直接接管”

如果项目或任务有更合适的 SLA，可以覆盖上述分钟数；但必须保留“观察窗口 -> 软检查点 -> 接管评估”的顺序，不得退化成刚派发就催办。

### Soft Checkpoint vs Hard Interrupt

普通跟进只能使用软检查点，不得把一般性状态确认写成停机指令。

#### Soft checkpoint（允许）

- “继续按原任务推进；到自然检查点后汇报：改动文件、测试结果、阻塞项。”
- “如遇阻塞请主动报告；若无阻塞，无需即时回复。”
- “完成当前小步后再同步状态，不改变当前执行。”
- “先不要扩 scope，完成当前子任务后一次性回报。”

#### Hard interrupt（默认禁止）

- “停止继续实现”
- “立即汇报当前状态”
- “不要再继续编辑”
- “我来接管这批文件”
- “先切到汇报态，避免后面撞文件”

只有以下情况允许硬中断：

- 用户明确要求停止、改派或取消
- 发生明确的文件边界冲突，且需要立即止损
- child 明确报告应当终止
- 当前任务需要硬回滚或撤销

### Ownership and Reclaim

一旦某组文件或 write set 被分配给某个 child，该范围在任务完成前默认视为 child-owned。

主 agent 必须遵守：

- 不得因为“担心后面撞文件”而抢先修改 child-owned 文件
- 如需推进相邻工作，只能修改非重叠文件
- 不得一边口头说“我不打断它”，一边自行补它的空缺并创建同组文件
- 不得把“避免冲突”解释成“先停掉 child，由主 agent 自己实现”

只有满足以下任一条件时，主 agent 才可回收 child 任务或 ownership：

1. child 明确回复 `BLOCKED` / 无法继续
2. child 明确说明尚未开始且主动交还任务
3. child 超过约定检查点窗口，且没有任何有效进展回报
4. 发生明确的文件边界冲突，必须重分配 ownership
5. 用户明确要求取消或改派任务

除上述情况外，以下都不是合法回收理由：

- “还没落代码”
- “我觉得它太慢”
- “我先补它的空缺”
- “我想更快推进主线”
- “我怕后面和它改同一组文件”
- “暂时没看到 diff”

### Dispatch and Follow-up Discipline

对 child 派发任务后，主 agent 的默认顺序必须是：

1. 明确 scope、role、write set、边界和回报格式
2. 进入观察窗口
3. 仅在窗口后发送一次软检查点
4. 再等待自然检查点结果
5. 必要时才进入接管评估
6. 满足 reclaim 条件后才允许改派或接管

看到 child 暂无代码落地时，必须按以下顺序判断：

1. child 是否已明确阻塞？
2. 是否已超过检查点窗口？
3. 是否存在明确文件冲突？
4. 是否有用户显式要求停止或改派？
5. 若以上都否：保持等待，不打断，不接管

### Child Task Completion and Session Closure

在以下情况之前，不应主动关闭 child session / worker：

- child 已完成自然工作单元并回报结果
- child 已明确说明无变更并主动交还任务
- child 已明确阻塞且上游决定终止或改派
- 用户明确要求结束该 child

主 agent 不得仅因以下现象就关闭 child：

- 尚未看到文件落地
- 尚未即时回复
- 主 agent 想自己接手这批文件
- 主 agent 想减少并行不确定性

### Subagent Anti-patterns

以下都属于协议级反模式：

- “Child X 还没落代码，我直接接管。”
- “先把它切到汇报态，避免后面撞文件。”
- “停止继续实现，立即汇报当前状态。”
- 在 child 仍正常推进时，主 agent 自行补 child 负责的空缺
- 未满足 reclaim 条件就关闭 child，并开始修改同组文件
- 把“没有 diff”自动等价成“没有工作”

## Phase Gates

### `Plan-only`

允许：

- 阅读当前 issue 集、role 分工、topology、relationships、ownership 和批次边界
- 选择 flat issue topology 或可选 hierarchy
- 决定 `keep-single-issue`、`split-into-peer-issues`、`promote-to-new-batch`
- 决定 `parallel-safe`、`sequential-in-batch`、`merge-into-peer`
- 在创建任何 `workspace` 之前，先补齐 topology 和真实 blocker

禁止：

- 直接开始实现
- 创建或删除 `workspace`
- 创建或删除 `vk/*` 分支
- 合并集成分支或回并 `main`
- 执行发布动作
- 进行 `git reset --hard HEAD`、`git clean -fdx` 一类 destructive cleanup

### `Execute`

允许：

- executor 只对已分配 issue 启动执行
- 只从对应 issue 本身创建 `workspace`
- 保持 issue -> `workspace` -> branch 关联
- 在当前 issue 的已定义 scope 内完成实现并准备集成

必须：

- 在启动执行前先确认 topology、ownership、relationships 已经足够清晰
- 如果某个 issue 必须等待另一个 issue 完成，且这件事尚未显式建模，就先创建或请求创建 `blocking` relationship，再继续
- 如果执行中暴露隐藏依赖、新批次边界或共享核心文件过多，立即停下并重塑 topology，而不是继续硬做

### `Cleanup`

默认语义：

- 只清理当前错误批次对应的 `workspace` 和匹配的 `vk/*` 分支
- 保留历史上已经完成并吸收进 `main` 的批次和上下文

升级到硬清理的前提：

- 用户明确要求完整重置
- 用户明确接受未提交修改和本地生成物可能丢失的风险
- 清理目标已经被验证为当前工作区，而不是无关批次

## Role Matrix

| Role | Must do | Must not do |
| --- | --- | --- |
| leader | 维护 issue topology、批次顺序、ownership、workspace linkage、执行委派与状态追踪 | 被任命为领导者后直接下场实现，或把“执行 issue”默认理解成自己编码 |
| planner | 定义 issue topology、relationships、ownership、批次边界 | 不在 planning 名义下直接开始实现 |
| executor | 只执行已分配 issue，尊重 blocker，保持 issue-linked `workspace` | 不越权改 topology，不跳过 blocker |
| reviewer | 检查 scope、relationship、workspace linkage、可合并性 | 不把 review 退化成只看代码 diff |
| integrator | 吸收批次产出、推进集成分支、回并 `main` | 不在 unresolved batch 上继续堆叠新批次 |
| cleanup | 只清当前错误批次，保留已吸收上下文 | 未经明确授权做 destructive reset |

## Cross-role Commit Hygiene

以下规则不区分角色。只要某个 agent 准备提交、准备吸收到集成分支、准备回并 `main`、或准备宣称“可合并”，都必须执行。

### 临时文件识别

术语 = 临时文件：构建产物、缓存、日志、一次性验证输出、解释器缓存、运行中间件，不属于需要审查和长期保留的源码、脚本、schema、样例或正式报告。

常见例子：

- Unreal：`Binaries/`、`DerivedDataCache/`、`Intermediate/`、`Saved/`
- Python：`__pycache__/`、`*.pyc`
- 运行期验证残留：临时导出的中间 JSON、一次性截图、临时 DOM dump、诊断日志

如果某个文件是否属于交付物存在歧义，不要猜。先回答两件事：

- 这个文件是“实现本身”还是“某次运行生成出来的副产物”
- 去掉它以后，issue 的源码意图是否仍然完整可审查

只要答案是“副产物”，默认不应提交。

### 提交前检查

- 在提交前检查当前 branch / workspace 的变更清单，而不是只看编辑过的源码文件
- 在吸收 issue 分支前再次检查一次变更清单，因为执行阶段可能额外生成缓存或日志
- reviewer 和 integrator 不能假设 executor 已经清干净；必须独立复核是否混入临时文件
- 如果发现临时文件，先在当前 issue 分支清理并重新提交，再进入集成分支

最低检查面：

- `git status --short`
- `git diff --name-only`
- 当前 issue 分支相对集成基线的 diff 文件列表

## Core Decisions

### Issue Topology

- `keep-single-issue`: 当前工作仍是一个边界清晰、可独立审查、没有隐藏前置依赖的单一 issue
- `split-into-peer-issues`: 当前工作仍属于同一批次，但已经暴露多个独立写入范围、输出物或依赖单元
- `promote-to-new-batch`: 新发现的工作已经形成新的前置批次或集成基线，后续 issues 依赖它

以下任一情况出现时，不要继续硬做当前 issue：

- 出现两个或以上独立写入范围
- 继续前必须先落地隐藏前置依赖
- 基础设施建设和依赖其结果的功能实现被混在一个 issue 里
- 共享核心文件过多，ownership 不再清晰
- 继续执行会把规划与实现混成一个不可审查的执行单元

### Optional Issue Hierarchy

- `parent_issue_id` / `sub_issues` 仍然是合法能力，但只是可选的 issue hierarchy
- 是否使用 hierarchy 取决于当前项目如何组织 issue，不是所有 agents 的默认前提
- 不要把 hierarchy 当成真实执行依赖的替代物；横向依赖仍然要落到 `Relationships`

### Parallelization

- `parallel-safe`: 写入范围独立，可独立审查，不依赖同级尚未公开的产出
- `sequential-in-batch`: 仍属于当前批次，但需要先拿到同级结果，或会修改共享核心文件
- `merge-into-peer`: 独立性不足，不值得拥有单独的 `workspace`

如果两个 issues 会修改同一组核心文件，不要并行。只能串行，或合并成一个 issue。

### Issue Relationships

- `Relationships` 负责横向关系，不负责 issue hierarchy
- 只要一个 issue 的执行必须等待另一个 issue 完成，就必须创建 `blocking` relationship
- `Blocked by` 是 `blocking` 在对侧 issue 上的显示结果，不是单独的写入类型
- `related` 只用于非阻塞的上下文关联、共享背景或协作提醒，不得替代真实 blocker
- `has_duplicate` 只用于重复 issue 清理，不得表达执行依赖
- 如果只是共享核心文件导致不能并行，但不存在明确的“先产出 A，后做 B”的前置结果，就保持 `sequential-in-batch`，不要伪造 `blocking`

### Workspace, Integration, and Cleanup

- 每个 `workspace` 都必须从对应 issue 本身创建
- 如果使用 `start_workspace` 且提供了非空 `prompt`，默认语义应视为“首个 session 的首轮执行已经被派发”；不要再对这个新 workspace 的首个 session 立刻补发一次等价的 `run_session_prompt`
- 对同一个新 workspace 的首轮执行，二选一即可：要么在 `start_workspace` 里提供 `prompt` 直接启动，要么创建后再显式 `run_session_prompt`；不要两者同时做
- 如果 `start_workspace` 的返回只给了 `workspace_id`，而没有直接给出 execution 细节，正确后续是先 `list_sessions` / 查询执行状态来确认首轮是否已经启动，而不是因为“没看到 execution_id”就重复派发同一任务
- `vk/*` 分支是一次性分支，不是长期协作分支
- 当前批次的产出应先进入集成分支，再吸收回 `main`
- 在当前批次完成吸收之前，不要启动下一批 unresolved work
- 如果同一 parent batch 内存在顺序 child issue，后续 child issue 的 `workspace` 基线必须已经包含前序 child issue 的已接收产出；不要从不包含前序结果的 stale `main` 或其他旧基线直接启动后续 child
- 对于这类顺序 child，允许通过集成分支、显式 merge、cherry-pick 或等价的最小整合方式吸收前序结果；重点是后续 child 的实际执行基线必须完整，而不是名义上“都属于同一个 parent”
- leader、reviewer 和 integrator 在接受后续 child 结果前，必须显式检查它是否真的建立在所需前序产出之上；如果没有，就停止收口，先补齐基线并重新验证
- 在吸收 issue 分支前，先清掉构建产物、缓存、日志和一次性验证输出；例如 Unreal 的 `Binaries/`、`DerivedDataCache/`、`Intermediate/`、`Saved/` 默认不应进入集成分支，除非它们本身就是被审查的交付物
- 项目特定的交付和发布规则不属于这个核心 protocol，应放到补充 reference

## Quick Reference

| Decision | Use when | Next action |
| --- | --- | --- |
| `keep-single-issue` | 当前 issue 仍是一个可独立审查单元 | 继续当前结构 |
| `split-into-peer-issues` | 同一批次下出现多个独立执行单元 | 停止当前执行，重建 peer issues |
| `promote-to-new-batch` | 出现新的前置批次或集成基线 | 停止当前执行，先提升为新 batch |
| `parallel-safe` | 文件集、模块、输出物都隔离 | 可并行启动 |
| `sequential-in-batch` | 同批次内存在顺序约束或共享核心文件 | 在批次内串行执行 |
| `merge-into-peer` | 任务没有足够独立性 | 不单开 `workspace`，并回同级 issue |

| Relationship | Use when | Do not use for |
| --- | --- | --- |
| `blocking` | 真正的执行前置依赖 | 仅仅因为共享文件而不适合并行 |
| `related` | 非阻塞关联、共享背景、协作提醒 | 真实 blocker |
| `has_duplicate` | 重复 issue | 执行依赖或 issue hierarchy |

## Common Mistakes

- 把 hierarchy 当成所有项目都必须有的中心模型
- 把 `Plan-only` 当成执行阶段，提前创建 `workspace` 或分支
- 明明已经需要 `split` 或 `promote`，却继续硬做当前 issue
- 依赖只写在 issue description 里，却没有落到 `Relationships`
- 被任命为领导者后，仍把“执行某个 issue”理解成自己亲自编码，而不是先通过 Vibe Kanban 选择 child issue、派发 executor、追踪状态
- 派发任务时没有显式要求目标 agent 使用 `vibe-kanban-agent-protocol`，也没有明确指派本次角色，导致接收方按各自理解执行
- 使用 `start_workspace(prompt=...)` 创建新 workspace 后，又立刻对首个 session 再发一次等价的 `run_session_prompt`，导致同一 child issue 被重复触发两次
- 同一 parent batch 内，后续 child issue 直接从不包含前序 child 产出的旧基线起 `workspace`，导致后续提交丢掉前序能力，却仍被误判为可接收结果
- executor 越权修改 topology 或绕过 blocker
- 从项目级入口批量创建 `workspace`，导致 issue 关联丢失
- 没做提交前文件清单检查，就把构建产物、缓存、日志和一次性验证输出混进 issue 分支，导致真实源码改动不可审查、集成分支不可安全吸收
- 把“尚未落代码”误判成“没有进展”，从而过早催办、停机或接管 child
- 在检查点窗口内发送“立即汇报”“停止实现”“不要再编辑”之类的硬中断消息
- 未满足 reclaim 条件就回收 child-owned 文件，随后主 agent 自己落同组实现
- 口头上说“不打断 child”，实际却提前创建 child 负责的新文件并关闭 child
- 把避免冲突理解成“先停掉 child 再由主 agent 自己实现”，而不是尊重 ownership 边界
- 把第二观察窗口结束自动等价成“现在可以直接接管”，而不是先进入接管评估
- 为了清一个错误批次，顺手删掉全部 `workspace`

## References

- `references/planning-constraints.md`: issue topology 示例、写入范围检查清单、dependency 建模样例
- `references/pitfalls.md`: 通用协议失败模式
- `references/desktop-delivery-pitfalls.md`: 仅适用于桌面 / Tauri / GitHub Release 类项目的交付问题
