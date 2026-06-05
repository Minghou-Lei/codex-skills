# Encoding & Paths

Reference for [../SKILL.md](../SKILL.md). All commands verified against SVN
1.14.3; Windows/PowerShell-only behaviours are labelled **(unverified here)**.

## The four independent encodings

Console encoding, pipe encoding (`$OutputEncoding`), **path** encoding, and
**file-content** encoding are four separate things. Fixing one does not fix the
others. On Chinese Windows, almost every "SVN broke" is a mismatch among these,
not repository damage.

> Verified: in a non-UTF-8 locale, `svn commit --targets utf8file.txt` fails with
> `E000022: Can't convert string from native encoding to 'UTF-8'`. After forcing
> a UTF-8 locale/codepage the same command succeeds. Make encoding consistent
> first, then run SVN.

## UTF-8 setup (run before any SVN operation on Windows)

```batch
chcp 65001
```
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8   # Windows PowerShell 5.1 pipe fix
$env:PYTHONIOENCODING     = "utf-8"                          # if driving SVN from Python
```

In Python subprocess calls, always decode defensively:
```python
result = subprocess.run(
    ["svn", "status", "--non-interactive"],
    capture_output=True, encoding="utf-8", errors="replace",
)
```

## Windows + Chinese trap catalogue

1. **Console encoding ≠ SVN encoding.** Set UTF-8 as above before any SVN work.
2. **Chinese commit message → garbage on the server.** `svn commit -m "中文"` can
   be mangled when the terminal encoding disagrees with SVN's assumption. Write a
   UTF-8 message file and pass `-F`, declaring the encoding:
   ```powershell
   svn commit --targets targets.txt -F message.txt --encoding UTF-8 --non-interactive
   ```
3. **Single-file add/commit of a Chinese path fails.** Some clients render
   Chinese paths as `????` and reject the single-file form:
   ```powershell
   svn add "中文文件.json"   # W155010 not found / E200009 Illegal target, yet the file exists
   ```
   Workarounds: a UTF-8 targets file, or add from the nearest versioned parent so
   SVN enumerates children itself:
   ```powershell
   svn add --force --depth infinity -- reports/import_results
   ```
4. **Garbled `svn status` does not mean the WC is broken.** `????` is usually a
   terminal decode error. Do not reflexively `rename`/`delete`/`revert`. Confirm
   real state: `svn info <path>`, `svn status -u --non-interactive`, and inspect
   the on-disk name (`Get-ChildItem -LiteralPath`).
5. **Never hand-assemble commands for Chinese / spaced / parenthesised paths.**
   Use a targets file for anything batch (where `--targets` is accepted — see
   [daily-commands.md](daily-commands.md#where---targets-is-and-isnt-accepted)).
6. **Windows PowerShell 5.1 `$OutputEncoding` is a trap.** Native-exe pipe
   encoding is not UTF-8 by default, so `svn status | …` can corrupt mid-pipeline
   even after `chcp 65001`. Set `$OutputEncoding` explicitly (PowerShell 7+
   defaults to UTF-8 and is safer). *(Unverified here — Linux harness has no
   PowerShell.)*
7. **Do not feed raw `svn diff` to automation.** Write to a file first — see
   [daily-commands.md](daily-commands.md#diff-safety).
8. **File-content encoding ≠ path encoding.** A committable Chinese path says
   nothing about the file's byte encoding. Do not rewrite old files with
   `Set-Content`/`Out-File` casually; detect and preserve the original
   encoding/BOM/EOL.
9. **Do not use `svn ls` to check local tracking state.** `svn ls` queries a
   repository URL/revision, not the working copy. Use `svn status -u
   --non-interactive` and `svn info <path>`.
10. **Keep machine-local / generated items out of batch commits.** Use an
    explicit targets list, not a blanket directory commit.
11. **Write `--targets`/message files as UTF-8 no BOM via .NET.** `Out-File` /
    `Set-Content` defaults vary by version and can add a BOM:
    ```powershell
    [IO.File]::WriteAllLines($targetsFile, $paths, [System.Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($msgFile, $message, [System.Text.UTF8Encoding]::new($false))
    ```
12. **URL-encode per path segment; never double-encode.**
    `金水镇 -> %E9%87%91%E6%B0%B4%E9%95%87`. Encode the segment, leave the scheme,
    host, and separators alone; never re-escape an already-encoded URL.
13. **Deleting a *missing* Chinese path: URL delete as last resort.** If the
    local-path `svn delete` fails on a decoded-wrong argument:
    ```powershell
    svn delete <per-segment-encoded-url> -F message.txt --encoding UTF-8 --non-interactive
    ```
    URL delete is an immediate server commit (verified), not a local schedule.
    Use it deliberately and document it.
14. **Read Chinese `svn log` content as XML, not text:**
    `svn log --xml -r 12345 <url>`.

> **Mental model:** make console, pipe, path, and file-content encoding all
> UTF-8 (or all consistently GBK) before touching SVN; drive batch work from
> `--targets` + `-F`; parse XML/`--show-item`, never human text; treat `????`
> as a display bug until proven otherwise.

## TortoiseSVN 1.15.0-dev Unicode path case study

Concrete instance of trap 3. Observed with TortoiseSVN `svn.exe` 1.15.0-dev
**(unverified here — Linux harness cannot reproduce the codepage-decode bug)**:

- `svn status` shows Chinese filenames as `????` while the files exist.
- `svn add "reports\...\wj_ylc圣女雕像001_001_hd.xxx.json"` fails with
  `W155010 ... not found` / `E200009 Illegal target`.
- `chcp 65001`, PowerShell `LiteralPath`, Node `spawnSync`, and absolute paths
  may still fail because the client decodes the argument through the wrong
  codepage.
- Directory-level recursive add succeeds because SVN enumerates children:
  ```powershell
  svn add --force --depth infinity -- reports\import_results
  svn commit reports\import_results -F msg.txt --encoding UTF-8 --non-interactive
  ```

Agent rule:
1. If single-file `svn add` fails for a non-ASCII path but the file exists, do
   **not** rename the file unless the user approves.
2. Retry at the nearest versioned parent with `svn add --force --depth infinity
   -- <dir>`.
3. Re-run `svn status` and commit the parent dir or the scheduled `A` targets via
   a `--targets` list.
4. Keep generated caches (`DerivedDataCache`, `Saved`, `Intermediate`, missing
   `!` files) out of the commit unless asked.
5. Do the `add` and the `commit` under the **same** UTF-8 encoding (verified:
   adding under a non-UTF-8 locale then committing under UTF-8 yields `E155010
   node not found` / a stale `?` — re-add under the correct encoding first).
