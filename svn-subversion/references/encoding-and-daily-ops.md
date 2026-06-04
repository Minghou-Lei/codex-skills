# Encoding & Daily Operations

Detailed reference for [../SKILL.md](../SKILL.md). All commands verified against
SVN 1.14.3; Windows-only behaviours are labelled.

## Machine-readable output (the #1 automation rule)

Scripts and agents must parse SVN's XML / `--show-item` output, never the
human-readable text. `svn status --xml` and `svn log --xml` always begin
`<?xml version="1.0" encoding="UTF-8"?>` regardless of console codepage
(verified), so Chinese paths and messages survive even when pretty-printed output
shows `????`.

| Instead of parsing… | Use (machine-readable, UTF-8, stable) |
|---|---|
| `svn status` text + column slicing | `svn status --xml --no-ignore --non-interactive` |
| `svn log` text | `svn log --xml -r <rev> [URL]` |
| `svn info` text labels | `svn info --show-item url` / `revision` / `last-changed-revision` |
| Hand-built path list | a UTF-8-no-BOM `--targets` file |
| `-m "中文 message"` | a UTF-8 message file via `-F message.txt --encoding UTF-8` |

```powershell
# Canonical safe pair (verified with Chinese + spaced paths):
svn status --xml --no-ignore --non-interactive
svn commit --targets targets.txt -F message.txt --encoding UTF-8 --non-interactive
```

Valid `--show-item` values (verified): `kind`, `url`, `relative-url`,
`repos-root-url`, `repos-uuid`, `repos-size`, `revision`,
`last-changed-revision`, `last-changed-date`, `last-changed-author`, `wc-root`.

Why `--no-ignore`: plain `svn status` omits ignored items, so a script can
wrongly conclude "no changes" when ignored Chinese files exist (verified:
`ignored.tmp` is hidden by plain status, shown as `I` only with `--no-ignore`).

## UTF-8 setup (run before any SVN operation on Windows)

```batch
chcp 65001
```
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8   # Windows PowerShell 5.1 pipe fix
$env:PYTHONIOENCODING     = "utf-8"                          # if driving SVN from Python
```

In Python subprocess calls, always decode defensively:
```python
result = subprocess.run(
    ["svn", "status", "--non-interactive"],
    capture_output=True, encoding="utf-8", errors="replace",
)
```

## Windows + Chinese trap catalogue

The repository internals are almost always fine. Console encoding, pipe encoding
(`$OutputEncoding`), path encoding, and file-content encoding are four
independent things; fixing one does not fix the others.

> Verified: in a non-UTF-8 locale, `svn commit --targets utf8file.txt` fails with
> `E000022: Can't convert string from native encoding to 'UTF-8'`. After forcing
> a UTF-8 locale/codepage the same command succeeds. Make encoding consistent
> first, then run SVN.

1. **Console encoding ≠ SVN encoding.** Set UTF-8 as above before any SVN work.
2. **Chinese commit message → garbage on the server.** `svn commit -m "中文"` can
   be mangled when the terminal encoding disagrees with SVN's assumption. Write a
   UTF-8 message file and pass `-F`, declaring the encoding:
   ```powershell
   svn commit --targets targets.txt -F message.txt --encoding UTF-8 --non-interactive
   ```
3. **Single-file add/commit of a Chinese path fails.** Some clients render
   Chinese paths as `????` and reject the single-file form:
   ```powershell
   svn add "中文文件.json"   # W155010 not found / E200009 Illegal target, yet the file exists
   ```
   Workarounds: a UTF-8 targets file, or add from the nearest versioned parent so
   SVN enumerates children itself:
   ```powershell
   svn add --force --depth infinity -- reports/import_results
   ```
4. **Garbled `svn status` does not mean the WC is broken.** `????` is usually a
   terminal decode error. Do not reflexively `rename`/`delete`/`revert`. Confirm
   real state: `svn info <path>`, `svn status -u --non-interactive`, and inspect
   the on-disk name (`Get-ChildItem -LiteralPath`).
5. **Never hand-assemble commands for Chinese / spaced / parenthesised paths.**
   Use a targets file for anything batch.
6. **Windows PowerShell 5.1 `$OutputEncoding` is a trap.** Native-exe pipe
   encoding is not UTF-8 by default, so `svn status | …` can corrupt mid-pipeline
   even after `chcp 65001`. Set `$OutputEncoding` explicitly (PowerShell 7+
   defaults to UTF-8 and is safer).
7. **Do not feed raw `svn diff` to automation.** Write to a file first (see
   [Diff safety](#diff-safety)).
8. **File-content encoding ≠ path encoding.** A committable Chinese path says
   nothing about the file's byte encoding. Do not rewrite old files with
   `Set-Content`/`Out-File` casually; detect and preserve the original
   encoding/BOM/EOL.
9. **Do not use `svn ls` to check local tracking state.** `svn ls` queries a
   repository URL/revision, not the working copy. Use `svn status -u
   --non-interactive` and `svn info <path>`.
10. **Keep machine-local / generated items out of batch commits.** Use an
    explicit targets list, not a blanket directory commit.
11. **Write `--targets`/message files as UTF-8 no BOM via .NET.** `Out-File` /
    `Set-Content` defaults vary by version and can add a BOM:
    ```powershell
    [IO.File]::WriteAllLines($targetsFile, $paths, [System.Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($msgFile, $message, [System.Text.UTF8Encoding]::new($false))
    ```
12. **URL-encode per path segment; never double-encode.**
    `金水镇 -> %E9%87%91%E6%B0%B4%E9%95%87`. Encode the segment, leave the scheme,
    host, and separators alone; never re-escape an already-encoded URL.
13. **Deleting a *missing* Chinese path: URL delete as last resort.** If the
    local-path `svn delete` fails on a decoded-wrong argument:
    ```powershell
    svn delete <per-segment-encoded-url> -F message.txt --encoding UTF-8 --non-interactive
    ```
    URL delete is an immediate server commit (verified), not a local schedule.
    Use it deliberately and document it.
14. **Read Chinese `svn log` content as XML, not text:**
    `svn log --xml -r 12345 <url>`.

> **Mental model:** make console, pipe, path, and file-content encoding all
> UTF-8 (or all consistently GBK) before touching SVN; drive batch work from
> `--targets` + `-F`; parse XML/`--show-item`, never human text; treat `????`
> as a display bug until proven otherwise.

## TortoiseSVN 1.15.0-dev Unicode path case study

Concrete instance of trap 3. Observed with TortoiseSVN `svn.exe` 1.15.0-dev:

- `svn status` shows Chinese filenames as `????` while the files exist.
- `svn add "reports\...\wj_ylc圣女雕像001_001_hd.xxx.json"` fails with
  `W155010 ... not found` / `E200009 Illegal target`.
- `chcp 65001`, PowerShell `LiteralPath`, Node `spawnSync`, and absolute paths
  may still fail because the client decodes the argument through the wrong
  codepage.
- Directory-level recursive add succeeds because SVN enumerates children:
  ```powershell
  svn add --force --depth infinity -- reports\import_results
  svn commit reports\import_results -F msg.txt --encoding UTF-8 --non-interactive
  ```

Agent rule:
1. If single-file `svn add` fails for a non-ASCII path but the file exists, do
   **not** rename the file unless the user approves.
2. Retry at the nearest versioned parent with `svn add --force --depth infinity
   -- <dir>`.
3. Re-run `svn status` and commit the parent dir or the scheduled `A` targets via
   a `--targets` list.
4. Keep generated caches (`DerivedDataCache`, `Saved`, `Intermediate`, missing
   `!` files) out of the commit unless asked.
5. Do the `add` and the `commit` under the **same** UTF-8 encoding (verified:
   adding under a non-UTF-8 locale then committing under UTF-8 yields `E155010
   node not found` / a stale `?` — re-add under the correct encoding first).

## Daily workflow

### Pre-flight (start of a session)
```bash
svn info --show-item revision          # WC health check; fails if WC is corrupt
svn status -u | tail -3                # pending server changes
svn cleanup --non-interactive          # release stale locks
```

### Status & info
```bash
svn status                             # alias: svn st / svn stat
svn status -u                          # include server-side changes
svn status --xml --no-ignore --non-interactive   # for scripts
svn info
svn info --show-item last-changed-revision
svn info --show-item last-changed-author
svnversion                             # "1234" uniform; "1234:1236" mixed; trailing M = local mods
```
For the full seven-column status decoding and path-extraction rules, see
[../SKILL.md](../SKILL.md#svn-status-columns).

### Update
```bash
svn update --non-interactive           # alias: svn up
svn update -r 1234
svn update <file>
svn update --accept postpone           # auto-postpone conflicts (valid for update)
svn update --ignore-externals
```

### Add / delete / move
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

### Revert
```bash
svn revert <file>
svn revert -R .                        # DESTRUCTIVE — discards all uncommitted changes
svn revert -R src/Renderer/
```
`svn revert` un-schedules an added file (`A` → `?`) but does **not** delete it
from disk; the file remains unversioned (relevant to the stash workflow).

### Commit
```bash
svn diff --internal-diff > /tmp/review.patch && cat /tmp/review.patch   # review first
svn commit -m "Fix: description" --encoding UTF-8 --non-interactive
svn commit file1.cpp file2.h -m "Refactor: extract helper" --encoding UTF-8
svn commit --targets targets.txt -F msg.txt --encoding UTF-8 --non-interactive   # batch, Chinese-safe
```
Message conventions: `Fix:` `Feature:` `Refactor:` `Shader:` `Asset:`.

> On Windows, prefer `-F message.txt` over inline `-m "中文"` (shell quoting +
> codepage). See the trap catalogue above.

## Parsing svn status safely

`svn status` emits 7 fixed columns, a space, then the path starting at column 9.
Not whitespace-delimited; paths may contain spaces.

| Goal | Bash | PowerShell |
|------|------|-----------|
| Extract path | `cut -c9-` | `$_.Substring(8).Trim()` |
| Modified only | `grep '^M' \| cut -c9-` | `... -match '^M' ...` |
| Untracked only | `grep '^?' \| cut -c9-` | `... -match '^\?' ...` |
| Missing only | `grep '^!' \| cut -c9-` | `... -match '^!' ...` |

Never use `awk '{print $2}'` — it corrupts any path with a space (verified:
`my dir` → `my`). For scripts, prefer `--xml`.

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

Include these in scripted contexts.

| Flag | Purpose |
|------|---------|
| `--non-interactive` | Prevents hanging on auth/certificate prompts |
| `--no-auth-cache` | Don't read/write the credentials cache (CI) |
| `--trust-server-cert-failures=ARG` | With `--non-interactive`, accept listed SSL failures. Valid ARGs: `unknown-ca`, `cn-mismatch`, `expired`, `not-yet-valid`, `other` (comma-separated) |
| `--encoding UTF-8` | Explicit message encoding on commit |
| `--targets FILE` | Read target paths from FILE (one per line). Robust for Chinese/spaced paths; FILE must match the active console encoding |
| `-F FILE` (`--file`) | Read the commit message from FILE. Use a UTF-8 file instead of inline `-m` for Chinese |

`--trust-server-cert` (no suffix) is **deprecated**; equivalent to
`--trust-server-cert-failures=unknown-ca`. Prefer the explicit form.

```bash
svn commit file.cpp \
  -m "Fix: auto-patched by agent" \
  --encoding UTF-8 --non-interactive --no-auth-cache \
  --trust-server-cert-failures=unknown-ca,cn-mismatch
```

## Conflict resolution

```bash
svn status | grep '^C'                 # list conflicted files

# Valid --accept values (verified): base | working | mine-conflict |
#   theirs-conflict | mine-full | theirs-full   (postpone is for `update`, not `resolve`)
svn resolve --accept mine-full <file>      # keep local entirely
svn resolve --accept theirs-full <file>    # take server entirely
svn resolve --accept working <file>        # manual edit done, mark resolved

# Manual merge: edit out <<<< ==== >>>> markers, then:
svn resolve --accept working <file>
svn status | grep '^C'                     # must be empty before committing
```

> `svn resolved <file>` (no `--accept`) is **deprecated** in favour of
> `svn resolve --accept working <file>`, and it only clears the conflicted state
> — it does not remove conflict markers from the file.

For **tree conflicts** (directory deleted/moved/replaced on the server), markers
don't apply — use `svn info <path>` for the description, then resolve once
understood.
