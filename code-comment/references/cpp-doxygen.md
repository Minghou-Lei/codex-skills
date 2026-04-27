# C++ Doxygen 注释规范

适用：`.cpp` `.h` `.hpp` `.cc`，引擎项目（UE、KG3D 等）中的 C++ 代码。

---

## 文件头注释

```cpp
/**
 * @file    RenderGraph.h
 * @brief   渲染图（RenderGraph）的核心调度器，负责管理 Pass 依赖与资源生命周期
 * @author  MinghouLei
 * @date    2025-01-10
 *
 * @note    本文件不依赖平台 RHI，仅处理抽象资源描述符。
 *          实际 GPU 提交由 RHICommandList 层完成。
 */
```

## 类注释

```cpp
/**
 * @class   FDeferredShadingPass
 * @brief   延迟着色阶段的 GBuffer 填充 Pass
 *
 * 负责将场景几何信息（法线、粗糙度、Base Color 等）写入 GBuffer，
 * 供后续光照 Pass 使用。不执行任何光照计算。
 *
 * @note    非线程安全，必须在渲染线程调用。
 *          生命周期由 FRenderGraph 管理，不允许手动 delete。
 */
class FDeferredShadingPass : public FRenderPass
{
    // ...
};
```

## 函数注释（按档位）

### 档位 S：有非显然约束 → 完整 Doxygen

```cpp
/**
 * @brief   将世界空间法线编码为 GBufferA 的 RG 通道（Octahedron 编码）
 *
 * 使用 Octahedral 映射将单位球面法线压缩到 [0,1]² 的 UV 空间，
 * 相比球坐标编码精度更高，避免极点奇异性。
 * 参考：Cigolle et al. 2014, "Survey of Efficient Representations for Independent Unit Vectors"
 *
 * @param   WorldNormal   世界空间单位法线，必须已归一化（length == 1.0f）
 * @param   OutEncoded    输出：编码后的 RG 值，范围 [0, 1]
 * @return  编码是否成功；输入零向量时返回 false，OutEncoded 置为 (0.5, 0.5)
 * @note    此函数在 Pixel Shader 路径被大量调用，禁止添加分支，保持向量化友好
 * @see     FGBufferDecoder::DecodeNormal()
 */
bool EncodeNormalToGBuffer(const FVector3f& WorldNormal, FVector2f& OutEncoded);
```

### 档位 0：名字自解释 → 不写注释

```cpp
// ❌ 这种注释是噪声
/** @brief 获取材质名称 */
FString GetMaterialName() const;

// ✅ 沉默就是最好的答案
FString GetMaterialName() const;
```

### 档位 A/S 边界：简单函数但有隐性约束 → 单行即可

```cpp
// 必须在 Initialize() 之前调用，运行时调整无效
void SetMaxInstances(int32 MaxCount);
```

## 成员变量注释

```cpp
class FMaterialProxy
{
private:
    /** 材质资产的弱引用，用于在资产热重载时自动失效（不阻止 GC） */
    TWeakObjectPtr<UMaterialInterface> MaterialRef;

    /** 上一帧的 Shader Hash，用于检测 Shader 是否需要重新编译 */
    uint64 CachedShaderHash = 0;

    /**
     * 当前批次中待提交的 Draw Call 数量。
     * 超过 FRenderConfig::MaxDrawCallsPerBatch 时触发强制刷新。
     */
    int32 PendingDrawCalls = 0;
};
```

## 内联注释规范

```cpp
// ---- 正确示范 ----

// 跳过 Stencil 值为 0 的像素（天空盒区域，不参与光照计算）
if (StencilValue == 0) continue;

// 使用 rsqrt 近似代替 normalize，精度损失 < 0.01%，性能提升约 2x（Profiler 数据见 #4521）
float InvLen = rsqrt(dot(N, N));

// HACK(leiMH): AMD GCN 驱动在 UAV 读写同帧时存在 race condition，
// 强制插入 barrier 绕过（驱动版本 >= 23.7.1 后可移除）
InsertUAVBarrier();

// ---- 禁止示范 ----
i++;            // 递增 i        ← 废话注释
return result;  // 返回结果      ← 废话注释
```

## TODO / FIXME 格式

```cpp
// TODO(username): 说明待做事项 + 原因（可加 Issue 编号）
// TODO(leiMH): 当 LOD 级别 > 4 时此路径未经测试，需补充单元测试（JIRA-3892）

// FIXME(username): 已知 Bug 说明 + 触发条件
// FIXME(leiMH): 在多视口模式下 ViewMatrix 未正确更新，复现步骤见 PR #287 描述

// HACK(username): 说明为何采用非常规做法，以及何时可以移除
// HACK(leiMH): UE 5.3 的 RDG 在此场景下存在资源泄漏，手动 AddPass 绕过
```

## 模板与宏的额外要求

```cpp
/**
 * @brief   类型安全的 Enum 位掩码操作，生成 operator| 等按位运算符重载
 *
 * @tparam  EnumType  必须是 enum class，且底层类型为整数
 *
 * @warning 不要对非位标志枚举使用此宏，会产生未定义含义的组合值
 */
#define ENUM_CLASS_FLAGS(EnumType) \
    inline EnumType operator|(EnumType A, EnumType B) { ... } \
    // ...
```

## 引擎项目特殊约定（KG3D / UE 通用）

- RHI 层函数注释须说明：支持的 API（DX11/DX12/Vulkan）、是否需要在渲染线程调用
- Pass 类注释须说明：读取哪些输入资源、写入哪些输出资源
- 线程模型相关函数必须标注：`@note 仅限渲染线程` / `@note 线程安全` / `@note 仅限游戏线程`
