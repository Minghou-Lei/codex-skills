# Game-Engine Shortcuts

Copy-paste snippets for engine repos. The bash filter pipelines were executed
against SVN 1.14.3 on versioned-then-modified files (verified working). For
scripts, prefer `svn status --xml --no-ignore` over text slicing; these
interactive shortcuts trade that for brevity.

All path extraction uses column slicing (`cut -c9-` / `.Substring(8)`) so paths
with spaces survive — see [../SKILL.md](../SKILL.md#svn-status-columns).

## Bash / Git Bash

```bash
# Modified C++ files only
svn status | grep '^M' | cut -c9- | grep -E '\.(cpp|h|c|cs)$'

# Modified shaders only
svn status | grep '^M' | cut -c9- | grep -E '\.(hlsl|glsl|usf|ush|shader)$'

# Commit only shaders via a changelist (space-safe)
svn status | grep '^M' | cut -c9- | grep -E '\.(hlsl|glsl|usf|ush)$' | \
  while IFS= read -r f; do svn changelist shader-batch "$f"; done
svn commit --cl shader-batch -m "Shader: update deferred pass" --encoding UTF-8 --non-interactive
svn changelist --remove --recursive --changelist shader-batch .

# Revert a subsystem
svn revert -R Engine/Source/Runtime/Renderer/

# Check server revision before update
svn status -u | tail -3
```

## PowerShell (Windows native)

> Set UTF-8 first (`chcp 65001`, `$OutputEncoding = [System.Text.Encoding]::UTF8`)
> — see [references/encoding-and-daily-ops.md](encoding-and-daily-ops.md).

```powershell
# Modified C++ files
svn status | Where-Object { $_ -match '^M' -and $_ -match '\.(cpp|h|c|cs)$' } |
    ForEach-Object { $_.Substring(8).Trim() }

# Modified shaders
svn status | Where-Object { $_ -match '^M' -and $_ -match '\.(hlsl|glsl|usf|ush|shader)$' } |
    ForEach-Object { $_.Substring(8).Trim() }

# Commit shaders via a changelist
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

## Generated-directory ignore baseline (UE-style repos)

Pin these so directory-level adds and batch commits can't sweep them in:

```bash
svn propset svn:global-ignores "Binaries Intermediate Saved DerivedDataCache *.pdb *.pid *.log" .
svn commit -m "Config: ignore generated dirs" --encoding UTF-8
```

See the release-flow hard rules in [../SKILL.md](../SKILL.md#release-flow-hard-rules-game-studio-automation).
