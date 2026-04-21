# 桌面交付常见失败模式

这份 reference 只适用于桌面 / Tauri / Rust / GitHub Release 类项目。

如果当前任务只是通用的 issue / `Relationships` / `workspace` 编排，请回到主 `SKILL.md`，不要把这些项目特定问题混入核心协议。

## 1. 缺少 Rust

症状：出现 `cargo metadata ... program not found`，或者系统里找不到 `cargo` / `rustc`。

原因：Rust 工具链未安装，或未加入 `PATH`。

正确做法：

- 安装 `rustup`。
- 确认 `cargo --version` 和 `rustc --version` 都可用。
- 只有在两者都就绪后，才重新运行桌面构建流程。

## 2. Tauri 版本不匹配

症状：npm 侧的 Tauri 包和 Rust 侧的 Tauri crate 报告版本不一致。

原因：前端包与 Rust crate 漂移到了不同的 major/minor 版本线。

正确做法：

- 让 `@tauri-apps/api`、`@tauri-apps/cli`、Rust `tauri` 与 `tauri-build` 保持相同的 major/minor 版本线。

## 3. 错误的前端开发端口

症状：即使前端 dev server 已经启动，桌面壳层仍一直等待前端。

原因：`tauri.conf.json` 与 `vite.config.ts` 的 dev server URL / port 配置不一致。

正确做法：

- 使用一个固定的开发端口。
- 让 Tauri 的 `devUrl` 与 Vite 的 `server.port` 保持一致。

## 4. 缺少 MSVC 链接器

症状：Rust 编译失败，并提示 `link.exe not found`。

原因：Rust 已安装，但当前环境没有可用的 MSVC Build Tools。

正确做法：

- 安装带有 C++ toolchain 和 Windows SDK 的 Visual Studio Build Tools。
- 在需要时，从 VS developer environment 运行构建命令。

## 5. 发布资产缺失

症状：GitHub Release 里只有源码压缩包，没有 installer 或可执行文件。

原因：打了版本 tag，但没有上传构建出的桌面产物。

正确做法：

- 保留 release tag。
- 把 `.exe` / `.msi` 上传为 release assets。
- 把源码压缩包视为自动副产物，而不是实际交付物。

## 6. README 图片失效

症状：README 预览图错误、过期，或在 GitHub 上无法显示。

原因：引用了本地路径，或替换文案时没有同步更新仓库内的资源文件。

正确做法：

- 把截图放在稳定的仓库路径下，例如 `docs/assets/`。
- 在 README 中只引用仓库相对路径的资源。

## 7. 安全警告不足

症状：用户把这个项目误认为可安全用于生产系统的工具。

原因：仓库只依赖 license 文本，没有放置显眼的运行风险警告。

正确做法：

- 将 license 与运行风险说明分开处理。
- 如果仓库属于实验性的 vibe-coding / multi-subagent 工作流测试，就在 README 中放置高可见度警告。
