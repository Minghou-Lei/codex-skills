# AGENTS.md — Compact Operating Contract

Purpose: keep Codex fast, low-token, and safe on this Windows + context-mode setup.
Follow this file before repo-local habits unless the user explicitly overrides it.

## 0. Priority

1. Current user request.
2. Safety / irreversible-action checks.
3. This AGENTS.md.
4. Repo-local build/test rules.
5. Style preferences.

When blocked by missing tools, state the limitation and use the closest safe fallback.

## 1. Default loop

For every task:

1. Infer intent; do not ask unless required.
2. Inspect only the minimum needed files/logs.
3. Prefer small, reversible edits.
4. Verify with the cheapest meaningful test/check.
5. Report: changed files, commands run, result, remaining risk.

Do not dump raw logs, raw HTML, huge grep output, or full files into context.

## 2. context-mode routing — mandatory

Use context-mode for exploration and processing. Raw shell is only for small bounded commands.

### Prefer these tools

- `ctx_batch_execute(commands, queries)` — multiple repo/shell checks, indexed, summarized.
- `ctx_search(queries)` — follow-up questions over indexed output.
- `ctx_execute(language, code)` — parse/filter/count/transform; print only the answer.
- `ctx_execute_file(path, language, code)` — analyze a file without pasting it.
- `ctx_fetch_and_index(url, source)` then `ctx_search(...)` — web/docs without raw HTML.
- `ctx_index(content, source)` — store useful known content.

### Raw shell allowed only when bounded

Allowed examples:

```bash
git status --short
git diff --stat
rg -n -m 20 "Pattern" "/f/Repo/Path"
find "/f/Repo/Path" -maxdepth 2 -type f | head -50
```

If output may exceed ~20 lines, route through `ctx_batch_execute`, `ctx_execute`, `head`, `tail`, `rg -m`, or a parser script.

### Forbidden raw context flooding

Never run these directly into chat/context:

```text
curl ...
wget ...
node -e "fetch(...)"
python -c "requests.get(...)"
large rg/grep/find/dir/Get-ChildItem output
raw HTML/JSON/API responses
```

For URLs: `ctx_fetch_and_index` -> `ctx_search`.

## 3. Windows shell identity

This machine is Windows, but `ctx_execute(language: "shell")` and `ctx_batch_execute` run in Git Bash/MSYS2 unless PowerShell is explicitly invoked.

Path domains:

| Consumer | Path style |
|---|---|
| Git Bash/MSYS2 | `/f/Repo/Project` |
| PowerShell / Windows tools | `F:\Repo\Project` |
| WSL | not used here; never emit `/mnt/f/...` |

Rules:

- Do not assume CWD is repo root. Use absolute paths.
- Quote every path.
- Convert boundaries explicitly: `cygpath -w /f/Repo`, `cygpath -u 'F:\Repo'`.
- Use `-LiteralPath` in PowerShell for filesystem paths.

## 4. Command classification before execution

Classify every shell command:

### `BASH_SAFE`

Git Bash commands: `git`, `rg`, `grep`, `find`, `ls`, `mkdir`, `rm`, `mv`, `cp`, `cat`, `head`, `tail`, `python`, `node`, `npm`, `cmake`.

Rules: MSYS paths, quoted paths, bounded output.

### `POWERSHELL_REQUIRED`

Any command containing PowerShell syntax/cmdlets:

```text
Get-* Set-* New-* Remove-* Test-Path Resolve-Path Select-Object Where-Object
$env: $_ $PSVersionTable [System.IO.*]
```

Rules: never inline raw in bash. Write a temporary `.ps1`, then run `pwsh -File`.

### `WINDOWS_NATIVE_WITH_NON_ASCII_PATHS`

Windows tools/scripts that may receive Chinese/non-ASCII paths:

```text
python.exe pwsh.exe powershell.exe UnrealEditor.exe UnrealEditor-Cmd.exe
Unity.exe MSBuild.exe devenv.exe custom .exe import/export tools
```

Rules: prefer ASCII-only `.ps1` wrapper + UTF-8 JSON/TXT manifest. Verify paths on the consumer side.

### `AMBIGUOUS`

Mixed bash + PowerShell syntax. Stop and rewrite as `.sh`, `.ps1`, `.py`, or `.js`.

## 5. PowerShell from context-mode

Do not use complex `pwsh -Command` / `powershell -Command` one-liners.

Preferred launcher from Git Bash:

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w /tmp/task.ps1)"
```

Fallback:

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w /tmp/task.ps1)"
```

Required top of generated `.ps1` touching files/tools:

```powershell
$ErrorActionPreference = "Stop"
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

Keep generated `.ps1` ASCII-only when possible. Put Chinese paths in UTF-8 manifests, not shell one-liners.

## 6. Chinese / non-ASCII path hard rules

Git Bash/MSYS2 is UTF-8. Native Windows tools may use UTF-8, ANSI/GBK, UTF-16, or their own parser. Most Chinese-path bugs are boundary bugs.

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

- Valid: `F:\...\门派室内长歌门\JZ_cgm`
- Invalid as path: `F:\...\\u95E8\\u6D3E...\JZ_cgm`
- Corrupted: `F:\...\é—¨æ´¾...` or `????`

Never manually patch mojibake unless doing explicit data recovery. Regenerate from source.

### UTF-8 defaults for bash commands touching text/paths

```bash
export LANG=${LANG:-zh_CN.UTF-8}
export LC_CTYPE=${LC_CTYPE:-zh_CN.UTF-8}
export LESSCHARSET=utf-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

Never set `LC_ALL=C` for commands that may touch non-ASCII filenames/text.

### Git path output

Use per-command config when agents/scripts read paths:

```bash
git -c core.quotepath=false status --short
git -c core.quotepath=false diff --name-only
git -c core.quotepath=false ls-files
```

Only change global Git config if the user asks.

### Manifests for non-ASCII paths

Do not pass complex Chinese paths through shell quoting. Use UTF-8 JSON/TXT files.

Python JSON:

```python
Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
data = json.loads(Path(p).read_text(encoding="utf-8"))
```

Node JSON:

```javascript
fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf8");
const data = JSON.parse(fs.readFileSync(p, "utf8"));
```

### Consumer-side verification

Verify existence where the path will be consumed.

PowerShell / Windows tools:

```powershell
if (-not (Test-Path -LiteralPath $Path)) { throw "missing path: $Path" }
```

Python:

```python
if not Path(path).exists(): raise FileNotFoundError(path)
```

Do not rely on bash `test -e` for a path later consumed by PowerShell, Windows Python, Unreal, Unity, MSBuild, or a Windows `.exe`.

### Failure playbook: Chinese path `FileNotFoundError`

1. Capture exact path received by failing process.
2. Check for literal `\uXXXX`, `????`, mojibake, Git octal escapes.
3. Verify intended Windows path with PowerShell `Test-Path -LiteralPath`.
4. Check manifest/file encoding is UTF-8 and JSON uses `ensure_ascii=False`.
5. Rerun via `.ps1 + pwsh -File` with UTF-8 setup.
6. Only then inspect business logic or asset discovery.

## 7. Generated scripts

- `.bat` / `.cmd`: ASCII-only. No Chinese comments, echoes, or path literals.
- Prefer `.ps1`, `.py`, or `.js` for Windows automation.
- For filenames with spaces/non-ASCII, never use newline `find | xargs`; use `find ... -print0 | xargs -0 ...` or `rg`.
- Normal logs should print `str(path)`, not `repr(path)`. Use `repr` only as labeled diagnostics.

## 8. Code-task skill routing

For any code generation, modification, review, debugging, refactor, tests, scripts, shaders, build files, or automation:

1. Load `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`.
2. Load `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`.
3. Apply both; do not treat them as optional.

If a skill file is inaccessible, state it and continue with closest known rules.

For trivial non-code Q&A, apply principles without dumping skill contents.

## 9. Output contract

Be terse and evidence-based.

Final response format for work items:

```text
Changed:
- path: what changed

Checked:
- command/result

Notes/Risks:
- remaining issue or "none known"
```

Write long artifacts to files. Return the file path and one-line description.

## 10. Hard bans

Never:

- paste huge raw outputs into context
- run raw HTTP fetches into context
- run PowerShell cmdlets directly as bash
- emit WSL `/mnt/...` paths on this machine
- assume sandbox CWD is repo root
- pass literal `\uXXXX` paths to filesystem APIs
- pass Chinese paths through raw bash one-liners when wrapper + manifest is practical
- generate `.bat` / `.cmd` with Chinese text
- use default `json.dumps` for Unicode path manifests
- run Python touching Chinese paths without UTF-8 env
- set `LC_ALL=C` for non-ASCII work
- parse default Git escaped paths as real paths
- use newline `find | xargs` for non-ASCII/space filenames
- hide failed checks; report them

# Optional include

If supported by the current Codex environment, also load:

```text
@C:\Users\KSG\.codex\RTK.md
```
