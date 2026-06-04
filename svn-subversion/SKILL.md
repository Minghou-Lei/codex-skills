---
name: svn-subversion
description: >-
  SVN (Subversion) and mixed Git/SVN workflow for AI-assisted development,
  especially on Windows working copies with Chinese paths. Use when a repo uses
  SVN (or both SVN and Git) and you need status, diff, add, revert, update,
  commit, log, conflicts, branching, externals, properties, or game-asset
  locking — and when SVN automation must not mis-parse paths, corrupt Chinese
  encodings, or commit the wrong file set. In pure SVN projects, use SVN
  commands instead of Git. All commands verified against SVN 1.14.3.
license: Proprietary
compatibility: >-
  SVN (Subversion) 1.14.x CLI. Bash/Git Bash and Windows PowerShell examples
  included; Windows-only behaviours (codepage, case-insensitive FS) are labelled.
metadata:
  verified-against: "svn 1.14.3"
  audience: "rendering/engine engineers, game-studio release automation"
---

# SVN (Subversion) Workflow

A working reference for driving SVN by hand and from agents/scripts. Every
command and flag here was executed against `svn, version 1.14.3`; verified
behaviours (error codes, recursion defaults, column positions) are marked
**(verified)**.

The body below is the high-frequency core. Detailed procedures live in
[references/](#references) and are loaded on demand.

## What good looks like (automation)

A correct SVN automation run, in one breath: **read state from XML, resolve
paths through a UTF-8 targets file, commit a reviewed whitelist with a UTF-8
message file, and never act on human-readable text output.** If a run satisfies
those four, the common failure classes (mis-parsed Chinese paths, garbled
messages, wrong commit scope, missed/ignored files) cannot occur.

## Eight rules that prevent real incidents

1. **Parse machine output, not human text.** `svn status --xml`,
   `svn log --xml`, and `svn info --show-item` always emit UTF-8 with stable
   structure, sidestepping console-codepage corruption (verified). Never parse
   pretty-printed `svn status` / `svn info` / `svn log` in a script.
2. **Make all four encodings consistent before touching SVN.** Console encoding,
   pipe encoding (`$OutputEncoding`), path encoding, and file-content encoding
   are independent; fixing one does not fix the others. On Windows, set UTF-8
   first (see [references/encoding-and-daily-ops.md](references/encoding-and-daily-ops.md)).
3. **Diff is not pipe-safe.** `svn diff` headers contain literal tabs
   (`--- file\t(revision N)`, verified). Write to a file, then read it.
4. **Drive batch work from files, not command strings.** A UTF-8-no-BOM
   `--targets` file for paths and `-F message.txt --encoding UTF-8` for the
   message survive shell quoting and Chinese characters.
5. **Garbled ≠ broken.** `????` in human output usually means the terminal
   decoded wrong, not that the working copy is damaged. Never
   `rename`/`delete`/`revert` on that basis — confirm with `svn info <path>`.
6. **Commit scope = the paths you name × all their local modifications.** There
   is no Git staging index. Generate and review a `--targets` whitelist before
   every commit; a directory-level commit sweeps in everything beneath it.
7. **Always pass `--non-interactive` in automation** so SVN cannot hang on auth,
   certificate, or conflict prompts.
8. **The model differs from Git:** mixed-revision working copies, properties are
   committable changes, `!` means *missing* (not *deleted*), and URL operations
   commit to the server immediately. See [SVN vs Git semantics](#svn-vs-git-semantics).

## SVN ↔ Git command map

All SVN commands and aliases below exist in SVN 1.14.3 (verified). Some mappings
are approximate — the two tools' models differ.

| Git | SVN (alias) | Notes |
|-----|-------------|-------|
| `git status` | `svn status` (`st`, `stat`) | Multi-column output; see [status columns](#svn-status-columns). Add `--no-ignore` for scripts |
| `git diff` | `svn diff` | Headers contain literal tabs; **`svn diff` is recursive by default and rejects `-R`** (verified). Write to a file |
| `git add <file>` | `svn add <file>` | New files must be added explicitly |
| `git commit -m "msg"` | `svn commit` (`ci`) `-m "msg"` | Commits **directly to the server** — no local commit stage |
| `git pull` | `svn update` (`up`) | Brings server changes into the WC |
| `git log` | `svn log` | `svn log -l 20`; use `--xml` for scripts |
| `git blame` | `svn blame` (`praise`, `annotate`, `ann`) | Line-by-line attribution |
| `git restore <file>` / `git checkout -- <file>` | `svn revert <file>` | Discards **uncommitted** local changes. This — *not* `git revert` — is the true equivalent |
| `git revert <commit>` | `svn up && svn merge -c -<rev> .` | Undo an **already-committed** revision by reverse-merging, then commit. `svn up` first is required — merging into a mixed-revision WC fails with `E195020` (verified) |
| `git stash` | `svn diff` → file + `svn revert` | See [references/properties-and-assets.md](references/properties-and-assets.md#stash-workaround-svn-has-no-native-stash); has caveats |
| `git add -p` (staging) | `svn changelist` (`cl`) | No true index; see [references/encoding-and-daily-ops.md](references/encoding-and-daily-ops.md#changelist-svns-staging-area) |
| `.gitignore` | `svn:ignore` property | A versioned **property**, not a file |

> `git revert <file>` was a common mis-mapping: `git revert` acts on a *commit*
> and creates a new inverse commit, whereas `svn revert` throws away uncommitted
> edits. They are not equivalent.

## svn status columns

`svn status` prints **seven status columns** before the path. Most readers only
look at column 1, but several traps live in the others. Each value below was
reproduced (verified).

| Col | Meaning | Common values |
|-----|---------|---------------|
| 1 | Content status | `M` modified, `A` added, `D` deleted, `R` replaced, `C` conflict, `?` unversioned, `!` **missing** (versioned file gone from disk — *not* scheduled delete), `~` type changed, `I` ignored, `X` external |
| 2 | **Property** status | `M` = only a versioned property changed (e.g. `svn:eol-style`), `C` = property conflict |
| 3 | Working-copy lock | `L` = WC locked (run `svn cleanup`) |
| 4 | History scheduled with commit | `+` = item added **with history** (e.g. result of `svn move`) |
| 5 | Switched relative to parent | `S` |
| 6 | Repository lock | `K`/`O`/`T`/`B` (shown with `-u`) |
| 9 | Out-of-date (`-u` only) | `*` = a newer revision exists on the server |

So ` M file` (leading space, `M` in column 2) is a **property-only** change, and
`A  +  file` is an add-with-history. Do not treat every `M` as a content edit.

**Path extraction:** the path begins at **column 9**. `svn status` is
column-positional, **not** space-delimited, so a path with spaces breaks
`awk '{print $2}'` (verified: `my dir` → `my`). Use column slicing:

```bash
svn status | grep '^?' | cut -c9-          # bash — preserves spaces (verified)
```
```powershell
svn status | Where-Object { $_ -match '^\?' } | ForEach-Object { $_.Substring(8).Trim() }
```
For scripts, prefer `svn status --xml --no-ignore` over any text slicing.

## SVN vs Git semantics

The traps that come from SVN's model, not from encoding. All reproduced against
1.14.3.

- **No staging index.** `svn commit <dir>` sends every local modification under
  `<dir>`. Use an explicit targets file or a changelist for selective commits.
- **`?` vs `!` vs `D`** (verified by triggering each): `?` unversioned (not yet
  added); `!` versioned but missing from disk; `D` scheduled for deletion. `!`
  does **not** become a deletion on commit — use `svn delete`, or `svn revert`
  to restore the file from pristine.
- **Unversioned directories do not expand in status** (verified). An unversioned
  dir shows one line — `? Binaries` — and SVN will not descend, even with
  `--depth infinity`, because the dir itself is unversioned. A script that trusts
  status to enumerate files will miss every child. After `svn add --force
  --depth infinity -- <dir>`, **re-audit** with `svn status --xml` and revert
  anything outside the whitelist.
- **`svn add --force` over-adds.** It recursively schedules everything it finds
  (`Saved/`, `Intermediate/`, logs, generated assets). Always re-audit after.
- **Mixed-revision working copies.** A WC can hold files at different revisions
  (`svnversion` shows e.g. `13044:13076M`) even with no conflicts. For a
  reproducible release, `svn export URL@REV` rather than copying the local tree.
- **Properties are committable changes.** `svn:eol-style`, `svn:mime-type`,
  `svn:ignore`, `svn:executable`, `svn:needs-lock` all version as properties; a
  column-2 `M` means a property-only change. Inspect with
  `svn diff --properties-only <path>` (**`svn diff` is recursive by default; do
  not pass `-R`**, verified).
- **`svn:mergeinfo` pollution.** Merging from a subdirectory (or some clients)
  can stamp `svn:mergeinfo` onto many directories — large, unrelated-looking
  property changes. If you did not deliberately merge, treat a burst of
  `svn:mergeinfo` edits as suspect and revert them.
- **Tree conflicts** are worse than text conflicts: a directory deleted, moved,
  or replaced on the server while you changed it locally does not resolve by
  editing markers. Use `svn info <path>` for the tree-conflict description, then
  `svn resolve --accept working <path>` once understood.
- **URL ops commit immediately; WC ops only schedule** (verified via
  `svn help delete`): a **PATH** is *scheduled* (you still `svn commit`); a
  **URL** is deleted/copied/moved on the server right away. Keep the two out of
  the same prepare-then-commit block, or you get "the delete already shipped but
  the main commit hasn't".
- **`svn cleanup` is routine.** After an interrupted operation a WC is often
  write-locked (`L`); `svn cleanup --non-interactive` releases it.
- **`svn:ignore` is not `.gitignore`** and is **not recursive** — it applies to
  the immediate children of the dir it is set on. Use `svn:global-ignores` (a
  recursive inherited property, verified) for tree-wide rules. In a Git+SVN
  checkout the two ignore systems are independent; check each.

## Windows + Chinese: the highest-risk area

On Chinese Windows, almost every "SVN broke" turns out to be a **client-side
encoding mismatch**, not repository damage. Full detail and PowerShell snippets:
[references/encoding-and-daily-ops.md](references/encoding-and-daily-ops.md). The
essentials:

- **Set UTF-8 first** — `chcp 65001`; in PowerShell also set
  `[Console]::OutputEncoding` **and** `$OutputEncoding` (Windows PowerShell 5.1
  corrupts native-exe pipes otherwise).
- **`chcp 65001` does not always save you.** Some Windows clients still decode
  `argv` through the system codepage, so `svn add "中文.json"` can fail with
  `W155010 not found` / `E200009 Illegal target` although the file exists. Add
  the nearest versioned parent with `svn add --force --depth infinity -- <dir>`,
  or use a targets file.
- **Write targets/message files as UTF-8 without BOM via .NET** (PowerShell
  `Out-File`/`Set-Content` defaults vary and can add a BOM):
  ```powershell
  [IO.File]::WriteAllLines($targets, $paths, [System.Text.UTF8Encoding]::new($false))
  [IO.File]::WriteAllText($msg, $message, [System.Text.UTF8Encoding]::new($false))
  svn commit --targets $targets -F $msg --encoding UTF-8 --non-interactive
  ```
- **Deleting a *missing* Chinese path:** if the local-path `svn delete` fails on
  a decoded-wrong argument, deleting by **per-segment-encoded URL** is the
  last-resort fallback — but it is an immediate server commit, not a local
  schedule. Document it; do not use it casually.
- **URL-encode per path segment, never double-encode** (`金水镇` →
  `%E9%87%91%E6%B0%B4%E9%95%87`); leave scheme/host/separators alone.
- **File-content encoding ≠ path encoding.** A Chinese path can commit fine while
  the file's bytes are GBK/UTF-8/UTF-8-BOM. Do not rewrite old files with
  `Set-Content`/`Out-File` casually — the default encoding can silently flip the
  whole file.
- **`--no-ignore` changes results** (verified): plain `svn status` hides ignored
  items, so a script can wrongly conclude "no changes" when ignored Chinese files
  exist. Always add `--no-ignore` in scripts.

## Case-only renames on Windows

On a case-insensitive Windows filesystem, `Foo.md → foo.md` can register as "no
change" or a broken state. Do it in two commits via a temporary name:

```bash
svn move Foo.md Foo_tmp.md && svn commit -m "rename step 1" --encoding UTF-8
svn move Foo_tmp.md foo.md  && svn commit -m "rename step 2" --encoding UTF-8
```

(On a case-sensitive FS the single `svn move Foo.md foo.md` works — verified on
Linux — so this is specifically a Windows hazard.)

## Release-flow hard rules (game-studio automation)

The most dangerous combination is **Chinese path + human-text status parsing +
directory-level add/delete + no commit whitelist** — it causes missed files,
wrong deletes, and committed garbage simultaneously. Enforce as code, not
runtime judgement:

| # | Rule | Why |
|---|------|-----|
| 1 | State via `svn status --xml --no-ignore`, never human text | Codepage corruption; ignored items hidden |
| 2 | Paths via UTF-8-no-BOM `--targets` written with `[IO.File]::WriteAllLines` | Command-line and `Out-File` both corrupt Chinese paths |
| 3 | Messages via `-F message.txt --encoding UTF-8`, never inline `-m "中文"` | Multi-layer shell/exe escaping mangles the message |
| 4 | Explicit commit whitelist; re-audit after any `--force` add | No staging index; `--force` over-adds; unversioned dirs don't expand |
| 5 | Pin generated dirs in `svn:ignore` (`Binaries/ Intermediate/ Saved/ DerivedDataCache/ *.pdb *.pid *.log`) | Stops the recurring "build output in repo" incident |
| 6 | URL delete only as a documented fallback for already-missing Chinese paths | URL ops commit immediately, bypassing the prepare/commit gate |
| 7 | `svn cleanup --non-interactive` before each run; `--non-interactive` on every command | Stale WC locks and prompts hang automation |
| 8 | Reproducible release = `svn export URL@REV`, not a copy of the local tree | Working copies are mixed-revision and untraceable |

The recurring plugin-`Binaries` incident was fundamentally "**status granularity
+ generated-dir filtering + commit whitelist** were never pinned down in code."
Keep all three mechanical and verifiable.

## References

Load these on demand; each is focused on one area.

- **[references/encoding-and-daily-ops.md](references/encoding-and-daily-ops.md)**
  — UTF-8 setup, the Windows/Chinese trap catalogue (with PowerShell), daily
  workflow (status/update/add/delete/revert/commit), machine-readable output,
  diff safety, cleanup & recovery, changelists, automation flags, conflict
  resolution.
- **[references/branching-and-history.md](references/branching-and-history.md)**
  — branching, tagging, switch, merge and reverse-merge, mergeinfo, viewing
  history, externals.
- **[references/properties-and-assets.md](references/properties-and-assets.md)**
  — `svn:ignore`/`svn:global-ignores`, EOL and file properties, binary MIME
  types, asset locking, the stash workaround and its caveats.
- **[references/game-engine-shortcuts.md](references/game-engine-shortcuts.md)**
  — copy-paste bash and PowerShell snippets for engine repos (filter modified
  C++/shaders, shader changelist commit, subsystem revert).
