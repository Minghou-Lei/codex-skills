# Windows CN Local Contract

Purpose: supplement the session hook. The hook owns context-mode routing and write-policy details. This file only fixes persistent local mistakes on Windows 11 Chinese environments.

## Priority

1. User request
2. Safety / irreversible checks
3. Session hook: `context_window_protection`
4. This file
5. Repo-local build/test rules

Stricter rule wins.

## Machine facts

- OS: Windows 11, Chinese-capable filesystem/user environment.
- context-mode `shell` commands run as Git Bash / MSYS2 by default.
- Git Bash paths: `/c/...`, `/f/...`, `/j/...`.
- Windows native paths: `C:\...`, `F:\...`, `J:\...`.
- WSL is not used. Never emit `/mnt/c/...`, `/mnt/f/...`, `/mnt/j/...`.

## Command preflight

Before running any command, classify it.

### `BASH_SAFE_SMALL`

Use only for small bounded Git Bash work: `git`, `rg -m`, `find ... | head`, `mkdir`, `rm`, `mv`, navigation.

Rules:

- Use `/x/path` paths.
- Quote every path.
- Bound output.
- Do not pass complex Chinese paths through raw argv when a manifest/wrapper is practical.

### `POWERSHELL_REQUIRED`

Any use of PowerShell cmdlets/syntax requires a `.ps1` wrapper:

- `Get-*`, `Set-*`, `New-*`, `Remove-*`, `Test-Path`, `Resolve-Path`
- `Select-Object`, `Where-Object`, `ForEach-Object`, `Format-*`
- `$env:`, `$_`, `$PSVersionTable`, `[System.IO.*]`

Rules:

- Never run PowerShell syntax directly in Git Bash.
- Create/edit `.ps1` with native Write/Edit tools.
- Run via `pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File`.
- Use `powershell.exe -File` only if `pwsh` is unavailable, and keep scripts encoding-safe.

### `WINDOWS_NATIVE_WITH_NON_ASCII_PATHS`

For Windows tools receiving Chinese/non-ASCII paths, prefer `.ps1` wrapper + UTF-8 JSON/TXT manifest:

- `python.exe`, `pwsh.exe`, `powershell.exe`
- `UnrealEditor.exe`, `UnrealEditor-Cmd.exe`, `Unity.exe`
- `MSBuild.exe`, `devenv.exe`, custom `.exe` tools

Do not trust Bash `test -e` for a path later consumed by a Windows-native process. Verify in the consumer environment.

### `AMBIGUOUS`

Mixed Bash + PowerShell syntax, mixed path styles, or unclear interpreter: stop and rewrite as `.ps1`, `.py`, `.js`, or small Bash.

## Actual path re-grounding

If a lookup missed the real directory, stop searching from CWD.

Re-anchor first:

1. Identify path domain: Windows `C:\...`, Git Bash `/c/...`, or proven repo-relative path.
2. Verify the absolute parent directory exists.
3. Search only inside the verified root.
4. Do not claim `not found` until that verified absolute root was searched.
5. Never run PowerShell syntax directly in Git Bash; use `.ps1 + pwsh -File`.

Avoid: relative guess -> not found -> another relative guess.  
Use: expected absolute root -> verify root -> search inside root.

## Path conversion

- Bash -> Windows: `cygpath -w '/f/Repo'`
- Windows -> Bash: `cygpath -u 'F:\Repo'`
- PowerShell filesystem paths: use `-LiteralPath`.
- Always quote paths.
- Do not assume CWD is repo root. Prove repo root or use absolute paths.

## MSYS2 argv/path conversion pitfalls

When Git Bash calls native Windows programs, MSYS2 may auto-convert Unix-looking args into Windows paths.

High-risk literals:

- `/c`, `/C`, `/sdcard`, `/data`, `/tmp`
- `--root=/`, `--mount=/x/y`, Docker/ADB/WSL-like args
- Any native `.exe` that expects Unix-style switches or literal slash paths

If needed, disable conversion locally:

```bash
MSYS2_ARG_CONV_EXCL='*' native.exe /literal/switch --root=/
```

Do not set this globally.

## PowerShell wrapper template

Run from Git Bash/context-mode shell:

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

Recommended `.ps1` header for file/tool work:

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

Avoid complex `pwsh -Command` / `powershell -Command` one-liners.

## Chinese path / Unicode rules

Treat Chinese-path failures as boundary/encoding bugs first.

Bad signs:

- Literal `\uXXXX` inside paths: escaped text reused as a path.
- `????`: lossy codepage conversion.
- `é—¨æ´¾`-style text: UTF-8/GBK mojibake.
- Git octal/quoted paths: Git path escaping.
- False `FileNotFoundError` on known Chinese path: verify in consumer environment.

Keep representations separate:

- Valid: `F:\...\门派室内长歌门\JZ_cgm`
- Invalid path text: `F:\...\\u95E8\\u6D3E...\JZ_cgm`
- Corrupt path text: `F:\...\é—¨æ´¾...` or `????`

Do not manually patch mojibake unless explicitly doing data recovery. Regenerate from the original Unicode source.

## Git path output

For human display:

```bash
git -c core.quotepath=false status --short
git -c core.quotepath=false diff --name-only
git -c core.quotepath=false ls-files
```

For script parsing, prefer NUL output:

```bash
git -c core.quotepath=false status --porcelain=v1 -z
git -c core.quotepath=false diff --name-only -z
git -c core.quotepath=false ls-files -z
```

Do not change global Git config unless the user asks.

## Non-ASCII path manifests

Do not pass complex Chinese paths through shell quoting if a manifest is practical. Use UTF-8 JSON/TXT.

Python JSON rule:

```python
Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
data = json.loads(Path(p).read_text(encoding="utf-8"))
```

Node JSON rule:

```javascript
fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf8");
const data = JSON.parse(fs.readFileSync(p, "utf8"));
```

Diagnostics: print `str(path)` normally. Use `repr(path)` only when labeled as encoding diagnostics.

## Chinese `FileNotFoundError` playbook

When a known Chinese/non-ASCII path is reported missing:

1. Capture the exact path received by the failing process.
2. Check for `\uXXXX`, `????`, mojibake, Git escaping.
3. Verify with PowerShell `Test-Path -LiteralPath` inside a `.ps1` wrapper.
4. Check manifest encoding is UTF-8 and JSON used `ensure_ascii=False`.
5. Rerun through `.ps1 + pwsh -File` with UTF-8 header.
6. Only then inspect business logic.

## File edits

The hook owns the detailed write policy. Local reminder:

- Use native Write/Edit tools for code, configs, markdown, JSON, YAML, manifests, and wrappers.
- Do not create/modify files with Bash heredoc or ad-hoc script writes unless the user explicitly asks.
- Avoid `.bat` / `.cmd` for Chinese Windows automation. Prefer `.ps1`, `.py`, `.js`.

## Skill routing

For code generation, modification, review, debugging, refactor, tests, scripts, shaders, build files, or automation:

1. Load `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`.
2. Load `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`.
3. Apply both.

If unavailable, state that and continue with closest known rules. Do not dump skill contents for trivial Q&A.

## Execution self-check

Before claiming done, verify:

- No raw PowerShell syntax in Git Bash.
- Bash paths are `/x/path`; Windows paths are `X:\path`.
- No `/mnt/x/...` paths.
- Actual root was verified before searching after a miss.
- Output is bounded or routed through context-mode.
- Non-ASCII paths crossing interpreters use UTF-8 wrapper/manifest.
- File edits used native Write/Edit tools.
- Failed checks are reported, not hidden.

## Optional include

If supported by the current Codex environment, also load:

```text
@C:\Users\KSG\.codex\RTK.md
```

If include syntax is unsupported, treat it as an operator note and continue.
