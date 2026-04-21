# 常见协议失败模式

## 1. 单个 issue 中的复杂度蔓延

症状：某个 issue 越做越大，不断吸附新依赖，看起来更像一组工作，而不是一个可审查单元。

原因：topology 已经失效，但执行没有停下来重塑结构。

正确做法：

- 只要当前 issue 不再是一个可独立审查的单元，就立刻停止它。
- 判断应该走 `split-into-peer-issues` 还是 `promote-to-new-batch`。
- 重建 issue topology、重新定义写入范围、依赖关系和 ownership，然后再恢复执行。

## 2. 过度并行

症状：系统出现 `429 Too Many Requests`、模型节流、频繁重试，或多个并行 issues 互相等待。

原因：一次启动了过多 issues，或者在当前 unresolved batch 尚未吸收前，又继续扇出下一批工作。

正确做法：

- 控制同批次内的并行规模。
- 只并行已确认 `parallel-safe` 的 issues。
- 错峰创建 `workspace`，并控制扇出规模。

## 3. 依赖只写在 description 里，没有落到 `Relationships`

症状：issue 描述里明明写了“依赖某 issue”“等待某任务先完成”，但 `Relationships` 面板仍然是空的。

原因：把真实执行依赖当成了说明文字，而没有显式建模为 `blocking` relationship。

正确做法：

- 先区分 issue hierarchy 和横向依赖：`parent_issue_id` 只是可选 hierarchy，`Relationships` 才负责横向关系。
- 只要一个 issue 必须等待另一个 issue 完成，就创建 `blocking` relationship。
- 如果只是共享核心文件导致不能并行，而不存在明确前置产物，就保持 `sequential-in-batch`，不要伪造 blocker。

## 4. 错误的 `workspace` 创建入口

症状：`workspace` 已经存在，但 issue 到 `workspace` 的关系缺失或不清晰。

原因：`workspace` 不是从对应 issue 本身创建出来的。

正确做法：

- 从 issue 详情记录创建 `workspace`。
- 为每个执行 issue 保留 issue -> `workspace` -> branch 关联。

## 5. 过早启动下一批未吸收工作

症状：新的 issues 已经开始执行，但上一批工作的结果还没有被稳定吸收进 `main`。

原因：integrator 还没完成当前批次的吸收，就继续放大未收敛的工作面。

正确做法：

- 先吸收并验证已经完成的当前批次。
- 再把它合并到 `main`。
- 下一批工作应从更新后的 `main` 和清晰的 topology 上启动。

## 6. 临时分支蔓延

症状：`vk/*` 分支和 `workspace` 越积越多，最后无法分辨哪些还相关。

原因：把临时执行分支当成了长期协作分支，没有在批次吸收完成后及时回收。

正确做法：

- 把 `vk/*` 当成一次性分支。
- 批次吸收完成后，立刻删除对应的 `workspace` 和临时分支。

## 7. 过度清理

症状：为了清理一个错误批次，却顺带破坏了之前某个成功批次的有用上下文，或丢掉了无关本地工作。

原因：删除了所有 `workspace`，或者直接进入 `git reset --hard HEAD` / `git clean -fdx`，而不是只清当前出错的那个批次。

正确做法：

- 只停止并删除受影响的那个批次。
- 除非用户明确要求完整重置并接受风险，否则不要进入 destructive cleanup。
- 在执行硬清理前，先确认目标就是当前批次对应的工作区，而不是无关上下文。
