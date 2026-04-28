# context-mode — MANDATORY routing rules

context-mode MCP tools are available. These rules protect the context window from raw-output flooding.
One unrouted command can dump tens of KB into the conversation.
Codex CLI hook/input-rewrite coverage may be limited, so this file is model-facing enforcement.
Follow strictly.

## Priority order

When rules conflict, use this order:

1. User's explicit current request.
2. Safety and irreversible-action checks.
3. context-mode routing rules in this file.
4. Windows shell boundary rules in this file.
5. Global skill routing rules in this file.
6. Style/output preferences.

If a rule cannot be followed because a tool/path/runtime is missing, state the limitation and use the closest safe fallback.

## Core principle: Think in Code — MANDATORY

For analyze/count/filter/compare/search/parse/transform tasks, write code via:

- `ctx_execute(language, code)`
- `ctx_execute_file(path, language, code)`

Only print the final answer or a small relevant excerpt.
Do not read raw data into chat.
Program the analysis; do not manually compute it in the conversation.

Pure JavaScript preference:

- Prefer Node.js built-ins only: `fs`, `path`, `child_process`, etc.
- Use `try/catch`.
- Handle `null` / `undefined`.
- One script should replace many raw tool calls.
- `console.log()` only the answer, not raw intermediate data.

## BLOCKED — do NOT use raw context-flooding commands

### `curl` / `wget` in shell — FORBIDDEN

Do not use `curl` / `wget` in shell for page/API fetching.
They can dump raw HTTP/HTML/JSON into context.

Use instead:

1. `ctx_fetch_and_index(url, source)`, then `ctx_search(queries)`; or
2. `ctx_execute(language: "javascript", code: "...")` only when the script fetches, parses, and prints a small summarized result.

### Inline HTTP in raw shell — FORBIDDEN

Do not run raw shell one-liners such as:

```text
node -e "fetch(...)"
python -c "requests.get(...)"
curl ...
wget ...
```

Boundary rule:

- Inline HTTP is forbidden in raw shell commands.
- `ctx_execute(language: "javascript" | "python")` may fetch only when stdout is deliberately small and summarized.
- For large pages, docs, JSON, or HTML, use `ctx_fetch_and_index` + `ctx_search`.

### Direct web fetching into chat — FORBIDDEN

Raw HTML can exceed 100 KB.
Never paste raw HTML/JSON into context.

Use:

1. `ctx_fetch_and_index(url, source)`
2. `ctx_search(queries)`

## REDIRECTED — use sandboxed processing

### Shell with large output

Shell is allowed only for small, bounded commands, such as:

- `git status --short`
- `git diff --stat`
- `mkdir`, `rm`, `mv`, `cp`
- `npm install`, `pip install`
- targeted `rg -n -m 20 "pattern" "path"`

If a shell command may produce more than about 20 lines, use one of:

- `ctx_batch_execute(commands, queries)` with targeted queries
- `ctx_execute(language: "javascript" | "python")` to parse/filter/summarize
- `ctx_execute(language: "shell", code: "...")` only when the command is bounded with `head`, `tail`, `rg -m`, `find ... | head`, or equivalent

Return only the relevant result, not the raw dump.

### File reading for analysis

Reading to edit is okay when exact content is needed.

Reading to analyze/explore/summarize should use:

- `ctx_execute_file(path, language, code)`

The script must extract exact facts needed and print only the answer.

### Grep/search with large results

For large grep/search output, do not dump raw matches into context.

Use:

- `ctx_batch_execute(commands, queries)` when multiple searches are needed
- `ctx_execute(language: "shell", code: "rg ... | head ...")` only when bounded
- `ctx_execute(language: "javascript" | "python")` when counting/grouping/filtering is needed

Filter, count, and summarize in the sandbox.

## Tool selection

1. **GATHER** — `ctx_batch_execute(commands, queries)`
   - Runs multiple shell commands.
   - Auto-indexes output.
   - Returns searched/summarized results.
   - One call replaces many raw command calls.
   - Each command shape: `{ label: "header", command: "..." }`.
   - Treat every command as Git Bash/MSYS2 on this Windows machine unless PowerShell is explicitly invoked.

2. **FOLLOW-UP** — `ctx_search(queries: ["q1", "q2", ...])`
   - Ask all follow-up questions in one array.
   - Use after gathered/indexed data exists.

3. **PROCESSING** — `ctx_execute(language, code)` / `ctx_execute_file(path, language, code)`
   - Sandbox execution.
   - Only stdout enters context.
   - Best for count/filter/parse/transform/compare.

4. **WEB** — `ctx_fetch_and_index(url, source)` then `ctx_search(queries)`
   - Raw HTML never enters context.
   - Search indexed content instead.

5. **INDEX** — `ctx_index(content, source)`
   - Store known content in FTS5 for later search.
   - Use descriptive source labels.

## Self-check before context-mode tool execution

Before any `ctx_execute(language: "shell")` or `ctx_batch_execute` call, verify:

1. No raw PowerShell syntax appears unless wrapped through temporary `.ps1` + `pwsh -File`.
2. Bash-side paths use `/x/path`, not `X:\path` and not `/mnt/x/path`.
3. PowerShell-side paths use `X:\path`, preferably with `-LiteralPath`.
4. Any command that may exceed 20 lines is bounded, summarized, or routed through `ctx_batch_execute` with queries.
5. The command does not rely on the sandbox CWD being the repo root.
6. Paths containing spaces are quoted.
7. Destructive commands are scoped and reversible where possible.

If any check fails, rewrite before execution.

## Output style

Terse. Technical substance exact.
Drop filler, pleasantries, hedging.
Fragments okay.
Short synonyms.
Code unchanged unless user requests changes.

Pattern:

```text
[thing] [action] [reason]. [next step].
```

Auto-expand only for:

- security warnings
- irreversible actions
- user confusion
- non-obvious tradeoffs

Write long artifacts to files instead of inlining them.
Return:

- file path
- one-line description

Use descriptive source labels for indexed/searchable content.

## ctx commands

| Command | Action |
|---|---|
| `ctx stats` | Call `stats` MCP tool, display full output verbatim. |
| `ctx doctor` | Call `doctor` MCP tool, run returned shell command, display as checklist. |
| `ctx upgrade` | Call `upgrade` MCP tool, run returned shell command, display as checklist. |
| `ctx purge` | Call `purge` MCP tool with `confirm: true`. Warn before wiping knowledge base. |

After `/clear` or `/compact`:

- knowledge base and session stats are preserved
- use `ctx purge` only when a fresh knowledge base is intended

# Windows notes — Codex + context-mode

## Shell identity

This machine is Windows, but context-mode `language: "shell"` runs through Git Bash / MSYS2 on this machine.
Do not rely on fallback PowerShell.
Treat every `ctx_execute(language: "shell")` and `ctx_batch_execute` command as bash unless PowerShell is explicitly invoked.

Important implication:

- Windows terminal may be PowerShell.
- context-mode shell is Git Bash/MSYS2.
- These are different execution layers.

## Command classification required

Before running shell code, classify the command as one of:

### 1. `BASH_SAFE`

Safe in Git Bash / MSYS2:

```text
git, rg, grep, find, ls, mkdir, rm, mv, cp, cat, head, tail,
python, python3, node, npm, bun, cmake, native .exe tools
```

Rules:

- Use MSYS path style on the bash side.
- Example: `F:\Repo\Project` -> `/f/Repo/Project`.
- Quote paths.
- Bound output.

### 2. `POWERSHELL_REQUIRED`

Any command containing PowerShell cmdlets, variables, or syntax:

```text
Get-*, Set-*, New-*, Remove-*, Test-Path, Resolve-Path,
Format-*, Select-Object, Where-Object, ForEach-Object,
$env:, $_, $PSVersionTable, [System.IO.*]
```

Rules:

- These must never appear raw in bash commands.
- Use a temporary `.ps1` file and run it through `pwsh -File`.
- Use `powershell.exe` only as fallback when `pwsh` is unavailable.

### 3. `AMBIGUOUS`

Mixed bash + PowerShell syntax.

Rules:

- Stop and rewrite before execution.
- Prefer `.ps1` for PowerShell logic.
- Prefer `.sh` / plain bash for bash logic.
- Do not attempt to make a hybrid one-liner.

## PowerShell policy from context-mode

For any PowerShell logic, do **not** inline complex `pwsh -Command` strings.

Instead:

1. Write a temporary `.ps1` file.
2. Run it from bash using `pwsh -File`.
3. Convert the script path with `cygpath -w` when invoking from Git Bash.

Preferred invocation:

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w /tmp/task.ps1)"
```

Fallback invocation:

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w /tmp/task.ps1)"
```

## Preferred PowerShell pattern

Use this pattern from `ctx_execute(language: "shell")` or `ctx_batch_execute`:

```bash
cat > /tmp/task.ps1 <<'PS1'
$ErrorActionPreference = "Stop"
Get-ChildItem -LiteralPath "C:\Users\KSG" | Select-Object -First 5 Name
PS1

pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w /tmp/task.ps1)"
```

For repo-specific scripts, prefer a temporary file under the repo or `%TEMP%` only when persistence/debugging is useful.
Otherwise use `/tmp/task.ps1`.

## Do not mix syntaxes

PowerShell-only syntax must not appear raw in bash:

```text
$env:VAR
$_
| Select-Object
| Where-Object
[System.IO.Path]
Test-Path
Resolve-Path
Get-ChildItem
Format-List
```

Bash-style syntax should not be placed inside PowerShell unless intentionally rewritten:

```text
export VAR=...
VAR=value cmd
2>/dev/null
$(pwd)
/c/Users/...
/f/Repo/...
```

## Relative paths

Sandbox CWD is a temp directory, not necessarily the project root.
Convert user-supplied paths to absolute paths before using `rg`, `grep`, `find`, or scripts.
Ask the user to confirm the absolute path only if it cannot be inferred from the task or known workspace.

## Windows drive letters

Sandbox runs Git Bash / MSYS2, not WSL.
Use MSYS2 path style:

```text
X:\path -> /x/path
F:\JX3QJ\Sword3 -> /f/JX3QJ/Sword3
C:\Users\KSG -> /c/Users/KSG
```

Never emit WSL paths for this machine:

```text
/mnt/c/...
/mnt/f/...
```

## Path boundary rule

Use the right path syntax for the current interpreter:

| Side | Path style |
|---|---|
| Bash / Git Bash / MSYS2 | `/f/Repo/Project` |
| PowerShell / Windows tools | `F:\Repo\Project` |

When crossing the boundary, convert explicitly:

```bash
cygpath -w /f/Repo/Project
cygpath -u 'F:\Repo\Project'
```

If `cygpath` is unavailable, manually convert and quote paths.

## Quote paths

Spaces in paths cause argument splitting.
Always double-quote paths in bash:

```bash
rg "symbol" "$REPO_ROOT/some dir/Source"
```

Inside PowerShell, prefer `-LiteralPath` for filesystem paths:

```powershell
Get-ChildItem -LiteralPath "F:\Some Dir\Project"
```

## Chinese Windows / encoding

Avoid non-ASCII text in `.bat` / `.cmd` scripts.
Prefer `.ps1`, `.js`, `.py`, or UTF-8 text files.
For generated scripts, explicitly choose encoding.
Do not rely on the Windows system code page.

For `.ps1` generated from PowerShell, prefer UTF-8:

```powershell
Set-Content -Encoding utf8 -LiteralPath "script.ps1" -Value $content
```

For files generated from bash here-docs, keep script bodies ASCII unless Chinese output is required.

## Preferred execution pattern on Windows

Use this priority:

1. `ctx_execute(language: "javascript" | "python")` for analyze/count/filter/parse/transform tasks.
2. `ctx_batch_execute` for multiple bounded Git Bash commands with indexed search.
3. `ctx_execute(language: "shell")` for small bounded Git Bash commands.
4. Temporary `.ps1` + `pwsh -File` for PowerShell-required logic.
5. Avoid complex `pwsh -Command` one-liners.

## Hard bans on this machine

Do not:

- run raw PowerShell cmdlets directly in `language: "shell"`
- put `Get-*`, `Test-Path`, `$env:`, `Select-Object`, or `[System.IO.*]` raw inside bash commands
- mix `/mnt/<drive>/...` paths with Git Bash/MSYS2 paths
- assume current directory is the repository root
- emit large raw `rg`, `grep`, `find`, `dir`, or `Get-ChildItem` output into context
- write generated `.bat` / `.cmd` files containing Chinese text
- create hybrid bash/PowerShell one-liners when a temporary script would be clearer

# Global Skill Routing

## Mandatory routing

For any task that writes, modifies, reviews, refactors, explains, or generates code, the agent must load and follow these skills from the global Codex skill directory:

1. `C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md`
2. `C:\Users\KSG\.codex\skills\code-comment\SKILL.md`

This is mandatory routing, not a recommendation.

## Routing rules

- `karpathy-guidelines` is required for any coding, debugging, patching, refactoring, code review, or implementation task.
- `code-comment` is required for any task that outputs, creates, modifies, rewrites, reviews, or documents code, including APIs, tests, scripts, patches, docstrings, inline comments, shaders, and build or automation scripts.
- The agent must not skip `code-comment` just because the user did not explicitly ask for comments; it must at least execute the skill's signal-tier scan, apply the file-header strategy when applicable, and perform the output self-check.
- If both skills apply, both must be used in this order:
  1. `karpathy-guidelines`
  2. `code-comment`

## Enforcement

- Treat any code-related request as matching both skills unless there is a clear, concrete reason that one does not apply.
- If there is any ambiguity, default to loading both skills.
- Do not present either skill as optional on code-related turns.
- If a required skill file is inaccessible, state that fact, continue with the closest matching rules already known, and do not silently ignore the missing skill.

## Lightweight exception

For trivial non-code conceptual Q&A or one-line command explanation, do not dump full skill content into context.
Still apply the relevant principles mentally.

# Extra routing file

If the current Codex environment supports include/import syntax, also load:

`C:\Users\KSG\.codex\RTK.md`

If include/import syntax is not supported, treat the line below as an operator note and continue with this AGENTS.md.

@C:\Users\KSG\.codex\RTK.md