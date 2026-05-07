# AGENTS.md — Codex Windows Contract

默认使用 Codex 原生工具：`Read` / `Edit` / `Write` / `Grep` / `Glob`。  
只有在满足明确条件时，才使用 `shell` 或 `context-mode`。

响应保持简短。  
失败不得反复猜测；同一路径或同一方向失败 ≥2 次后，必须停止并报告已尝试内容。

---

## 0. 总体工具选择原则

### 默认优先级

1. **优先使用 Codex 原生工具**
   - `Read`
   - `Edit`
   - `Write`
   - `Grep`
   - `Glob`

2. **只有满足 §2 条件时，才使用 context-mode**

3. **只有原生工具不适合时，才使用 shell**

---

## 1. 工具决策树

```text
任务开始
  │
  ├─ 是否满足任意 context-mode 触发条件？（见 §2）
  │    └─ YES → 使用 context-mode MCP
  │
  ├─ NO：是否必须使用 shell？
  │    ├─ NO  → 使用 Read / Edit / Write / Grep / Glob
  │    └─ YES → 是否涉及 Windows 自动化 / 非 ASCII 路径 / PowerShell 语法？
  │               ├─ YES → 使用 .ps1 + pwsh -File（见 §5）
  │               └─ NO  → 允许小型 Bash（必须满足 bounded Bash，见 §4）
  │
  └─ 任意路径或工具方向失败 ≥2 次
       → 停止，报告已尝试内容，等待用户指示
```

---

## 2. context-mode 使用边界

context-mode 只在明确适合“大范围读取、索引、搜索、汇总”时使用。

### 2.1 允许触发 context-mode 的条件

满足以下任意一项即可使用：

- 需要读取或汇总多个文件
- 需要跨仓库 / 跨模块理解代码
- 需要对已索引材料进行多轮 follow-up 搜索
- 原始命令输出可能溢出 chat context
- 大型日志 / 构建输出需要索引后搜索
- 用户明确要求使用：
  - `ctx_search`
  - `ctx_stats`
  - `ctx_doctor`
  - 其他 context-mode 相关能力

### 2.2 禁止触发 context-mode 的场景

以下场景不得使用 context-mode：

- 单文件读取
- 小型编辑
- 简单 grep
- `git status`
- 配置检查
- 已知路径查看
- 小范围、可控输出的本地查询

### 2.3 context-mode 子命令选择

| 场景 | 使用命令 |
|---|---|
| 初次索引、多命令并行探索 | `ctx_batch_execute`，必须附带 label |
| 已知目标的单条后续操作 | `ctx_execute` / `ctx_execute_file` |
| 索引后跨文件搜索 | `ctx_search` |

---

## 3. Windows 路径规则

### 3.1 Windows 路径必须原样保留

```text
C:\...
F:\...
J:\...
```

不得无依据改写为其他路径形式。

### 3.2 小型已知路径

对于小型、明确、已知路径，优先使用：

- `Read`
- `Glob`
- `Grep`

### 3.3 大规模路径发现

如果是在 Windows 路径下进行大规模发现，允许使用 context-mode。  
此时应使用 JS `fs/path` 探测路径，不得依赖 Git Bash 路径猜测。

### 3.4 `cygpath` 限制

`cygpath` 只能证明路径字符串转换成功。  
它不能证明文件或目录真实存在。

### 3.5 路径验证必须提供显式证据

验证路径时，必须说明实际消费者和验证结果：

```json
{
  "consumer": "Read|Glob|Grep|PowerShell|Node fs",
  "root": "...",
  "rootExists": true,
  "target": "...",
  "targetExists": true,
  "type": "file|directory|missing"
}
```

### 3.6 `(no output)` 不等于“未找到”

只有在正确消费者、正确根目录、正确路径域下完成搜索后，才允许判断“未找到”。

### 3.7 路径 lookup 失败时的重定位流程

路径查找失败时，按以下顺序处理：

1. 确认路径域：
   - Windows-native：`X:\path`
   - Git Bash：`/x/path`
   - 仓库相对路径：必须先证明仓库根目录

2. 验证绝对父目录是否存在

3. 只在已验证的根目录内搜索

4. 不得使用 WSL 路径：

```text
/mnt/c/...
```

### 3.8 路径重定位停止条件

同一路径重定位失败 ≥2 次后，必须停止。

停止时报告：

- 已尝试的路径
- 使用过的消费者
- 每次失败的现象
- 下一步需要用户确认的信息

禁止继续猜测。

---

## 4. Shell 使用规则

context-mode shell 默认是 Git Bash / MSYS2。  
除非显式调用 PowerShell，否则不得把 shell 当作 PowerShell 使用。

### 4.1 bounded Bash 定义

只有同时满足以下三条，才允许使用 Bash：

```text
≤3 条命令
预期输出 ≤100 行
argv 不包含非 ASCII 字符
```

任何一条不满足，都必须改用：

- `.ps1`
- 或 context-mode

### 4.2 Bash 中禁止直接运行 PowerShell 语法

禁止在 Bash 中直接使用：

```text
Get-* 
Set-* 
New-* 
Remove-* 
Test-Path 
Resolve-Path
Select-Object
Where-Object
ForEach-Object
Format-*
$env:
$_
$PSVersionTable
[System.*]
```

### 4.3 shell 命令必须限制输出

执行任何 shell 命令前，必须添加输出限制。

示例：

```bash
git log --max-count=20
find ... -maxdepth 3 | head -50
grep -m 30 ...
rg --max-count 30 ...
```

没有输出限制的命令不得执行。

### 4.4 Bash 允许范围

Bash 仅限以下场景：

```text
git status / diff / log
mkdir / rm / mv
navigation
bounded ASCII-safe grep / rg
```

前提：根目录已经被证明存在。

### 4.5 Bash 路径规则

Bash 内路径使用：

```text
/c/...
/f/...
/j/...
```

要求：

- 所有路径必须加引号
- 避免 argv 中出现中文或其他非 ASCII 字符
- 不得使用 WSL 路径

### 4.6 MSYS2 路径转换排除

仅在必要时单次使用：

```bash
MSYS2_ARG_CONV_EXCL='*' native.exe --literal=/foo
```

不得全局设置。

---

## 5. PowerShell Wrapper 规则

涉及 Windows 自动化、非 ASCII 路径、PowerShell 语法、Windows 工具链时，必须使用 `.ps1` wrapper。

### 5.1 创建方式

使用 Codex 原生工具创建脚本：

- `Write`
- `Edit`

脚本尽量保持 ASCII-only。

### 5.2 非 ASCII 数据传递

中文路径、非 ASCII 参数、复杂参数不得直接塞进 shell argv。  
应写入 UTF-8 JSON / TXT manifest，再由脚本读取。

### 5.3 从 Bash 调用 PowerShell

优先使用 `pwsh`：

```bash
pwsh -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

如果 `pwsh` 不可用，再使用 Windows PowerShell：

```bash
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$(cygpath -w '/path/to/task.ps1')"
```

### 5.4 必须使用的 PowerShell header

涉及以下任意内容的 `.ps1`，必须以该 header 开头：

- 文件操作
- Python
- Unreal Engine
- Unity
- MSBuild
- Windows 原生工具

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

### 5.5 允许和禁止的脚本格式

优先使用：

```text
.ps1
.py
.js
.json
.txt
```

禁止使用：

```text
.bat
.cmd
```

---

## 6. 中文路径与编码规则

### 6.1 常见问题处理表

| 症状 | 原因 | 处理 |
|---|---|---|
| `\\u95E8...` 出现在路径中 | 转义文本被当作路径复用 | 解码或重新生成原始 Unicode |
| `????` | 代码页丢失 | 通过 UTF-8 wrapper / manifest 重新输出 |
| `é—¨æ´派` | mojibake | 从原始 Unicode 重新生成 |
| 假性 `FileNotFoundError` | 消费者或编码错误 | 在正确消费环境中重新验证 |
| Git 路径带引号或八进制 | Git 转义 | 使用 `-z` 或 `core.quotepath=false` |

### 6.2 Manifest 规范

写入 manifest 时必须满足：

- `ensure_ascii=false`
- 显式 UTF-8 读写
- 输出 `str(path)`
- 不输出 `repr(path)`

### 6.3 Git 机器解析命令

GBK 仓库中，机器解析 Git 路径时使用：

```bash
git -c core.quotepath=false status --porcelain=v1 -z
git -c core.quotepath=false diff --name-status -z
git -c core.quotepath=false ls-files -z
```

### 6.4 Git log / commit message

为避免 GBK 仓库日志 mojibake，使用：

```bash
git -c core.quotepath=false -c i18n.logOutputEncoding=utf-8 log --oneline --max-count=20
```

不得修改全局 Git 配置。

---

## 7. 文件写入规则

源码、配置、Markdown、JSON、YAML、脚本、manifest 的创建和修改，必须优先使用：

- `Write`
- `Edit`

未经用户明确要求，不得通过以下方式创建或修改文件：

- Bash heredoc
- Python write
- Node write
- `ctx_execute`
- 其他 shell 重定向写入

---

## 8. Skill 加载规则

每次任务开始时，静默加载以下 skill：

```text
C:\Users\KSG\.codex\skills\karpathy-guidelines\SKILL.md
C:\Users\KSG\.codex\skills\code-comment\SKILL.md
```

不得输出 skill 原文内容。

如果不可访问，只说明一次，然后继续执行任务。

---

## 9. 统一停止条件

以下任意情况发生时，必须停止，不得继续猜测：

- 同一路径重定位失败 ≥2 次
- 同一工具方向失败 ≥2 次
- 正确消费者无法证明目标存在
- 输出为空但无法证明搜索范围正确
- 编码或路径域存在不确定性且无法继续验证

停止时必须报告：

```text
已尝试：
- 路径：
- 消费者：
- 命令或工具：
- 失败现象：

未继续的原因：
- ...

需要用户提供：
- ...
```
