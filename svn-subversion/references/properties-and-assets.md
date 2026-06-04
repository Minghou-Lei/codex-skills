# Properties, Assets & Stash

Detailed reference for [../SKILL.md](../SKILL.md). All commands verified against
SVN 1.14.3.

## svn:ignore

```bash
svn propset svn:ignore "*.obj
*.pdb
*.suo
Binaries
Intermediate
.vs
x64" .

svn propedit svn:ignore .              # edit interactively
svn propget svn:ignore .               # view
svn commit -m "Config: update svn:ignore" --encoding UTF-8
```

`svn:ignore` is **not recursive** — it applies only to the immediate children of
the directory it is set on. For a tree-wide rule use `svn:global-ignores` (a
recursive inherited property, verified) or the client-side `global-ignores`
config:

```bash
svn propset svn:global-ignores "*.tmp *.log" .     # recursive, inherited
# ~/.subversion/config [miscellany]:
#   global-ignores = *.o *.obj *.pdb *.suo .vs Binaries Intermediate x64
```

In a Git+SVN checkout the two ignore systems are independent — a file untracked
by Git is not ignored by SVN. Check each with its own status command.

## EOL and file properties

```bash
svn propset svn:eol-style native src/Renderer/DeferredPass.cpp
svn propset svn:eol-style native -R src/        # recursive
# Values (all verified): native (CRLF on Windows, LF on Unix) | LF | CRLF | CR
```

`svn:eol-style` triggers line-ending translation on checkout/commit. Before and
after a large rewrite of Markdown / PowerShell / C++, confirm you are not seeing
a whole-file diff caused purely by EOL flips:
```bash
svn diff --internal-diff <path> > /tmp/eol_check.patch   # whole-file churn = EOL/encoding, not real edits
```

A property-only change shows as `M` in **column 2** of `svn status` (verified).
Inspect property deltas with `svn diff --properties-only <path>` (`svn diff` is
recursive by default; do not pass `-R`).

## Binary files and MIME types

SVN does not infer binary-ness from diff heuristics the way Git does. Mark binary
files so diff/log/merge behave:

```bash
svn propset svn:mime-type application/octet-stream Assets/Textures/Hero.dds
```
```bash
# Batch-mark all PNGs — bash (space-safe):
find Assets/ -name '*.png' -print0 | xargs -0 -I{} svn propset svn:mime-type application/octet-stream "{}"
```
```powershell
Get-ChildItem -Recurse -Filter '*.png' | ForEach-Object {
    svn propset svn:mime-type application/octet-stream $_.FullName
}
```

In a game repo, most **generated** binaries (`.pdb`, build output, DDC) should
not be committed at all — pin them in `svn:ignore`/`svn:global-ignores`.

## Asset locking (non-mergeable binaries)

```bash
svn lock Assets/Textures/HeroAlbedo.dds -m "Editing hero albedo texture"
svn unlock Assets/Textures/HeroAlbedo.dds

# Require a lock before editing (commit the property to enforce team-wide):
svn propset svn:needs-lock "*" Assets/Textures/HeroAlbedo.dds

# Inspect locks
svn status -u                          # 'K' you hold, 'O' other holds, 'T' stolen, 'B' broken
svn info Assets/Textures/HeroAlbedo.dds  # lock owner and comment
```

This `svn lock` asset lock is unrelated to the working-copy lock (`L` in status
column 3) cleared by `svn cleanup`.

## Stash workaround (SVN has no native stash)

```bash
svn diff --internal-diff > /tmp/my_stash.patch     # 1. save
svn revert -R .                                    # 2. clean WC
# 3. ... do other work, commit if needed ...
svn patch /tmp/my_stash.patch                      # 4. re-apply (understands SVN diff + props)
```

> ⚠️ Two verified caveats — this is **not** a faithful `git stash`:
>
> 1. **Newly added files do not round-trip cleanly.** `svn revert` un-schedules
>    an added file but leaves it on disk as unversioned. `svn patch` then reports
>    `Skipped 'file' -- obstructed by unversioned node` and does **not** re-add
>    it. After patching, manually `svn add` files that were new before the stash.
> 2. **Deletions and property-only changes** may need manual fix-up. Run
>    `svn status` after `svn patch` and reconcile.
>
> For anything beyond simple text edits, prefer a **changelist + branch** over
> this workaround.

Use `svn patch` (not `patch -p0`): it understands SVN's diff format including
property changes and resolves paths without guessing a strip level. Only fall
back to `patch -p0 < file` on SVN older than 1.7.
