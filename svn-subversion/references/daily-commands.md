# Daily Commands

Reference for [../SKILL.md](../SKILL.md). All commands verified against SVN
1.14.3.

## Pre-flight (start of a session)
```bash
svn info --show-item revision          # WC health check; fails if WC is corrupt
svn status -u | tail -3                # pending server changes
svn cleanup --non-interactive          # release stale locks
```

## Status & info
```bash
svn status                             # alias: svn st / svn stat
svn status -u                          # include server-side changes
svn status --xml --no-ignore --non-interactive   # for scripts
svn info
svn info --show-item last-changed-revision
svn info --show-item last-changed-author
svnversion                             # "1234" uniform; "1234:1236" mixed; trailing M = local mods
```
Valid `--show-item` values (verified): `kind`, `url`, `relative-url`,
`repos-root-url`, `repos-uuid`, `repos-size`, `revision`,
`last-changed-revision`, `last-changed-date`, `last-changed-author`, `wc-root`.

The full seven-column status decoding is in
[../SKILL.md](../SKILL.md#svn-status-columns).

## Parsing svn status

`svn status` emits 7 fixed columns, a space, then the path starting at column 9.
Not whitespace-delimited; paths may contain spaces.

| Goal | Bash | PowerShell |
|------|------|-----------|
| Extract path | `cut -c9-` | `$_.Substring(8).Trim()` |
| Modified only | `grep '^M' \| cut -c9-` | `... -match '^M' ...` |
| Untracked only | `grep '^?' \| cut -c9-` | `... -match '^\?' ...` |
| Missing only | `grep '^!' \| cut -c9-` | `... -match '^!' ...` |

Never use `awk '{print $2}'` — it corrupts any path with a space (verified:
`my dir` → `my`). For scripts, prefer XML and parse it with a real parser
(matching `path="..."` by hand also catches the `<target path=".">` wrapper):
```bash
svn status --xml --no-ignore | python3 -c \
  'import sys,xml.etree.ElementTree as ET; [print(e.get("path")) for e in ET.fromstring(sys.stdin.read()).iter("entry")]'
# (or: svn status --xml | xmllint --xpath "//entry/@path" - )
```

## Where `--targets` is and isn't accepted

Verified support matrix on 1.14.3. `--targets` is accepted by **`commit`,
`add`, `delete`, `revert`, `info`, `lock`, `unlock`, `changelist`, `propset`,
`log`**, and **rejected by `update` and `status`** (both exit 1 with `doesn't
accept option '--targets'`). Three working replacements for `update`/`status`
over many paths (all verified):

```bash
# A. Pass paths as positional args (simplest — status/update take multiple paths)
svn status -- p1.txt "spaced name.txt"
svn update --non-interactive -- p1.txt p2.txt

# B. Loop per path from a list file (when paths come from a generated file)
while IFS= read -r p; do svn update --non-interactive -- "$p"; done < paths.txt

# C. Aggregate state from XML, then act (script-grade; parse XML properly)
svn status --xml --no-ignore | python3 -c \
  'import sys,xml.etree.ElementTree as ET; [print(e.get("path")) for e in ET.fromstring(sys.stdin.read()).iter("entry")]'
```
```powershell
# PowerShell equivalent of A/B
$paths = Get-Content paths.txt
svn update --non-interactive -- @paths
```

## Update
```bash
svn update --non-interactive           # alias: svn up
svn update -r 1234
svn update <file>
svn update --accept postpone           # auto-postpone conflicts (valid for update)
svn update --ignore-externals
```

> A conflicting `update --accept postpone` still exits 0 (verified) — re-check
> status afterward; see
> [conflicts-and-merging.md](conflicts-and-merging.md#conflict-resolution).

## Add / delete / move
```bash
svn add new_file.cpp
svn add new_dir/ --force                       # add dir + contents recursively
svn add --force --depth infinity -- <dir>      # robust for Chinese/spaced paths
svn delete old_file.cpp
svn delete --force old_file.cpp                # if locally modified
svn move old_name.cpp new_name.cpp             # rename, preserves history

# Add all untracked, column-safe (handles spaces):
svn status | grep '^?' | cut -c9- | while IFS= read -r f; do svn add "$f"; done
```
```powershell
svn status | Where-Object { $_ -match '^\?' } |
    ForEach-Object { svn add $_.Substring(8).Trim() }
```

> **Case-only rename on Windows** (case-insensitive FS): `Foo.md → foo.md` can
> register as "no change" or a broken state. Do it in two commits via a temp
> name (verified to work on a case-sensitive FS; the hazard is Windows-specific):
> ```bash
> svn move Foo.md Foo_tmp.md && svn commit -m "rename step 1" --encoding UTF-8
> svn move Foo_tmp.md foo.md  && svn commit -m "rename step 2" --encoding UTF-8
> ```

## Revert
```bash
svn revert <file>
svn revert -R .                        # DESTRUCTIVE — discards all uncommitted changes
svn revert -R src/Renderer/
```
`svn revert` un-schedules an added file (`A` → `?`) but does **not** delete it
from disk; the file remains unversioned (relevant to the stash workflow).

## Commit
```bash
svn diff --internal-diff > /tmp/review.patch && cat /tmp/review.patch   # review first
svn commit -m "Fix: description" --encoding UTF-8 --non-interactive
svn commit file1.cpp file2.h -m "Refactor: extract helper" --encoding UTF-8
svn commit --targets targets.txt -F msg.txt --encoding UTF-8 --non-interactive   # batch, Chinese-safe
```
Message conventions: `Fix:` `Feature:` `Refactor:` `Shader:` `Asset:`.

> **Committing a newly added directory:** include the directory **and** its
> children in the targets list. If a new dir is scheduled `A` (e.g.
> `.planning/phases`, `docs/reference`), a targets file listing only a child file
> fails (verified): `E200009: '<dir>' is not known to exist in the repository
> and is not part of the commit, yet its child '<file>' is part of the commit`.
> Correct targets:
> ```
> docs
> docs/reference
> docs/reference/x.md
> ```

> On Windows, prefer `-F message.txt` over inline `-m "中文"` (shell quoting +
> codepage) — see [encoding-and-paths.md](encoding-and-paths.md).

## Diff safety

`svn diff` unified-diff headers contain a literal tab — `--- a.txt\t(revision 1)`
and `+++ a.txt\t(working copy)` (verified) — which corrupts agent JSON pipelines.
Write to a file first.

```bash
svn diff --internal-diff > /tmp/svn_changes.patch
cat /tmp/svn_changes.patch
svn diff --internal-diff src/RenderPipeline.cpp > /tmp/one.patch
svn diff --internal-diff -r 1233:1234 src/ > /tmp/range.patch
```

`--internal-diff` forces SVN's built-in engine, overriding any `diff-cmd` in
`~/.subversion/config` — important for reproducible agent output.

`svn diff` is **recursive by default and rejects `-R`** (verified: `Subcommand
'diff' doesn't accept option '-R'`; it uses `--depth`). Property-only deltas
don't appear in the text body — use `--properties-only`:
```bash
svn diff --properties-only <path>                       # only property changes
svn diff --properties-only . | grep -i mergeinfo        # spot stray mergeinfo (recursive by default)
```

## Cleanup & recovery

After an interrupted operation (network drop, timeout, kill) the WC may be
write-locked (`L`). Run cleanup first.

```bash
svn cleanup
svn cleanup --vacuum-pristines         # also reclaim disk (removes cached base files)
svn cleanup --non-interactive
```

> ⚠️ `svn cleanup --remove-unversioned` and `--remove-ignored` **permanently
> delete files from disk** — in a game project this can wipe build output and
> local-only assets. Never run them in automation without explicit approval.

Recovery after an interrupted op:
```bash
svn cleanup
svn status                             # assess
svn status | grep '^C'                 # conflicts introduced?
svn update --non-interactive           # re-sync
```

## Changelist (SVN's staging area)

Changelists group already-modified files for selective commit (you cannot add an
unversioned file to one). Alias: `cl`.

```bash
svn changelist my-feature src/Renderer/DeferredPass.cpp src/Renderer/ShadowMap.h
svn status --cl my-feature
svn commit --cl my-feature -m "Feature: deferred shadow refinement" --encoding UTF-8
svn changelist --remove --recursive --changelist my-feature .
svn status | grep -- '--- Changelist'      # list changelist headers (no leading anchor)
```

Agent workflow:
```bash
svn changelist agent-patch File1.cpp File2.h File3.hlsl
svn diff --internal-diff --cl agent-patch > /tmp/agent_patch_review.patch
svn commit --cl agent-patch -m "Fix: agent-applied patch" --encoding UTF-8 --non-interactive
svn changelist --remove --recursive --changelist agent-patch .
```

## Automation flags

| Flag | Purpose |
|------|---------|
| `--non-interactive` | Prevents hanging on auth/certificate prompts |
| `--no-auth-cache` | Don't read/write the credentials cache (CI) |
| `--trust-server-cert-failures=ARG` | With `--non-interactive`, accept listed SSL failures. Valid ARGs: `unknown-ca`, `cn-mismatch`, `expired`, `not-yet-valid`, `other` (comma-separated) |
| `--encoding UTF-8` | Explicit message encoding on commit |
| `--targets FILE` | Read target paths from FILE (one per line). Robust for Chinese/spaced paths; FILE must match the active console encoding. **Not accepted by `update`/`status`** |
| `-F FILE` (`--file`) | Read the commit message from FILE. Use a UTF-8 file instead of inline `-m` for Chinese |

`--trust-server-cert` (no suffix) is **deprecated**; equivalent to
`--trust-server-cert-failures=unknown-ca`. Prefer the explicit form.

```bash
svn commit file.cpp \
  -m "Fix: auto-patched by agent" \
  --encoding UTF-8 --non-interactive --no-auth-cache \
  --trust-server-cert-failures=unknown-ca,cn-mismatch
```

## Viewing history
```bash
svn log -l 20                          # last 20
svn log -r 1230:1240                   # revision range
svn log -v -r 1234                     # verbose: changed files
svn log <file>                         # file history
svn diff --internal-diff -r 1233:1234 > /tmp/rev_diff.patch
svn blame <file>                       # alias: praise / annotate / ann
svn cat -r 1234 src/file.cpp > /tmp/old_version.cpp

# Machine-readable (best for agents — UTF-8, no codepage ambiguity):
svn log -l 10 --xml > /tmp/svn_log.xml
svn log --xml -r 12345 <url>           # single revision, e.g. for a release note
```
