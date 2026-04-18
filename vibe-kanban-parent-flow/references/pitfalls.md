# Common Failure Modes

## 1. Too Much Parallelism

Symptom: Vibe Kanban returns `429 Too Many Requests` or exceeded retry limits.

Cause: Starting too many subtasks at once, especially across multiple parent todos.

Correct approach:

- Run parent todos serially.
- Only parallelize child subtasks under the same parent.
- Stagger workspace creation and add retry backoff.

## 2. Wrong Workspace Entry Point

Symptom: A workspace exists, but the issue-to-workspace relationship is missing or unclear.

Cause: Creating workspaces from the wrong place instead of the subtask issue itself.

Correct approach:

- Start workspaces from the subtask issue detail record.
- Preserve issue -> workspace -> branch linkage for every subtask.

## 3. Starting the Next Parent Too Early

Symptom: The next parent todo behaves as if previous work never happened.

Cause: The previous parent was not merged into `main` before the next parent started.

Correct approach:

- Integrate the finished parent batch.
- Merge it into `main`.
- Start the next parent only from updated `main`.

## 4. Temporary Branch Sprawl

Symptom: `vk/*` branches and workspaces accumulate until it becomes unclear what is still relevant.

Cause: Treating temporary execution branches as long-lived collaboration branches.

Correct approach:

- Treat `vk/*` as disposable.
- Delete child workspaces and temporary branches as soon as the parent batch is absorbed.

## 5. Over-Broad Cleanup

Symptom: Cleaning one mistaken batch also destroys useful context from an earlier successful parent todo.

Cause: Deleting all workspaces instead of only the current bad batch.

Correct approach:

- Stop and delete only the affected batch.
- Keep already-finished parents intact unless the user explicitly requests a full reset.

## 6. Rust Missing

Symptom: `cargo metadata ... program not found` or `cargo` / `rustc` missing.

Cause: Rust toolchain is not installed or not on `PATH`.

Correct approach:

- Install `rustup`.
- Confirm `cargo --version` and `rustc --version`.
- Re-run Tauri only after both are available.

## 7. Tauri Version Mismatch

Symptom: npm Tauri packages and Rust Tauri crates report mismatched versions.

Cause: Frontend packages and Rust crates drifted onto different major/minor lines.

Correct approach:

- Keep `@tauri-apps/api`, `@tauri-apps/cli`, Rust `tauri`, and `tauri-build` aligned on the same major/minor line.

## 8. Wrong Frontend Dev Port

Symptom: Tauri waits forever for the frontend even though Vite already started.

Cause: `tauri.conf.json` and `vite.config.ts` disagree about the dev server URL/port.

Correct approach:

- Use a single fixed dev port.
- Keep Tauri `devUrl` and Vite `server.port` aligned.

## 9. Missing MSVC Linker

Symptom: Rust compile fails with `link.exe not found`.

Cause: Rust is installed, but MSVC build tools are not available in the active environment.

Correct approach:

- Install Visual Studio Build Tools with the C++ toolchain and Windows SDK.
- Run build commands from a VS developer environment when needed.

## 10. Release Assets Missing

Symptom: GitHub Release only shows source archives and no installer or executable.

Cause: Tagging a version without uploading built desktop artifacts.

Correct approach:

- Keep the release tag.
- Upload `.exe` / `.msi` artifacts as release assets.
- Treat source archives as automatic byproducts, not the release deliverable.

## 11. Broken README Images

Symptom: README previews are wrong, stale, or missing on GitHub.

Cause: Referencing local paths or replacing copy without updating repository assets.

Correct approach:

- Store screenshots under a stable repo path such as `docs/assets/`.
- Reference only repo-relative asset paths from README.

## 12. Weak Safety Disclaimer

Symptom: Users mistake the project for a production-safe system utility.

Cause: The repository relies on license text alone and lacks a prominent warning.

Correct approach:

- Keep the license separate from operational risk messaging.
- Put a high-visibility warning in README when the project is an experimental vibe-coding / multi-subagent workflow test.
