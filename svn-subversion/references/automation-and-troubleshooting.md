# Automation & Troubleshooting

Reference for [../SKILL.md](../SKILL.md). Cross-cutting concerns for scripting SVN
reliably. SVN-side facts verified against 1.14.3; PowerShell- and Git-specific
behaviours are marked **(unverified here)** — the Linux test harness has no
PowerShell and no dual-VCS checkout.

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
| Hand-built path list | a UTF-8-no-BOM `--targets` file (commit/add/… only) |
| `-m "中文 message"` | a UTF-8 message file via `-F message.txt --encoding UTF-8` |

```powershell
# Canonical safe pair (verified with Chinese + spaced paths):
svn status --xml --no-ignore --non-interactive
svn commit --targets targets.txt -F message.txt --encoding UTF-8 --non-interactive
```

> Parse the XML with a real parser. Matching `path="..."` by hand also catches
> the `<target path=".">` wrapper element, injecting a spurious `.` into your
> file list (verified). Correct extraction:
> ```bash
> svn status --xml --no-ignore | python3 -c \
>   'import sys,xml.etree.ElementTree as ET; [print(e.get("path")) for e in ET.fromstring(sys.stdin.read()).iter("entry")]'
> ```

Why `--no-ignore`: plain `svn status` omits ignored items, so a script can
wrongly conclude "no changes" when ignored Chinese files exist (verified:
`ignored.tmp` is hidden by plain status, shown as `I` only with `--no-ignore`).

## Probing working-copy state (exit codes are information)

SVN uses non-zero exit codes as *signals*, not just failures — `svn info
<unversioned>` returns exit 1 with `W155010 ... not found` to mean "not tracked"
(verified; a versioned path returns exit 0). Scripts that treat any non-zero exit
as fatal will misclassify normal states.

```bash
# bash: branch on the signal, don't abort
if svn info "$path" >/dev/null 2>&1; then echo "tracked"; else echo "not tracked"; fi
```

Similarly, `svn propget svn:externals .` exits 1 with `W200017: Property not
found` when there are no externals (verified) — not an empty success. Treat that
exit-1 as "no externals", not an error.

## PowerShell-7 exit-code and log traps

Reported from real runs; **unverified here** (no PowerShell in the Linux
harness). Both interact badly with SVN's use of non-zero exit codes as
information.

- **`$PSNativeCommandUseErrorActionPreference = $true` turns expected non-zero
  exits into terminating errors.** `svn info <unversioned>` returning exit 1 is a
  normal "not tracked" signal (verified at the SVN level), but with that
  preference on, a classification script aborts. Probe with it off, or wrap in
  try/catch and read `$LASTEXITCODE`:
  ```powershell
  $prev = $PSNativeCommandUseErrorActionPreference
  $PSNativeCommandUseErrorActionPreference = $false
  try { svn info $path *> $null; $tracked = ($LASTEXITCODE -eq 0) }
  finally { $PSNativeCommandUseErrorActionPreference = $prev }
  ```
- **Mixed native + cmdlet output corrupts validation logs.** Piping native SVN
  output through `Tee-Object` / `Add-Content` can inject NUL / UTF-16-style bytes,
  making a verification wrapper falsely report failure. Capture with a Python
  subprocess (`encoding="utf-8", errors="replace"`) or `[IO.File]::WriteAllText`
  instead of mixing cmdlet redirection with native stdout.

## Git + SVN dual checkout: re-check after every update

**Unverified here** (no dual-VCS checkout in the harness); reported from a live
Git+SVN repo and consistent with the independent-ignore-systems behaviour.

An `svn update` that merges a remote revision can introduce content the Git side
now sees as tracked modifications; committing through SVN may then ship a merge
result Git never recorded. Treat "SVN update" and "git status" as a paired step:

```bash
svn update --accept postpone --non-interactive
svn status --xml | grep -q 'item="conflicted"' && echo "resolve SVN conflicts first"
# resolve any SVN conflicts, then look at what the merge did to the Git view:
git status --porcelain        # empty = SVN merge introduced nothing new to Git
git diff                      # review merge result before any SVN commit
```

If `git status` is non-empty after resolving, decide deliberately whether those
merge results should be committed (to SVN, to Git, or reverted) — do not let an
`svn commit` ship a change Git never recorded.
