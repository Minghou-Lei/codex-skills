---
name: vibe-kanban-parent-flow
description: Use when a software project is executed through Vibe Kanban with parent todos, child subtasks, issue-linked workspaces, staged integration branches, merges back to main, and release publishing. Trigger when Codex must plan or run parent tasks serially, fan out child subtasks in parallel without merge conflicts, preserve issue/workspace links, clean up temporary vk branches, or manage packaged desktop releases.
---

# Vibe Kanban Parent Flow

Use this skill when the user wants Vibe Kanban to drive delivery and expects strict control over:

- parent todo sequencing
- subtask parallelism
- issue-linked workspace creation
- merge-safe branch planning
- cleanup of mistaken or completed batches
- release and GitHub publishing discipline

Only apply the rules below when they match the current project flow. Do not generalize beyond them.

For detailed task decomposition constraints, read [references/planning-constraints.md](references/planning-constraints.md).

For concrete failure patterns and fixes, read [references/pitfalls.md](references/pitfalls.md).

## Core Model

- A **parent todo** is an ordered integration milestone.
- A **child subtask** is an execution unit that may run in parallel with sibling subtasks only if its write scope is isolated.
- A **workspace** is an issue-linked execution container and a temporary `vk/*` branch.
- `main` is the only accepted integration baseline between parent todos.

## Hard Rules

### Parent / Child Sequencing

- `[Hard]` Run parent todos serially.
- `[Hard]` Do not start the next parent todo until the current parent batch is integrated and merged to `main`.
- `[Hard]` Child subtasks under the same parent may run in parallel only if they can be kept merge-safe.
- `[Hard]` Do not start child subtasks from multiple parent todos at the same time.

### Workspace Creation

- `[Hard]` Create each workspace from the child issue itself, using the issue-level `Workspace -> Create` path or equivalent API semantics.
- `[Hard]` Preserve direct issue -> workspace linkage for every started child.
- `[Hard]` If the user points to a specific issue detail page as the source of truth, follow that issue-first creation path instead of bulk project-level creation.

### Merge-Safe Parallelism

- `[Hard]` Do not parallelize subtasks that write the same files or the same tightly coupled module.
- `[Hard]` Before starting sibling subtasks, define ownership by file set, module, or layer.
- `[Hard]` Prefer parallel subtasks that split by one of:
  - backend vs frontend
  - scanner vs UI
  - docs/specs vs implementation
  - independent pages/components
  - separate storage or schema areas
- `[Hard]` If two subtasks both need the same core files, either:
  - fold them into one subtask, or
  - run them sequentially inside the same parent batch

### Integration Discipline

- `[Hard]` Treat each `vk/*` branch as disposable.
- `[Hard]` Integrate child outputs into a parent integration branch first.
- `[Hard]` Merge the completed parent integration branch into `main` before launching the next parent.
- `[Hard]` Never treat a temporary child workspace branch as a long-lived collaboration branch.

### Cleanup

- `[Hard]` When a batch was started the wrong way, delete only that batch's workspaces and matching `vk/*` branches.
- `[Hard]` When the user asks to clean current execution state, stop/delete the relevant workspaces first, then remove the matching `vk/*` branches.
- `[Hard]` When the user asks for the cleanest possible Git state, use full cleanup semantics: `git reset --hard HEAD`, `git clean -fdx`, and prune stale worktrees.

### Release / GitHub

- `[Hard]` For desktop releases, publish built binaries as GitHub Release assets; do not treat GitHub's automatic source archives as the release deliverable.
- `[Hard]` Keep release links, README download links, and repository metadata aligned with the actual shipped assets.
- `[Hard]` README must carry a prominent warning when the project is an experimental vibe-coding / multi-subagent workflow test and may contain bugs or system risk.

## Planning Protocol

When planning a new parent todo:

1. Confirm the current branch state is clean enough to branch from `main`.
2. Read the parent todo and all of its child subtasks.
3. Classify each child as one of:
   - parallel-safe
   - sequential within parent
   - merge into sibling / not independent enough
4. Assign each child a clear write scope.
5. Start only the children that are parallel-safe.
6. Hold the rest until dependency or ownership conflicts are removed.

## Parallel-Safe Child Criteria

Only run child subtasks in parallel if all are true:

- each child has a distinct write scope
- each child can be reviewed independently
- the merge path back into the parent integration branch is obvious
- no child depends on unpublished results from a sibling
- the combined fan-out is small enough to avoid API or model throttling

If any of those fail, do not parallelize.

## Suggested Practices

- `[Suggested]` Start with one parent todo, fan out its safe subtasks, then converge before moving on.
- `[Suggested]` Stagger workspace creation enough to avoid `429 Too Many Requests`.
- `[Suggested]` Keep the repository on `main` between parent batches so new workspaces inherit the latest accepted state.
- `[Suggested]` Delete temporary workspace branches immediately after their parent batch is absorbed.
- `[Suggested]` Prefer installer artifacts for end users, with raw `.exe` as a secondary option.
- `[Suggested]` Include token/cost transparency in README only when the user explicitly wants that information public.

## Execution Checklist

1. Pick exactly one parent todo.
2. Read all child subtasks under that parent.
3. Split children into parallel-safe vs sequential.
4. Start child workspaces only from their own issue detail records.
5. Preserve issue links per subtask.
6. Let the parent batch finish.
7. Integrate child branches into the parent branch.
8. Merge the parent branch into `main`.
9. Delete parent batch workspaces and `vk/*` branches.
10. Start the next parent from updated `main`.
