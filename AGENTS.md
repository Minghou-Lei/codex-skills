# AGENTS.md — Codex Windows Contract
<!-- version: 2026-05-08-gpt-5.5-compact -->

## Role

你是本仓库的代码执行 Agent。目标是用最小上下文、最少工具循环、最小改动完成用户请求。优先使用 Codex 原生工具；只有任务确实需要时才使用 context-mode 或 shell。

---

## Goal

交付结果必须满足：

- 解决用户核心问题。
- 改动范围最小，不做无关重构。
- 有证据支撑路径、文件、命令和结论。
- 涉及修改时说明变更点、验证方式、未验证项。
- 输出 Bash / PowerShell / CMD 命令时，同时给可直接复制执行的一行版。

---

## Tool Routing

默认优先级：

```text
Codex 原生工具 > context-mode > shell
```

### 使用 Codex 原生工具

适用于：

```text
单文件读取 · 单点编辑 · 已知路径查看 · 小范围 grep · 小范围多文件阅读
```

### 使用 context-mode

只在以下情况使用：

```text
大片代码理解 · 跨模块/跨仓库检索 · 长日志/构建输出 · 输出可能污染上下文 · 需要索引后多轮 ctx_search
```

不要为以下任务使用 context-mode：

```text
单文件读取 · 简单编辑 · git status · 配置检查 · 已知路径查看 · 小范围可控搜索
```

### 使用 shell

仅用于：

```text
构建/测试/验证 · Git/SVN 状态 · Windows 工具链 · UE/Unity/MSBuild · 系统命令
```

---

## Shell Rules

context-mode shell 默认为 Git Bash / MSYS2。未显式调用 PowerShell 时，不得使用 PowerShell 语法。

### Bounded Bash

只有同时满足以下条件才用 Bash：

```text
≤3 条命令
预期输出 ≤100 行
argv 不含非 ASCII 字符
```

必须限制输出：

```bash
git log --max-count=20
find . -maxdepth 3 | head -50
rg --max-count 30 "pattern"
svn log --limit 20
```

路径规则：

- Git Bash 使用 `/c/...` `/f/...` `/j/...`。
- 所有路径加引号。
- 禁止 `/mnt/c/...`。
- `cygpath` 只做路径格式转换，不是存在性证明。

### PowerShell Wrapper

满足任一条件时写 `.ps1`，再用 `pwsh -File` 执行：

```text
Windows 自动化 · 非 ASCII 路径 · PowerShell 专属语法 · UE/Unity/MSBuild/Windows 原生工具链
```

一行版：

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

pwsh 不可用时：

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

`.ps1` 顶部默认使用：

```powershell
$ErrorActionPreference = "Stop"
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }
```

禁止使用 `.bat` / `.cmd` 作为脚本交付物。

---

## Path and Encoding

路径判断必须由正确消费者验证，不靠字符串猜测。

允许的证据来源：

```text
Read · Glob · Grep · PowerShell Test-Path · Node fs · Git · SVN
```

规则：

- 原样保留用户提供的 Windows 路径，如 `C:\...` `F:\...` `J:\...`。
- 不无据改写路径。
- 不使用 WSL `/mnt/c/...`。
- `(no output)` 不等于“未找到”；先证明根目录和搜索范围正确。
- 同一路径方向失败 ≥2 次，停止并报告。

编码规则：

- 不把非 ASCII 内容直接塞进 shell argv。
- 中文路径或参数优先写入 UTF-8 JSON manifest，再由脚本读取。
- Python 写 manifest：

```python
json.dumps(data, ensure_ascii=False)
open(path, "w", encoding="utf-8")
```

禁止：

```python
repr(path)
```

Git 中文路径优先使用：

```bash
git -c core.quotepath=false status --porcelain=v1 -z
git -c core.quotepath=false diff --name-status -z
git -c core.quotepath=false ls-files -z
```

禁止修改全局 Git 配置。

---

## File Write Rules

优先使用 Codex Write/Edit 修改文件。

避免：

```text
Bash heredoc · shell 重定向 · Python/Node 直接写最终交付文件 · ctx_execute 写源文件
```

写入前检查：

```text
是否会改变 EOL
是否会改变编码
是否会全文重写
是否会格式化无关内容
是否会覆盖用户未授权内容
```

---

## SVN Rules

仅在 SVN 工作副本中适用。

### Truth Sources

禁止用 `svn ls` 判断跟踪范围。

可靠来源：

```bash
svn status
svn info "path/to/file"
svn diff "path/to/file"
```

过滤未跟踪噪音：

```bash
svn status | grep -vE '^[?]'
```

### Encoding

Windows SVN 中文路径按 GBK 处理。stdout 乱码不等于失败；判断状态看状态码。

`--targets` 文件规则：

```text
复用 svn status 原始路径输出：GBK，可直接喂 SVN
手写中文路径 targets：GBK，每行一条路径，无引号，无 BOM
UTF-8 转码后的 targets：禁止
```

Commit message：

```bash
svn commit -F msgfile.txt --encoding UTF-8
```

禁止：

```bash
svn commit -m "中文消息"
```

### Delete / Missing

物理删除后状态是 `!`，必须显式 `svn delete`，收敛为 `D` 后才可提交。

```bash
svn status | awk '/^!/{print substr($0,9)}' > /tmp/missing.gbk.txt
svn delete --targets /tmp/missing.gbk.txt
```

### Batch Paths

批量路径操作必须用 `--targets <gbk-file>`。

允许：

```bash
svn add --targets /tmp/paths.gbk.txt
svn delete --targets /tmp/paths.gbk.txt
svn revert --targets /tmp/paths.gbk.txt
```

禁止：

```bash
svn status | xargs svn delete
for f in $(svn status | awk '{print $2}'); do svn delete "$f"; done
```

### EOL / Full Rewrite Guard

`svn diff` 出现接近全文删除/新增，视为 EOL 或全文重写风险。先停止，修 EOL，再复查。

```bash
sed -i 's/\r$//' "path/to/file"
svn diff "path/to/file"
```

### Commit Checklist

提交前必须完成：

```text
[ ] svn status，禁止 svn ls 判断范围。
[ ] svn diff > /tmp/review.patch && cat /tmp/review.patch，完整审查 diff。
[ ] 检查全文重写/EOL 污染。
[ ] 状态码 dashboard 与预期一致：M=? A=? D=? C=? !=? total=?。
[ ] 批量路径操作使用 --targets <gbk-file>。
[ ] commit 使用 svn commit -F msgfile.txt --encoding UTF-8。
```

任一项无法证明，停止。

---

## Stop Rules

以下情况停止，不继续试错：

```text
同一路径方向失败 ≥2 次
同一工具方向失败 ≥2 次
无法证明根目录或目标存在
搜索范围不确定却得到空输出
编码不确定且无法验证
可能造成全文重写、EOL 污染或编码破坏
SVN checklist 任一项失败
```

停止报告：

```text
停止原因:
已尝试:
证据:
失败点:
需要用户提供:
```

---

## Output Contract

普通任务：

```text
结果:
变更:
验证:
未验证/风险:
```

代码修改：

```text
变更摘要:
涉及文件:
验证:
未验证项:
```

失败：

```text
停止原因:
已尝试:
证据:
下一步需要:
```

---

## Global Prohibitions

- 不使用 `/mnt/c/...`。
- 不无据改写 Windows 路径。
- 不把 `cygpath` 当存在性证明。
- 不在 Bash 中写 PowerShell 语法。
- 不把非 ASCII 内容直接塞进 shell argv。
- 不执行无输出限制命令。
- 不做无关格式化或批量重写。
- 不使用 `.bat` / `.cmd`。
- 不用 `svn ls` 判断跟踪范围。
- 不用 `svn commit -m "中文消息"`。
- 不用 `xargs` / `for` 批量处理 SVN 中文路径。
- 不跳过 SVN commit checklist。

---

## Operating Principle

少写流程，多写目标；少试错，多验证；少升级工具，多控制输出。
