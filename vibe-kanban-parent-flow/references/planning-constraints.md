# Planning Constraints

Use this reference when the main question is not “how to execute a task” but “how to split a parent todo into safe child subtasks”.

## Goal

Child subtasks should be parallel only when they are merge-safe.

Parent todos should remain serial because each parent usually establishes a new baseline for the next stage.

## How To Classify Child Subtasks

For every child subtask, decide:

- what files it will write
- what modules it will change
- what outputs it produces
- what prior work it depends on
- whether another sibling needs the same files or same state shape

Then classify the child as:

- **parallel-safe**
  Distinct write scope and no unpublished dependency on a sibling.
- **sequential**
  Needs sibling output first, or touches shared core files.
- **merge-into-sibling**
  Not truly independent enough to deserve its own workspace.

## Good Parallel Splits

- documentation vs implementation
- backend scanner vs frontend pages
- data model vs docs/specs
- independent view/page files
- separate schemas or config domains

## Bad Parallel Splits

- two tasks both editing the same central state file
- two tasks both editing the same routing table
- two tasks both editing the same shell entrypoint
- two tasks both editing the same README section
- two tasks where one child is really the prerequisite of the other

## Write-Scope Checklist

Do not launch sibling workspaces together until you can answer:

- Which files belong to child A?
- Which files belong to child B?
- Which files are shared and therefore unsafe for parallel work?
- If conflicts occur, is that because the split was wrong?

If the shared file list is large or central, the split is wrong.

## Parent Todo Ordering

Treat parent todos as release-style milestones:

1. complete parent A
2. integrate and validate parent A
3. merge parent A to `main`
4. only then start parent B

Do not let parent B branch from a `main` that does not already include parent A.

## Workspace Creation Rule

Always create child workspaces from the child issue itself, not from a bulk project-level entrypoint, unless the user explicitly says otherwise.

This preserves:

- issue linkage
- workspace traceability
- branch attribution
- easier cleanup later

## Cleanup Rule

When a batch was launched incorrectly:

- delete only the incorrect batch
- keep previously finished parent batches intact
- keep `main` as the source of truth

When a parent batch is done:

- merge to `main`
- delete child workspaces
- delete `vk/*` branches
- leave the next parent to start from a clean baseline
