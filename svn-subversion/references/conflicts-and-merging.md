# Conflicts & Merging

Reference for [../SKILL.md](../SKILL.md). Branching, merging, and conflict
resolution kept together as one topic. All commands verified against SVN 1.14.3.

## Branching and tagging

Standard layout: `trunk/` | `branches/` | `tags/`. Branches and tags are
server-side copies (instant, no data transfer). All URL→URL copies verified.

```bash
# Create branch
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/branches/feature-name \
         -m "Branch: feature-name" --encoding UTF-8

# Switch working copy to branch / check current branch
svn switch https://svn.example.com/repo/branches/feature-name
svn info --show-item url

# Create tag (same mechanism; by convention don't commit to tags/)
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/tags/v2.1.0 \
         -m "Tag: v2.1.0" --encoding UTF-8

# Create a directory directly in the repo (immediate server commit)
svn mkdir -m "layout" https://svn.example.com/repo/trunk/newsub
```

## Merging

```bash
# Merge branch → trunk (record-based, SVN 1.5+). svn up first to flatten the WC.
svn switch https://svn.example.com/repo/trunk
svn up
svn merge https://svn.example.com/repo/branches/feature-name
svn status                              # review
svn diff --internal-diff > /tmp/merge_review.patch && cat /tmp/merge_review.patch
svn commit -m "Merge: feature-name into trunk" --encoding UTF-8

# Merge history
svn mergeinfo https://svn.example.com/repo/branches/feature-name
svn mergeinfo --show-revs eligible https://svn.example.com/repo/branches/feature-name
```

### Reverse-merge = the `git revert <commit>` equivalent

To undo an already-committed revision, reverse-merge it, then commit. **`svn up`
first is mandatory** — merging into a mixed-revision working copy fails (verified:
`E195020: Cannot merge into mixed-revision working copy [N:M]; try updating
first`).

```bash
svn up
svn merge -c -<rev> .                   # reverse-merge revision <rev>
svn status                              # review
svn commit -m "Revert r<rev>" --encoding UTF-8
```

> A reverse merge also records `svn:mergeinfo` on the target (verified). If you
> later see unexplained `svn:mergeinfo` property churn, this — or a subdirectory
> merge — is a likely source.

## Conflict resolution

```bash
svn status | grep '^C'                 # list conflicted files

# Valid --accept values (verified): base | working | mine-conflict |
#   theirs-conflict | mine-full | theirs-full   (postpone is for `update`, not `resolve`)
svn resolve --accept mine-full <file>      # keep local entirely (DISCARDS remote)
svn resolve --accept theirs-full <file>    # take server entirely (DISCARDS local)
svn resolve --accept working <file>        # manual edit done, mark resolved

# Manual merge: edit out <<<< ==== >>>> markers, then:
svn resolve --accept working <file>
svn status | grep '^C'                     # must be empty before committing
```

> **A conflicting update can still exit 0** (verified). `svn update --accept
> postpone` returns exit 0 even when it produces a text conflict — status shows
> `C` and `--xml` shows `item="conflicted"`, but the exit code is 0. Never use
> the exit code to detect conflicts; always re-check status after an update:
> ```bash
> svn update --accept postpone --non-interactive <path>
> svn status --xml <path> | grep -q 'item="conflicted"' && echo "CONFLICT — resolve before commit"
> ```

> **`mine-full` / `theirs-full` are not three-way merges** (verified). They
> accept one side's full text and discard the other entirely — a `mine-full` test
> dropped a unique remote line with no warning. SVN's help: these are "only
> useful … where it is acceptable to discard local or incoming changes
> altogether." On conflict, SVN writes sidecar files (verified):
> `<file>.mine`, `<file>.rOLD`, `<file>.rNEW` (e.g. `a.txt.mine`, `a.txt.r3`,
> `a.txt.r4`). Inspect those or the conflict blocks before choosing a side; use
> `working` after a manual merge when you must keep content from both.

> `svn resolved <file>` (no `--accept`) is **deprecated** in favour of
> `svn resolve --accept working <file>`, and it only clears the conflicted state
> — it does not remove conflict markers from the file.

## Tree conflicts (worse than text conflicts)

A directory deleted, moved, or replaced on the server while you changed it
locally produces a **tree conflict**, which does not resolve by editing markers.

```bash
svn status                  # look for 'C' on directories / "tree conflict" notes
svn info <path>             # shows the tree-conflict description
svn resolve --accept working <path>   # only after you understand the change
```
