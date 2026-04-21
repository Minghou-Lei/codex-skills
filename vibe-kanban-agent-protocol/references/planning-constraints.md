# Issue Topology Constraints

当核心问题不是“能不能执行”，而是“当前 issue 集应该怎么组织”，使用这份参考文档。

主 skill 负责协议边界；这里专门提供 topology 示例、检查清单和 dependency 建模样例。

## 先看什么

对每个候选 issue，先看五件事：

- 它会写哪些文件
- 它会改哪些模块
- 它会产出什么结果
- 它依赖哪些前序工作
- 它是否和同级 issue 共享核心文件或状态形状

如果这些问题答不清，就还不应该进入执行。

## 良好的 peer split 示例

- backend API 与 frontend UI，各自写不同目录并通过稳定接口衔接
- docs/specs 与 implementation，且文档不与实现共改同一核心入口
- 两个彼此独立的 page / view / component
- 独立的 schema 域与无共享核心状态的配置域

这些案例通常更接近 `parallel-safe`。

## 糟糕的 peer split 示例

- 两个 issues 都在编辑同一个核心状态文件
- 两个 issues 都在编辑同一个路由表或 shell 入口
- 两个 issues 都需要改同一段 README 或同一份规范文档
- 其中一个 issue 其实是另一个 issue 的隐藏前置条件

这些案例通常更接近 `sequential-in-batch` 或 `merge-into-peer`。

## 写入范围检查清单

在同时启动同级 `workspace` 之前，必须先回答清楚：

- 哪些文件属于 issue A
- 哪些文件属于 issue B
- 哪些文件是共享的，因此不适合并行
- 哪些输出物可以分别审查
- 哪些约束来自 blocker，哪些约束只是共享核心文件
- 如果最终发生冲突，是执行偶发问题，还是 topology 本身就是错的

如果共享文件列表很大，或者这些文件都是核心文件，这次拆分通常就是错的。

如果一个 issue 必须等待另一个 issue 的明确产出才能开始，就不要只把这件事写在 description 里；应显式创建 `blocking` relationship。

## 分类样例

### 样例 1: `parallel-safe`

一个 issue 做后端搜索接口，另一个 issue 做前端搜索结果页：

- 文件集分离
- 输出物分离
- 通过稳定 API 契约衔接

这类拆分通常适合 `parallel-safe`。

### 样例 2: `sequential-in-batch`

两个 issues 都要改同一个状态管理入口，但目标仍属于同一个批次：

- 写入范围冲突
- 审查边界不独立

这类拆分通常更适合 `sequential-in-batch`。

这里不要伪造 `blocking` relationship，因为真正的问题是共享核心文件，而不是“先完成 A，才能开始 B”的独立前置产物。

### 样例 3: `merge-into-peer`

一个候选 issue 只是在另一个 issue 内部补一段很小的配套改动：

- 没有自己的独立输出物
- 没有必要拥有单独的 `workspace`

这类拆分通常更适合 `merge-into-peer`。

### 样例 4: `promote-to-new-batch`

执行中才发现后续多个 issues 都依赖一个尚不存在的新基线，例如公共 schema、核心脚手架或新的集成层：

- 当前工作已经不只是“继续做当前 issue”
- 后续多个 issues 都会依赖这个前置结果

这类情况通常应该先提升为新的 batch，再继续后续拆分。

## 依赖建模样例

### 样例 5: 必须建 `blocking`

issue A 先建立目录骨架，issue B 再补 README 和索引：

- B 需要等待 A 的稳定目录基线
- 这是明确的前置产出依赖，不只是共享文件

这类情况应保留两个独立 issues，并显式创建 `blocking` relationship。

### 样例 6: 只保留 `sequential-in-batch`

两个 issues 都要修改同一份核心入口文档，但谁先谁后并不依赖新的独立产出：

- 它们不适合并行
- 但这不是一个“先完成 A 的产物，后做 B”的 blocker

这类情况只保留 `sequential-in-batch`，不要为了凑关系而创建 `blocking`。

## Optional Hierarchy Note

`parent_issue_id` / `sub_issues` 可以用于组织 issue hierarchy，但这只是可选拓扑，不是 protocol 的唯一形态。

如果 flat issue set + `Relationships` 已经足够表达结构，就不要为了形式感强行套 hierarchy。
