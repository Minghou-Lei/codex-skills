---
name: svn-workflow
description: >
  SVN (Subversion) and mixed Git/SVN version-control workflow.
  Use this skill whenever:
  - The user mentions Git, SVN, version control, commit, submit, add, staging, status, diff, revert, branch, tag, update, or log
  - The user says "版本控制", "提交", "本地库", "add", "Git", "SVN", "git", "svn", "TortoiseSVN", or "VisualSVN"
  - The conversation is about JX3QJ project work (JX3QJ, 剑网三, SO3Client, KG3DEngine, KGUI, GameDesignerEditor, sword3-products, Base, DevEnv)
  - The project uses SVN (svn:// or https:// SVN URLs, presence of .svn directories)
  - The user asks to commit, update, diff, revert, branch, tag, or check status using SVN
  - The repository uses both Git and SVN and the user asks to submit to one or both systems
  - You need to replace a Git-based workflow with SVN equivalents
  - The user says "我们用SVN" or mentions TortoiseSVN, VisualSVN, or svn commands
  - You need to handle SVN conflicts, externals, or working copy management
  In pure SVN projects, do NOT use Git commands (git commit, git push, etc.). Always use svn equivalents.
  In mixed Git/SVN projects, inspect both working-copy states and commit each system with its own commands.
---

# SVN Workflow

Complete SVN workflow guide for AI-assisted development on projects without Git.

> **Critical — read first:**
> 1. **Encoding**: SVN on Windows with Chinese paths/messages requires explicit encoding handling. See [Encoding Safety](#encoding-safety).
> 2. **Diff safety**: `svn diff` output contains `\t` that corrupts agent JSON pipelines. Always pipe to a file first. See [SVN Diff Safety](#svn-diff-safety).
> 3. **Agent automation**: Always add `--non-interactive` to prevent SVN from hanging on auth prompts.

---

## SVN ↔ Git Command Map (Quick Reference)

| Git | SVN | Notes |
|-----|-----|-------|
| `git status` | `svn status` | M=modified, A=added, ?=untracked, !=missing |
| `git diff` | `svn diff` | See diff safety section |
| `git add <file>` | `svn add <file>` | Must add new files explicitly |
| `git commit -m "msg"` | `svn commit -m "msg"` | Commits directly to server |
| `git pull` | `svn update` | `svn up` for short |
| `git log` | `svn log` | `svn log -l 20` for last 20 |
| `git blame` | `svn blame` | |
| `git revert <file>` | `svn revert <file>` | Local revert, no commit needed |
| `git stash` | `svn diff` → file + `svn revert` | See stash workaround section |
| `git add -p` (staging) | `svn changelist` | See changelist section |
| `.gitignore` | `svn:ignore` property | See ignore section |

---

## Encoding Safety

> ⚠️ **Critical for JX3/KG3D**: Windows SVN clients default to the system ANSI codepage (GBK/CP936 on Chinese Windows). Mismatch between commit message encoding, file content encoding, and agent pipeline encoding causes garbled output, failed commits, and silent data corruption.

### Windows — set UTF-8 console before any SVN operation (agent/script context)
```batch
chcp 65001
```
```powershell
# PowerShell equivalent
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"   # if driving SVN from Python
```

### Commit messages with Chinese characters
```bash
# Explicitly specify encoding of the -m string
svn commit -m "Fix: 修复延迟渲染阴影偏移" --encoding UTF-8

# If repo/team standard is GBK:
svn commit -m "Fix: 修复延迟渲染阴影偏移" --encoding GBK
```

### Reading SVN log with Chinese content
```bash
# Write to file with known encoding before processing
svn log -l 20 > /tmp/svn_log.txt
# On Windows, set chcp 65001 first so the file is written in UTF-8
```

### Detecting encoding issues
```bash
# If svn log shows garbled output, the terminal/pipe encoding is wrong
# Check current SVN config locale:
svn --version
# Check ~/.subversion/config: [miscellany] section, no encoding override = uses system locale
```

### Agent pipeline rule
When an agent captures SVN output programmatically, **always** specify `encoding='utf-8', errors='replace'` in subprocess calls (Python example):
```python
result = subprocess.run(
    ["svn", "status", "--non-interactive"],
    capture_output=True,
    encoding="utf-8",
    errors="replace"   # never let a bad byte crash the pipeline
)
```

---

## Daily Workflow

### Pre-flight check (run before starting any work session)
```bash
svn info --show-item revision          # quick WC health check; fails if WC is corrupt
svn status -u | tail -3                # check for pending server changes
svn cleanup --non-interactive          # release any stale locks from previous session
```

### Check status
```bash
svn status                             # short: svn st
svn status -u                          # include server-side changes
svn info                               # repo URL, current revision, last author
svn info --show-item last-changed-revision   # just the revision number
svnversion                             # e.g. "1234M" = modified, "1234:1236" = mixed
```

Status codes: `M`=modified `A`=added `D`=deleted `C`=conflict `?`=untracked `!`=missing `X`=external

### Update working copy
```bash
svn update --non-interactive           # short: svn up
svn update -r 1234                     # specific revision
svn update <file>                      # single file
svn update --accept postpone           # auto-postpone conflicts (resolve later)
```

### Commit changes
```bash
# Review before committing (encoding-safe)
svn diff > /tmp/review.patch && cat /tmp/review.patch

svn status
svn commit -m "Fix: description of change" --encoding UTF-8 --non-interactive
svn commit file1.cpp file2.h -m "Refactor: extract helper" --encoding UTF-8
```

Commit message conventions:
- `Fix:` bug fix
- `Feature:` new functionality
- `Refactor:` structural changes
- `Shader:` shader-specific changes
- `Asset:` asset additions/modifications

### Add / Delete files

**Bash / Git Bash:**
```bash
svn add new_file.cpp
svn add new_dir/ --force               # add directory + contents recursively

# Add all untracked files (bash)
svn status | grep "^?" | awk '{print $2}' | xargs -I{} svn add "{}"

svn delete old_file.cpp
svn delete --force old_file.cpp        # force if locally modified
svn move old_name.cpp new_name.cpp     # rename (preserves history)
```

**PowerShell (Windows native):**
```powershell
# Add all untracked files
svn status | Where-Object { $_ -match '^\?' } |
    ForEach-Object { svn add $_.Substring(8).Trim() }

# Delete a file
svn delete old_file.cpp
```

### Windows Unicode path add pitfall

Observed on Windows with TortoiseSVN `svn.exe` 1.15.0-dev:

- `svn status` can show Chinese filenames as `????` while the real files exist on disk.
- `svn add "reports\...\wj_ylc圣女雕像001_001_hd.xxx.json"` can fail with `W155010 ... not found` / `E200009 Illegal target`.
- `chcp 65001`, PowerShell `LiteralPath`, Node `spawnSync`, and full absolute paths may still fail because the SVN client decodes the argument path through the wrong codepage.
- Directory-level recursive add can succeed because SVN enumerates children itself:

```powershell
svn add --force --depth infinity -- reports\import_results
svn commit reports\import_results -m "Feature: 提交验证报告" --encoding UTF-8 --non-interactive
```

Agent rule:

1. If single-file `svn add` fails for a non-ASCII path but the file exists, do not rename the file unless the user approves.
2. Retry at the nearest already-versioned parent directory with `svn add --force --depth infinity -- <dir>`.
3. Re-run `svn status` and commit the parent directory or the scheduled `A` targets.
4. Keep generated caches such as `DerivedDataCache`, `Saved`, `Intermediate`, and missing `!` generated files out of the commit unless the user explicitly asks to version them.

### Revert local changes
```bash
svn revert <file>
svn revert -R .                        # revert everything (DESTRUCTIVE — use with care)
svn revert -R src/Renderer/
```

---

## SVN Diff Safety

> ⚠️ Raw `svn diff` contains `\t` in unified-diff headers — this corrupts agent JSON pipelines.
> Always write to a temp file first, then read the file separately.

```bash
# Safe pattern for agent use
svn diff --internal-diff > /tmp/svn_changes.patch
cat /tmp/svn_changes.patch

# Single file diff (safe to capture directly — header tabs are minimal)
svn diff src/RenderPipeline.cpp

# Revision range diff
svn diff -r 1233:1234 src/

# UNSAFE: svn diff | agent_json_capture  → \t corrupts JSON strings
```

`--internal-diff` forces SVN's built-in diff engine, avoiding unpredictable output from external diff tools configured in `~/.subversion/config`.

---

## Cleanup & Recovery

> When an SVN operation is interrupted (network drop, agent timeout, process kill), the working copy may be left in a locked state. Always run `svn cleanup` first.

```bash
svn cleanup                            # release locks, resume interrupted ops
svn cleanup --vacuum-pristines         # also reclaim disk space (removes cached base files)
svn cleanup --non-interactive

# If cleanup itself fails (rare, WC severely corrupted):
svn cleanup --remove-unversioned --remove-ignored
# Last resort: delete .svn/lock file manually, then retry
```

**Recovery workflow after interrupted operation:**
```bash
svn cleanup
svn status                             # assess damage
svn status | grep "^C"                # check for conflicts introduced
svn update --non-interactive          # re-sync with server
```

---

## Changelist (SVN's Staging Area)

> SVN changelists are the equivalent of Git's index — they let you group modified files and commit selectively without listing every file path manually.

```bash
# Create a changelist and assign files to it
svn changelist my-feature src/Renderer/DeferredPass.cpp src/Renderer/ShadowMap.h
svn changelist my-feature src/Shaders/DeferredLighting.hlsl

# View what's in a changelist
svn status --cl my-feature

# Commit only the changelist (all files in it, no matter where they are in the WC)
svn commit --cl my-feature -m "Feature: deferred shadow refinement" --encoding UTF-8

# Remove files from changelist after commit
svn changelist --remove --recursive --changelist my-feature .

# List all changelists in WC
svn status | grep "^--- Changelist"
```

**Typical agent workflow with changelist:**
```bash
# Agent edits files, then groups them
svn changelist agent-patch File1.cpp File2.h File3.hlsl
# Review
svn diff --cl agent-patch > /tmp/agent_patch_review.patch
# Commit atomically
svn commit --cl agent-patch -m "Fix: agent-applied patch" --encoding UTF-8 --non-interactive
# Cleanup
svn changelist --remove --recursive --changelist agent-patch .
```

---

## Agent / Automation Flags

Always include these flags in non-interactive (script/agent) contexts:

| Flag | Purpose |
|------|---------|
| `--non-interactive` | Prevents hanging on auth/certificate prompts |
| `--no-auth-cache` | Don't read/write credentials cache (CI environments) |
| `--trust-server-cert-failures=unknown-ca,cn-mismatch,expired,other` | Skip cert errors in controlled environments |
| `--encoding UTF-8` | Explicit message encoding on commit/log |

```bash
# Full safe automation commit example
svn commit file.cpp \
  -m "Fix: auto-patched by agent" \
  --encoding UTF-8 \
  --non-interactive \
  --no-auth-cache
```

---

## Conflict Resolution

```bash
# List conflicted files
svn status | grep "^C"

# Resolution options
svn resolve --accept mine-full <file>     # keep local version entirely
svn resolve --accept theirs-full <file>  # take server version entirely
svn resolve --accept working <file>      # manual edit done, mark resolved

# Workflow: manual merge
# 1. Edit the file to remove <<<< ==== >>>> markers
# 2. Mark resolved:
svn resolve --accept working <file>

# Verify no conflicts remain before committing
svn status | grep "^C"                    # must be empty
```

> **Note**: `svn resolved <file>` (no `--accept`) is **deprecated** since SVN 1.10. Use `svn resolve --accept working <file>` instead.

---

## Branching and Tagging

Standard SVN layout: `trunk/` (main) | `branches/` | `tags/`

```bash
# Create branch (instant server-side copy, no data transfer)
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/branches/feature-name \
         -m "Branch: feature-name" --encoding UTF-8

# Switch working copy to branch
svn switch https://svn.example.com/repo/branches/feature-name

# Check current branch
svn info --show-item url

# Create tag (same as branch, convention is don't commit to tags/)
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/tags/v2.1.0 \
         -m "Tag: v2.1.0" --encoding UTF-8

# Merge branch → trunk (record-based merge, SVN 1.5+)
svn switch https://svn.example.com/repo/trunk
svn merge https://svn.example.com/repo/branches/feature-name
svn status                            # review merge result
svn diff > /tmp/merge_review.patch && cat /tmp/merge_review.patch
svn commit -m "Merge: feature-name into trunk" --encoding UTF-8

# Check merge history (what has already been merged)
svn mergeinfo https://svn.example.com/repo/branches/feature-name
svn mergeinfo --show-revs eligible https://svn.example.com/repo/branches/feature-name
```

---

## Viewing History

```bash
svn log -l 20                          # last 20 commits
svn log -r 1230:1240                   # revision range
svn log -v -r 1234                     # verbose: show changed files
svn log <file>                         # file-specific history
svn diff -r 1233:1234 > /tmp/rev_diff.patch  # diff between revisions (safe)
svn blame <file>                       # line-by-line attribution
svn cat -r 1234 src/file.cpp > /tmp/old_version.cpp  # retrieve old version

# Machine-readable log (for agent parsing — avoids encoding issues)
svn log -l 10 --xml > /tmp/svn_log.xml
```

---

## Externals Management

```bash
# View externals defined on a directory
svn propget svn:externals .
svn propget -R svn:externals .         # recursive

# Update externals explicitly
svn update --non-interactive           # updates externals by default
svn update --ignore-externals          # skip externals (faster)

# Add an external definition
svn propedit svn:externals .
# Format in editor: <local-dir> [-r<rev>] <repo-url>
# Example:  ThirdParty/zlib  https://svn.example.com/ext/zlib/trunk

# Commit the property change
svn commit -m "Externals: add zlib" --encoding UTF-8
```

---

## SVN Ignore

```bash
# Set ignore properties (multiline value)
svn propset svn:ignore "*.obj
*.pdb
*.suo
Binaries
Intermediate
.vs
x64" .

svn propedit svn:ignore .             # edit interactively
svn propget svn:ignore .              # view current list

# Commit the property change
svn commit -m "Config: update svn:ignore" --encoding UTF-8

# Recommend adding to ~/.subversion/config [miscellany]:
# global-ignores = *.o *.obj *.pdb *.suo .vs Binaries Intermediate x64
```

---

## SVN EOL and File Properties

```bash
# Set end-of-line style (prevents CRLF/LF corruption in cross-platform teams)
svn propset svn:eol-style native src/Renderer/DeferredPass.cpp
svn propset svn:eol-style native -R src/   # recursive

# Values: native (CRLF on Windows, LF on Unix) | LF | CRLF

# Mark binary files (prevents corrupt merges on .png, .fbx, .uasset, etc.)
svn propset svn:mime-type application/octet-stream Assets/Textures/Hero.dds
# Batch mark all PNG in a directory:
# bash:
find Assets/ -name "*.png" | xargs -I{} svn propset svn:mime-type application/octet-stream "{}"
# PowerShell:
Get-ChildItem -Recurse -Filter "*.png" | ForEach-Object {
    svn propset svn:mime-type application/octet-stream $_.FullName
}
```

---

## Binary Files and Asset Locking

```bash
# Exclusive lock (prevents simultaneous edits of non-mergeable binary assets)
svn lock Assets/Textures/HeroAlbedo.dds -m "Editing hero albedo texture"
svn unlock Assets/Textures/HeroAlbedo.dds

# Require lock before edit (TortoiseSVN will show lock icon)
svn propset svn:needs-lock "" Assets/Textures/HeroAlbedo.dds

# Check who holds locks
svn status -u | grep "K\|O\|T\|B"     # K=locally locked, O=other holds lock
svn info Assets/Textures/HeroAlbedo.dds  # shows lock owner and comment
```

---

## Stash Workaround (SVN has no native stash)

```bash
# Save current changes
svn diff --internal-diff > /tmp/my_stash.patch

# Clean working copy
svn revert -R .

# ... do other work, commit if needed ...

# Re-apply saved changes (use svn patch, not GNU patch)
svn patch /tmp/my_stash.patch

# If svn patch is unavailable (very old SVN < 1.7):
patch -p0 < /tmp/my_stash.patch
```

> **Use `svn patch`** (not `patch -p0`): `svn patch` understands SVN diff format including property changes, and correctly handles paths without needing to guess strip level.

---

## Game Engine Project Shortcuts

### Bash / Git Bash
```bash
# Modified C++ files only
svn status | grep "^M" | grep -E "\.(cpp|h|c|cs)$"

# Modified shaders only
svn status | grep -E "\.(hlsl|glsl|usf|ush|shader)$"

# Safely commit only shaders via changelist (handles spaces in paths)
svn status | grep "^M" | grep -E "\.(hlsl|glsl|usf|ush)$" | awk '{print $2}' | \
  xargs -I{} svn changelist shader-batch "{}"
svn commit --cl shader-batch -m "Shader: update deferred pass" --encoding UTF-8
svn changelist --remove --recursive --changelist shader-batch .

# Revert a subsystem
svn revert -R Engine/Source/Runtime/Renderer/

# Check server revision before update
svn status -u | tail -3
```

### PowerShell (Windows native)
```powershell
# Modified C++ files
svn status | Where-Object { $_ -match '^M' -and $_ -match '\.(cpp|h|c|cs)$' }

# Modified shaders
svn status | Where-Object { $_ -match '\.(hlsl|glsl|usf|ush|shader)$' }

# Commit shaders via changelist
$shaders = svn status |
    Where-Object { $_ -match '^M' -and $_ -match '\.(hlsl|glsl|usf|ush)$' } |
    ForEach-Object { $_.Substring(8).Trim() }
$shaders | ForEach-Object { svn changelist shader-batch $_ }
svn commit --cl shader-batch -m "Shader: update deferred pass" --encoding UTF-8 --non-interactive
svn changelist --remove --recursive --changelist shader-batch .

# Quick revision info
svn info --show-item last-changed-revision
svn info --show-item last-changed-author
```
