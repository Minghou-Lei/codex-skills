# Windows Codex Contract

Purpose: make Codex reliable on this Windows 11 + Chinese-path + Unreal/Unity workspace.
Keep this file short. The session hook owns generic `ctx_*` routing; this file only fixes local execution failures.

## 0. Non-negotiable rule

For Windows repo/file discovery, use the consumer that will actually read the files.

If the task touches any of these:

- Windows drive path: `C:\...`, `F:\...`, `J:\...`
- Unreal/Unity/MSBuild/Visual Studio project
- `.uproject`, `.uasset`, `.sln`, `.vcxproj`, `.csproj`, `Content/`, `Plugins/`
- Chinese/non-ASCII path or filename
- external project/sample path
- repo tree discovery or source-file lookup

then FIRST probe with Windows-native filesystem access:

```text
ctx_execute(language: "javascript") using Node built-ins: fs, path, child_process
```

Do NOT start with Git Bash `ls`, `find`, `rg`, `grep`, `test -e`, or `cygpath -> ls/rg`.

Git Bash may be used only after the exact Windows repo root/path has been proven.

## 1. Evidence before search

`(no output)` is not evidence.

A path is verified only if the probe prints structured facts:

```json
{
  "consumer": "Node fs/path",
  "cwd": "...",
  "root": "J:\\...",
  "rootExists": true,
  "target": "...",
  "targetExists": true,
  "type": "file|directory|missing"
}
```

`cygpath` output only proves string conversion, not filesystem accessibility.

Do not say "not found" until the verified absolute root was searched by the correct consumer.

## 2. Path re-grounding

If a lookup missed the real directory, stop searching from CWD.

Re-anchor:

1. Identify path domain:
   - Windows-native: `X:\path`
   - Git Bash/MSYS2: `/x/path`
   - Repo-relative: only after repo root is proven
2. Verify absolute parent exists.
3. Search only inside the verified root.
4. If the user supplied an absolute Windows path, preserve it as the source of truth.

Never emit WSL paths here: no `/mnt/c/...`, no `/mnt/f/...`.

## 3. Shell identity

context-mode shell is Git Bash/MSYS2 unless PowerShell is explicitly invoked.

### Bash-safe

Use Bash only for small bounded work:

```text
git status/diff/log
mkdir/rm/mv
navigation
bounded ASCII-safe grep/rg after root is proven
```

Rules:

- Use `/c/...`, `/f/...`, `/j/...`.
- Quote every path.
- Bound output.
- Avoid Chinese paths in raw shell argv.

### PowerShell-required

The following must not appear raw in Bash:

```text
Get-* Set-* New-* Remove-* Test-Path Resolve-Path
Select-Object Where-Object ForEach-Object Format-*
$env: $_ $PSVersionTable [System.*]
```

Use `.ps1 + pwsh -File`.

## 4. PowerShell wrapper

For nontrivial Windows work:

1. Create/edit `.ps1` with native Write/Edit tools.
2. Keep `.ps1` ASCII-only when practical.
3. Put Chinese/non-ASCII paths into UTF-8 JSON/TXT manifests.
4. Run from Git Bash:

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

Fallback only if `pwsh` is unavailable:

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

Header for `.ps1` that touches files, Python, Unreal, Unity, MSBuild, or custom Windows tools:

```powershell
$ErrorActionPreference = "Stop"
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $true
}
```

## 5. MSYS2 conversion traps

When Bash calls native Windows executables, MSYS2 may rewrite path-like args.

Avoid passing literal Linux-style options to native exe unless intended.

If needed, use local one-shot exclusions only:

```bash
MSYS2_ARG_CONV_EXCL='*' native.exe --literal=/foo
MSYS2_ENV_CONV_EXCL='VAR' VAR=/foo native.exe
```

Do not set these globally.

## 6. Unicode / Chinese path rules

Most Chinese-path failures are boundary bugs.

Stop and diagnose encoding first when seeing:

| Symptom | Meaning | Action |
|---|---|---|
| `\u95E8...` in a path | escaped text reused as path | decode/regenerate |
| `????` | codepage loss | rerun through UTF-8 wrapper/manifest |
| `é—¨æ´¾` | mojibake | regenerate from original Unicode |
| false `FileNotFoundError` | wrong consumer/encoding | verify in the consuming environment |
| quoted/octal Git path | Git escaping | use `-z` or `core.quotepath=false` |

For manifests:

- JSON: `ensure_ascii=false`
- Read/write UTF-8 explicitly.
- Print normal `str(path)`, not unlabeled `repr(path)`.

## 7. Git path output

For machine parsing:

```bash
git -c core.quotepath=false status --porcelain=v1 -z
git -c core.quotepath=false diff --name-status -z
git -c core.quotepath=false ls-files -z
```

For human display:

```bash
git -c core.quotepath=false status --short
git -c core.quotepath=false diff --name-only
```

Do not change global Git config unless asked.

## 8. File writes

Follow hook write policy.

Local reinforcement:

- Use native Write/Edit for source, configs, markdown, JSON, YAML, scripts, manifests.
- Do not create files through Bash heredoc, Python writes, Node writes, or `ctx_execute` unless the user explicitly asks for that path.
- Avoid `.bat` / `.cmd` for Chinese Windows automation.
- Prefer `.ps1`, `.py`, `.js`, UTF-8 JSON/TXT.

## 9. Code-task skill loading

For code edits/reviews/debugging/scripts/shaders/build automation:

- Load `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`
- Load `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`

Do not dump skill contents. Apply them silently.
If inaccessible, state once and continue.

Use heavier workflow skills only when task clearly needs planning/research.
Do not over-route trivial edits.

## 10. Worktree safety

Before edits:

```text
check git status
identify user changes
avoid overwriting unrelated files
```

After edits:

```text
run targeted validation when practical
show changed files
report unresolved risks
```

Commit only when the user asked for commit or the active skill explicitly requires it.

## 11. Response format

Keep replies compact.

Default:

```text
- Changed: ...
- Files: ...
- Verified: ...
- Notes: ...
```

No long tool logs.
No "not found" without evidence.
No repeated guessing from CWD.
