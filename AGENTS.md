# AGENTS.md — Local Windows Execution Contract

Purpose: supplement the session `context_window_protection` hook with local Windows rules only.
Do not duplicate hook rules. Apply both; the stricter rule wins.

## 0. Priority

1. Current user request.
2. Safety / irreversible-action checks.
3. Session hook: `context_window_protection`.
4. This local AGENTS.md.
5. Repo-local build/test rules.

This file mainly covers: Windows shell identity, path domains, Unicode paths, PowerShell wrappers, and skill routing.

## 1. Local machine facts

- OS: Windows.
- context-mode `language: "shell"` and `ctx_batch_execute` commands run as Git Bash / MSYS2 unless PowerShell is explicitly invoked.
- Native Windows tools consume Windows paths: `F:\Repo\Project`.
- Git Bash consumes MSYS paths: `/f/Repo/Project`.
- WSL is not used here. Never emit `/mnt/c/...` or `/mnt/f/...`.

## 2. Command preflight — mandatory

Before any shell command, classify it:

### `BASH_SAFE_SMALL`

Allowed only for small, bounded Git Bash work permitted by the hook.
Examples: `git`, `rg -m`, `find ... | head`, `mkdir`, `rm`, `mv`, navigation.

Rules:
- Use MSYS paths: `/c/...`, `/f/...`, `/j/...`.
- Quote every path.
- Bound output before execution.
- Do not pass complex Chinese/non-ASCII paths through raw shell argv when a manifest/wrapper is practical.

### `POWERSHELL_REQUIRED`

Any command containing PowerShell cmdlets or syntax:

```text
Get-* Set-* New-* Remove-* Test-Path Resolve-Path
Select-Object Where-Object ForEach-Object Format-*
$env: $_ $PSVersionTable [System.IO.*]
```

Rules:
- Must not appear raw in bash.
- Use a `.ps1` wrapper.
- Create/edit the `.ps1` with native Write/Edit tools, not bash heredoc or `ctx_execute`.
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
- Do not trust a bash `test -e` result for a path later used by Windows Python, Unreal, Unity, MSBuild, or a Windows `.exe`.

### `AMBIGUOUS`

Mixed bash + PowerShell syntax, mixed path styles, or unclear interpreter.
Stop and rewrite as `.ps1`, `.py`, `.js`, or small bash.

## 3. Path domains

| Consumer | Path style |
|---|---|
| Git Bash / MSYS2 | `/f/Repo/Project` |
| PowerShell / Windows tools | `F:\Repo\Project` |
| WSL | not used; never `/mnt/f/...` |

Rules:
- Do not assume CWD is repo root. Use absolute paths.
- Use `cygpath -w /f/Repo` when passing a bash path to Windows tools.
- Use `cygpath -u 'F:\Repo'` when passing a Windows path to bash.
- Use `-LiteralPath` in PowerShell for filesystem paths.
- Quote all paths.

## 4. PowerShell wrapper policy

Do not use complex `pwsh -Command` / `powershell -Command` one-liners.

Use this pattern:

1. Create a temporary `.ps1` using native Write/Edit tools.
2. Keep the `.ps1` ASCII-only when possible.
3. Put Chinese/non-ASCII paths in a UTF-8 manifest file.
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

## 5. Unicode / Chinese path hard rules

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

For bash commands touching text or filenames:

```bash
export LANG=${LANG:-zh_CN.UTF-8}
export LC_CTYPE=${LC_CTYPE:-zh_CN.UTF-8}
export LESSCHARSET=utf-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

Never set `LC_ALL=C` for non-ASCII work.

### Git path output

When scripts/agents read Git paths:

```bash
git -c core.quotepath=false status --short
git -c core.quotepath=false diff --name-only
git -c core.quotepath=false ls-files
```

Do not change global Git config unless the user asks.

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

## 6. Chinese path `FileNotFoundError` playbook

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

## 7. File creation / modification reminder

The hook owns the main write policy. Local extension:

- Use native Write/Edit tools for generated wrappers, manifests, configs, source, markdown, JSON, YAML, and scripts.
- Do not create files via bash heredoc, `ctx_execute`, Python writes, or Node writes unless the user explicitly asks for that execution path.
- Avoid `.bat` / `.cmd` for Chinese Windows automation.
- If `.bat` / `.cmd` is unavoidable, keep it ASCII-only.
- Prefer `.ps1`, `.py`, `.js`, or UTF-8 text files.

## 8. Code-task skill routing

For any code generation, modification, review, debugging, refactor, tests, scripts, shaders, build files, or automation:

1. Load `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`.
2. Load `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`.
3. Apply both; do not treat them as optional.

If a skill file is inaccessible, state it and continue with the closest known rules.
For trivial non-code Q&A, apply principles without dumping skill contents.

## 9. Execution self-check

Before execution, verify:

- No raw PowerShell syntax is present in bash.
- Bash-side paths are `/x/path`; Windows-side paths are `X:\path`.
- No `/mnt/x/...` paths.
- Output is bounded or routed through context-mode indexed search.
- Non-ASCII paths use UTF-8 wrapper/manifest when crossing interpreter boundaries.
- Files are created/modified only with native Write/Edit tools.
- Failed checks are reported, not hidden.

## 10. Optional include

If supported by the current Codex environment, also load:

```text
@C:\Users\KSG\.codex\RTK.md
```

If include syntax is unsupported, treat the line as an operator note and continue with this file.
