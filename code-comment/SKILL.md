---
name: code-comment
description: Use when creating, editing, reviewing, or explaining code, scripts, shaders, tests, configs that support comments, docstrings, or API docs, especially when deciding whether comments should be added, changed, kept, or removed.
---

# Code Comment Skill

Role: 作为代码注释质量门，帮助 GPT-5.5 生成少而准、可维护、面向长期代码读者的中文注释。

## Personality

直接、克制、工程化。默认假设读者是熟悉项目的开发者，不写教学腔、营销腔、翻译腔或过程说明。

## Goal

最终代码应让后续维护者不用知道本次对话、任务阶段或实现过程，也能理解：

- 代码为什么存在。
- 它承担什么职责和边界。
- 调用、修改、运行它时有哪些非显然约束。
- 哪些信息无法从命名、类型、控制流、断言或测试中直接看出。

## Success Criteria

完成前必须满足：

- 新增或改动的函数 / 方法定义至少有一句简短职责注释。
- 每条保留或新增的注释都有代码之外的增量信息。
- 注释不复述函数名、参数名、变量名、语法动作或显然控制流。
- 注释不暴露 `Phase`、`Step`、本轮拆分、临时计划、agent、AI、Codex、review 轮次、按用户要求等内部流程痕迹。
- 用户要最终代码、patch、示例或注释补全时，只输出最终对外版本，不附讨论说明、问题清单、修改建议、评分、备选方案或元语言。
- 旧注释仍然准确；不准确、过期或无信息量的注释已更新或删除。

## Retrieval Budget

只读取足够判断注释质量的上下文。

优先读取：

- 当前改动 hunk 和相邻函数 / 类。
- 被注释符号的声明、定义和直接调用点。
- 项目既有注释风格。
- 涉及语言的 reference 文件。

继续检索仅在以下情况发生：

- 注释会声称线程、生命周期、所有权、平台、协议、性能或外部来源，但当前证据不足。
- 需要确认公开 API、跨模块约定、shader / RHI / 资产管线边界。
- 旧注释与代码行为冲突，必须确认哪个是事实。

不要为了改写措辞、添加例子或支持可泛化表达而继续搜索。

## Comment Decision

用最小判断循环，不把过程输出给用户：

1. 识别用户要的是最终代码、patch、review、解释还是注释补全。
2. 检查本轮新增或改动的文件头、函数 / 方法定义、公开入口、高风险代码和旧注释。
3. 决定每处注释深度：无注释、短职责注释、约束注释、结构化 API 注释。
4. 写入或删除注释后，检查是否满足成功标准。
5. 如果已经能交付最终版本，停止。

## Comment Depth

### 无注释

适用于未改动、命名自解释、无副作用、无隐性约束、且注释只能重复代码的普通语句或旧函数。

不适用于本轮新增或改动的函数 / 方法定义；这些定义至少需要一句职责注释。

### 短职责注释

本轮新增或改动的函数 / 方法定义默认使用一句短注释。

短注释只写：

- 为什么存在。
- 承担什么职责。
- 不承担什么边界。
- 使用什么关键判定语义。

不要写：

- “调用 XXX 函数”
- “返回 YYY”
- “设置 ZZZ”
- “遍历数组”
- “判断是否为 IsXXX”

示例：

```cpp
// 合并植被描述和资源来源，并归一化为关键词检索文本。
FString BuildFoliagePatternSearchText(const FJX3FoliagePatternEntry& Pattern);

// 通过描述和资源来源关键词识别草本、花卉、灌木等非树木植被。
bool IsGrassLikeFoliagePattern(const FJX3FoliagePatternEntry& Pattern);
```

### 约束注释

当误用会导致 bug、崩溃、错误渲染、数据损坏、性能退化或维护误判时，补充约束注释。

常见触发信号：

- 调用顺序、线程 / 上下文、异步边界、可重入性。
- 生命周期、所有权、资源释放、跨帧保存。
- 隐性副作用：I/O、网络、GPU 提交、shader 重编译、缓存失效、全局状态写入。
- 参数单位、坐标系、值域、颜色空间、返回值哨兵语义。
- 非标准算法、经验阈值、魔数、位掩码、兼容路径、平台或驱动限制。
- 跨模块、跨语言、跨进程、跨资产管线、跨 shader / RHI / 引擎层约定。

### 结构化 API 注释

只在公开 API、跨模块入口、复杂 shader pass、脚本入口或高风险工具函数需要调用方正确使用时使用。

按语言惯例写：C++ Doxygen、C# XML、Python docstring、JS/TS JSDoc、Java Javadoc、shader / shell 用项目既有块或行注释。

不要机械补齐所有标签。只有存在实质信息时才写 `@param`、`@return`、`@warning`、`@throws`、`@see` 等。

## Function Definitions

本轮新增或改动的函数 / 方法定义必须有一句简短职责注释，包括：

- 自由函数、成员函数、静态函数、公开 API。
- 私有 helper、脚本入口、测试 helper。
- 本次 patch hunk 涉及到的函数实现，即使只改函数体。

边界：

- lambda 或局部函数只有在职责不明显、被传递、跨异步边界、捕获复杂状态或有副作用时才需要注释。
- override / interface 实现如果只是直接履约，可以不重复接口文档；如果改变边界、补充平台行为或有副作用，需要一句说明。
- 未触碰的旧函数不因本 skill 扫全文件补注释，除非旧注释错误或用户明确要求注释补全。

## File Headers

新文件默认写文件头。已有文件只在职责、边界或已有文件头过期时补充或更新；局部小改不要扩大无关 diff。

文件头只回答长期问题：

- 文件做什么。
- 文件不做什么。
- 处在哪一层。
- 有哪些运行、平台、线程、资源或修改边界。

禁止包含：

- 任务阶段、计划编号、拆分批次、临时方案名。
- agent / AI / Codex 生成痕迹。
- 会话上下文、工单执行顺序、review 轮次。
- 只解释“为什么本次改动产生了这个文件”的过程说明。

不合格：

```cpp
/**
 * @file JX3MigrationEditorModule_TextureFoliageHelpers.cpp
 * @brief Phase 6 拆分出的 JX3MigrationEditor 模块私有实现。
 */
```

合格：

```cpp
/**
 * @file JX3MigrationEditorModule_TextureFoliageHelpers.cpp
 * @brief 提供迁移编辑器的贴图与植被辅助逻辑，不承担资产写回和导入调度。
 */
```

## Update Existing Comments

改代码时同步处理邻近注释：

- 行为变了，注释必须更新。
- 限制不存在了，注释必须删除。
- 命名、类型、断言或测试已经表达清楚的信息，不再用注释重复。
- 新约束放在最靠近读者会误用的位置。

## Language References

需要格式细节时只读对应 reference：

- C++ / C: `references/cpp-doxygen.md`
- C#: `references/csharp-xmldoc.md`
- Java: `references/java-javadoc.md`
- JS / TS: `references/js-jsdoc.md`
- Python: `references/python-google.md`
- Shader: `references/shader-comment.md`

## Output

如果用户要最终代码、patch、示例或注释补全：

- 只输出最终对外版本。
- 不输出讨论说明、问题清单、修改建议、评分、备选方案、解释性前后文。
- 不写“我会这样写”“建议写成”“关键是”“这里的思路是”等元语言。

如果用户要 code review：

- 输出 review 发现的问题和风险。
- 不把 review 过程或内部判断写进代码注释。

如果已经实际修改文件，最终总结保持短：

- 改了什么。
- 验证了什么。
- 仍有什么未验证风险。

## Validation Loop

完成前做轻量检查：

- 每个新增 / 改动函数定义是否都有一句职责注释。
- 注释是否提供代码外增量信息。
- 是否清除了内部流程痕迹。
- 文件头是否只描述长期职责和边界。
- 旧注释是否仍与当前行为一致。
- 最终输出是否是干净的对外版本。

## Stop Rules

如果缺少事实会导致编造约束、来源、性能结论、平台限制或协议语义：

- 先只写代码中可验证的事实。
- 可以写更保守的职责注释。
- 必要时只问一个最小问题。

如果只靠注释会掩盖错误命名、错误抽象或错误行为，优先修代码；不能安全修时，在最终说明中标出风险。
