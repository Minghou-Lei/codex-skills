# Local Windows CN Execution Contract

Purpose: supplement the session `context_window_protection` hook with durable local Windows rules only.
Do not duplicate hook-owned `ctx_*` routing, raw-output limits, fetch policy, or artifact-output policy here.
Apply both; the stricter rule wins.

## 0. Priority

1. Current user request.
2. Safety / irreversible-action checks.
3. Session hook: `context_window_protection`.
4. This local `AGENTS.md`.
5. Repo-local build/test rules.

If this file conflicts with hook-injected tool routing, the hook wins.

This file mainly covers: Windows shell identity, Git Bash/MSYS2 path behavior, Chinese/Unicode paths, PowerShell wrappers, encoding safety, and skill routing.

## 1. Operating principles

- Infer first. Ask only when blocked, unsafe, or ambiguity changes the result.
- Root cause before patch. Avoid symptom-only fixes.
- Minimal footprint. No unrelated refactors, formatting churn, or dependency changes.
- Evidence before done. Verify with the narrowest reliable check available.
- Preserve user constraints, active decisions, and session roles until revoked.
- Never expose secrets, tokens, private endpoints, or unnecessary environment details.

## 2. Local machine facts

- OS: Windows 11, Chinese-language environment is possible.
- context-mode `language: "shell"` and `ctx_batch_execute` commands run as Git Bash / MSYS2 unless PowerShell is explicitly invoked.
- Native Windows tools consume Windows paths: `F:\Repo\Project` or `F:/Repo/Project`.
- Git Bash consumes MSYS paths: `/f/Repo/Project`.
- WSL is not used here. Never emit `/mnt/c/...`, `/mnt/f/...`, or other WSL-style local-drive paths.
- The environment may contain Chinese usernames, Chinese filenames, GBK/CP936 legacy files, UTF-8 BOM files, UTF-16 files, and mixed-encoding engine assets.

## 3. context-mode / Codex boundaries

- context-mode routing is hook-owned. Do not restate `ctx_search`, `ctx_batch_execute`, `ctx_execute`, `ctx_execute_file`, or fetch rules here.
- Treat Codex hooks as guardrails, not full command rewriting. PreToolUse may block, but do not assume it can rewrite incorrect tool input.
- On Windows Codex, failing shell calls may not reliably produce PostToolUse events. For investigative commands where output must be captured, print the exit code and avoid losing diagnostics.
- Do not claim context-mode captured a failure unless evidence exists in tool output or session diagnostics.
- If hook/session state looks stale, verify current cwd/session before acting. Do not infer from old hook metadata alone.

## 4. Shell identity — never confuse Git Bash with PowerShell

Assume the default shell can be Git Bash / MSYS2, not PowerShell.

### Never do this in Bash

```bash
Get-ChildItem F:\Repo
Select-String -Path .\file.txt -Pattern foo
$env:Path
cmd /c dir
powershell.exe -File script.ps1   # unsafe for UTF-8 scripts on Windows PowerShell 5.1
```

### Use this instead

```bash
pwd
ls -la "/f/Repo"
grep -R "foo" .
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "script.ps1"
```

For nontrivial Windows logic, create a `.ps1` with native Write/Edit tools, then run it with `pwsh -File`.
Avoid complex inline `pwsh -Command` unless the command is tiny and ASCII-only.

If `pwsh` is unavailable and Windows PowerShell 5.1 must be used, do not run UTF-8 scripts directly with `powershell.exe -File`. Use a bootstrap that explicitly reads UTF-8, or use `-EncodedCommand` with UTF-16LE Base64.

## 5. Command preflight — mandatory

Before any shell command, classify it.

### `BASH_SAFE_SMALL`

Allowed only for small, bounded Git Bash work permitted by the hook.
Examples: `git`, `rg -m`, `find ... | head`, `mkdir`, `rm`, `mv`, navigation.

Rules:

- Use MSYS paths: `/c/...`, `/f/...`, `/j/...`.
- Quote every path.
- Bound output before execution.
- Do not pass complex Chinese/non-ASCII paths through raw shell argv when a manifest/wrapper is practical.
- Do not use Bash for commands that produce large raw output; let the hook/context-mode indexed workflow own that.

### `POWERSHELL_REQUIRED`

Any command containing PowerShell cmdlets or syntax:

```text
Get-* Set-* New-* Remove-* Test-Path Resolve-Path
Select-Object Where-Object ForEach-Object Format-*
$env: $_ $PSVersionTable [System.IO.*]
```

Rules:

- Must not appear raw in Bash.
- Use a `.ps1` wrapper.
- Create/edit the `.ps1` with native Write/Edit tools, not Bash heredoc or `ctx_execute`.
- Run the wrapper through `pwsh -File` from context-mode shell.

### `WINDOWS_NATIVE_WITH_NON_ASCII_PATHS`

Any native Windows tool/script receiving Chinese or non-ASCII paths:

```text
python.exe pwsh.exe powershell.exe UnrealEditor.exe UnrealEditor-Cmd.exe
Unity.exe MSBuild.exe devenv.exe custom .exe import/export tools
```

Rules:

- Prefer ASCII-only `.ps1` wrapper + UTF-8 JSON/TXT manifest.
- Verify paths in the same environment that will consume them.
- Do not trust a Bash `test -e` result for a path later used by Windows Python, Unreal, Unity, MSBuild, or a Windows `.exe`.

### `AMBIGUOUS`

Mixed Bash + PowerShell syntax, mixed path styles, or unclear interpreter.
Stop and rewrite as `.ps1`, `.py`, `.js`, or small Bash.

## 6. Path domains

| Consumer | Path style |
|---|---|
| Git Bash / MSYS2 | `/f/Repo/Project` |
| PowerShell / Windows tools | `F:\Repo\Project` or `F:/Repo/Project` |
| WSL | not used; never `/mnt/f/...` |

Rules:

- Do not assume CWD is repo root. Use absolute paths when uncertain.
- Use `cygpath -w /f/Repo` when passing a Bash path to Windows tools.
- Use `cygpath -u 'F:\Repo'` when passing a Windows path to Bash.
- Use `-LiteralPath` in PowerShell for filesystem paths.
- Quote all paths.
- Do not mix backslashes into Bash paths. `\t`, `\n`, and `\U` can be interpreted as escapes by tools.

## 7. MSYS2 argument/path conversion pitfalls

Git Bash/MSYS2 may auto-convert arguments that look like Unix paths before launching native Windows programs.
This can break switches such as `/c`, foreign paths such as `/sdcard`, Docker/WSL-style mounts, and values like `--root=/` or `--arg=/path`.

Rules:

- Prefer PowerShell or `cmd.exe` outside Bash for Windows-native workflows.
- When a native `.exe` must be called from Bash, pass Windows paths as `C:/path/with/forward/slashes` where possible.
- If arguments must not be converted, wrap only that call with:

```bash
MSYS2_ARG_CONV_EXCL='*' native.exe /literal/switch --root=/ "C:/path"
```

- For environment variables that must preserve Unix-style values, use:

```bash
MSYS2_ENV_CONV_EXCL='VAR_NAME' VAR_NAME=/literal/value native.exe
```

- Do not globally export `MSYS2_ARG_CONV_EXCL='*'` for an entire session unless the task explicitly requires it.

## 8. PowerShell wrapper policy

Do not use complex `pwsh -Command` / `powershell -Command` one-liners.

Use this pattern:

1. Create a temporary `.ps1` using native Write/Edit tools.
2. Keep the `.ps1` ASCII-only when possible.
3. Put Chinese/non-ASCII paths in a UTF-8 JSON/TXT manifest.
4. Run from context-mode shell:

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

Fallback only if `pwsh` is unavailable:

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

Required header for `.ps1` touching files, Python, Unreal, Unity, MSBuild, or custom Windows tools:

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

Recommended PowerShell file-write pattern:

```powershell
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
```

## 9. Unicode / Chinese path hard rules

Most Chinese-path failures here are boundary bugs, not business-logic bugs.

### Stop and diagnose encoding first when seeing

| Symptom | Meaning | Action |
|---|---|---|
| `\u95E8\u6D3E...` inside a path | escaped JSON/text reused as a path | decode/regenerate; never pass literal `\uXXXX` to filesystem APIs |
| `????` | lossy codepage conversion | rerun through UTF-8 wrapper/manifest |
| `é—¨æ´¾`-style mojibake | UTF-8/GBK mismatch | regenerate from original Unicode source |
| false `FileNotFoundError` on known Chinese path | path corrupted before consumer | verify in the consumer environment |
| quoted/octal Git paths | `core.quotepath` escaping | use `git -c core.quotepath=false ...` |

### Representation rule

Keep these separate:

- Valid path: `F:\...\门派室内长歌门\JZ_cgm`
- Invalid as path: `F:\...\\u95E8\\u6D3E...\JZ_cgm`
- Corrupted path: `F:\...\é—¨æ´¾...` or `????`

Never manually patch mojibake unless doing explicit data recovery. Regenerate from source.

### Bash UTF-8 defaults for text/path work

For Bash commands touching text or filenames:

```bash
export LANG=${LANG:-zh_CN.UTF-8}
export LC_CTYPE=${LC_CTYPE:-zh_CN.UTF-8}
export LESSCHARSET=utf-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

Never set `LC_ALL=C` for non-ASCII work.
Do not blindly normalize encodings.
Avoid global `chcp 65001` as a universal fix.
Treat Windows PowerShell 5.1 as unsafe for UTF-8 script decoding unless explicitly bootstrapped.
Prefer UTF-8 without BOM for new repo text files unless existing project style says otherwise.

### Manifests for non-ASCII paths

Do not pass complex Chinese paths through shell quoting. Use UTF-8 JSON/TXT manifests.

Python:

```python
Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
data = json.loads(Path(p).read_text(encoding="utf-8"))
```

Node:

```javascript
fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf8");
const data = JSON.parse(fs.readFileSync(p, "utf8"));
```

Normal diagnostics should print `str(path)`, not `repr(path)`. Use `repr` only as labeled diagnostics.

## 10. Git in Chinese filename repos

Rules:

- Prefer machine-readable Git output over localized/human output.
- Use `-z` when parsing filenames.
- Use `core.quotepath=false` when displaying Chinese filenames to the user.
- Do not change global Git config unless the user asks.
- Do not parse quoted octal escapes from default Git output as real filenames unless no better output is available.

For scripts/agents that parse file lists:

```bash
git -c core.quotepath=false status --porcelain=v1 -z
git -c core.quotepath=false diff --name-status -z
git -c core.quotepath=false ls-files -z
```

For short human display only:

```bash
git -c core.quotepath=false status --short
git -c core.quotepath=false diff --name-only
git -c core.quotepath=false ls-files
```

## 11. Chinese path `FileNotFoundError` playbook

When a script/tool reports missing file under a Chinese/non-ASCII path:

1. Capture the exact path received by the failing process.
2. Check for literal `\uXXXX`, `????`, mojibake, Git octal escapes.
3. Verify intended Windows path in PowerShell:

```powershell
if (-not (Test-Path -LiteralPath $Path)) { throw "missing path: $Path" }
```

4. Check manifest/file encoding is UTF-8 and JSON uses `ensure_ascii=False`.
5. Rerun through `.ps1 + pwsh -File` with the required UTF-8 header.
6. Only then inspect business logic or asset discovery.

## 12. Command failure capture

On Windows Codex, avoid losing diagnostics from nonzero shell exits.

For investigative Bash commands:

```bash
set +e
some_command
rc=$?
printf '\n__exit_code=%s\n' "$rc"
exit 0
```

Then report `__exit_code` truthfully. Do not treat the wrapper `exit 0` as success of `some_command`.

For verification commands where the process exit code itself is the evidence, let the command fail normally, but include the failure details in the final response.

## 13. File creation / modification reminder

The hook owns the main write policy. Local extension:

- Use native Write/Edit tools for generated wrappers, manifests, configs, source, markdown, JSON, YAML, and scripts.
- Do not create files via Bash heredoc, `ctx_execute`, Python writes, or Node writes unless the user explicitly asks for that execution path.
- Avoid `.bat` / `.cmd` for Chinese Windows automation.
- If `.bat` / `.cmd` is unavoidable, keep it ASCII-only.
- Prefer `.ps1`, `.py`, `.js`, or UTF-8 text files.

## 14. Editing rules

- Read enough surrounding context before editing.
- Preserve existing style, naming, layout, line endings, and encoding unless the task requires change.
- Prefer small, reviewable diffs.
- For config changes, keep comments only when they prevent repeat mistakes.
- For generated docs/configs, make them deterministic and easy to diff.
- For failures, report exact failing area, likely cause, and next concrete check.

## 15. Code-task skill routing

For any code generation, modification, review, debugging, refactor, tests, scripts, shaders, build files, or automation:

1. Load `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`.
2. Load `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`.
3. Apply both; do not treat them as optional.

If a skill file is inaccessible, state it and continue with the closest known rules.
For trivial non-code Q&A, apply principles without dumping skill contents.

## 16. Execution self-check

Before execution, verify:

- No raw PowerShell syntax is present in Bash.
- Bash-side paths are `/x/path`; Windows-side paths are `X:\path` or `X:/path`.
- No `/mnt/x/...` paths.
- MSYS2 path conversion will not corrupt native `.exe` arguments.
- Output is bounded or routed through context-mode indexed search.
- Non-ASCII paths use UTF-8 wrapper/manifest when crossing interpreter boundaries.
- Files are created/modified only with native Write/Edit tools.
- Git filename parsing uses `-z` when machine-read.

## 17. Response format

Default final response:

```text
Summary:
- action/result
- action/result

Files:
- path — purpose

Findings:
- key fact / risk / remaining uncertainty
```

Keep replies concise. Expand only for security risks, irreversible actions, user confusion, or complex tradeoffs.

## 18. Done criteria

Before claiming completion:

- Relevant evidence checked.
- Modified files listed.
- Remaining risk or uncertainty stated.
- No unrelated changes introduced.
