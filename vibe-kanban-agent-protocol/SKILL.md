---
name: vibe-kanban-agent-protocol
description: Use when multiple Vibe Kanban agents need a shared protocol for issue topology, `Relationships` such as `Blocks`, `Blocked by`, `Related to`, and `Duplicate of`, issue-linked `workspace` usage, staged integration to `main`, and safe cleanup across planner, executor, reviewer, integrator, and cleanup roles.
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

在以下场景不要使用：

- 工作本身只是单分支、小范围修改，不需要 issue topology 或多 agent 协作
- 当前项目没有 issue-linked `workspace` 或 `vk/*` 分支语义
- 用户只是在问某个项目特有的桌面交付、Tauri、Rust、README 发布细节

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
| planner | 定义 issue topology、relationships、ownership、批次边界 | 不在 planning 名义下直接开始实现 |
| executor | 只执行已分配 issue，尊重 blocker，保持 issue-linked `workspace` | 不越权改 topology，不跳过 blocker |
| reviewer | 检查 scope、relationship、workspace linkage、可合并性 | 不把 review 退化成只看代码 diff |
| integrator | 吸收批次产出、推进集成分支、回并 `main` | 不在 unresolved batch 上继续堆叠新批次 |
| cleanup | 只清当前错误批次，保留已吸收上下文 | 未经明确授权做 destructive reset |

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
- `vk/*` 分支是一次性分支，不是长期协作分支
- 当前批次的产出应先进入集成分支，再吸收回 `main`
- 在当前批次完成吸收之前，不要启动下一批 unresolved work
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
- executor 越权修改 topology 或绕过 blocker
- 从项目级入口批量创建 `workspace`，导致 issue 关联丢失
- 为了清一个错误批次，顺手删掉全部 `workspace`

## References

- `references/planning-constraints.md`: issue topology 示例、写入范围检查清单、dependency 建模样例
- `references/pitfalls.md`: 通用协议失败模式
- `references/desktop-delivery-pitfalls.md`: 仅适用于桌面 / Tauri / GitHub Release 类项目的交付问题
