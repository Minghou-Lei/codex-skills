# C# XML 文档注释规范

适用：`.cs` 文件，兼容 Visual Studio IntelliSense、DocFX、Sandcastle 文档生成。

---

## 文件/命名空间说明（用 region 或顶部注释）

```csharp
// ============================================================
// GBufferUtils.cs
// GBuffer 编解码工具类，提供从/向 GBuffer RT 读写数据的辅助方法。
// 依赖：UnityEngine.Rendering（HDRP 渲染管线）
// 线程模型：所有方法仅在渲染线程调用
// ============================================================
```

## 类注释

```csharp
/// <summary>
/// 延迟着色阶段的 GBuffer 分配器，负责创建和管理 MRT 渲染目标。
/// </summary>
/// <remarks>
/// 本类不执行光照计算，仅负责将几何信息（法线、粗糙度等）写入对应的 RT Slot。
/// 实例生命周期由 <see cref="DeferredRenderPipeline"/> 管理，请勿手动释放。
/// <para>
/// 线程安全：<b>非线程安全</b>，所有方法须在渲染线程调用。
/// </para>
/// </remarks>
public class GBufferAllocator : IDisposable
{
    // ...
}
```

## 方法注释

```csharp
/// <summary>
/// 将世界空间单位法线编码为 Octahedral 格式，写入 GBufferA 的 RG 通道。
/// </summary>
/// <remarks>
/// Octahedral 编码将球面方向压缩到 [0,1]² 的 UV 空间，
/// 相比球坐标编码在极点附近精度更高，且 GPU 解码开销更低。
/// <para>
/// 参考：Cigolle et al. 2014 "Survey of Efficient Representations for Independent Unit Vectors"
/// </para>
/// </remarks>
/// <param name="worldNormal">
///   世界空间单位法线。必须已归一化（magnitude ≈ 1.0f）。
///   传入零向量时返回 <see langword="false"/>，输出置为 (0.5f, 0.5f)。
/// </param>
/// <param name="encoded">
///   输出：编码后的 RG 值，值域 [0f, 1f]，对应 GBufferA 的前两个通道。
/// </param>
/// <returns>
///   编码是否成功。输入为非零向量时始终返回 <see langword="true"/>。
/// </returns>
/// <exception cref="ArgumentException">
///   当 <paramref name="worldNormal"/> 包含 NaN 或 Infinity 时抛出。
/// </exception>
/// <seealso cref="DecodeNormalFromGBuffer(Vector2, out Vector3)"/>
public static bool EncodeNormalToGBuffer(Vector3 worldNormal, out Vector2 encoded)
{
    // ...
}
```

## 属性注释

```csharp
/// <summary>
/// 当前帧 GBuffer 中实际使用的 MRT 数量。
/// </summary>
/// <value>
/// 范围 [1, <see cref="MaxMRTCount"/>]。
/// 在 <see cref="Allocate"/> 调用前值为 0。
/// </value>
public int ActiveMRTCount { get; private set; }

/// <summary>
/// 平台支持的最大 MRT 绑定数量（从驱动查询，不可修改）。
/// </summary>
/// <remarks>
/// DX11 = 8，DX12 / Vulkan = 8，Metal = 8（iOS 为 4）。
/// 超出此值的 RT Slot 会被静默忽略，并输出一条警告日志。
/// </remarks>
public static readonly int MaxMRTCount;
```

## 枚举注释

```csharp
/// <summary>
/// GBuffer RT Slot 的逻辑分配枚举，与 Shader 中的 SV_Target 序号对应。
/// </summary>
public enum GBufferSlot
{
    /// <summary>GBufferA（RGBA8）：Base Color（RGB）+ 材质掩码（A）</summary>
    BaseColor = 0,

    /// <summary>GBufferB（RGBA8）：Octahedral 法线（RG）+ 粗糙度（B）+ 金属度（A）</summary>
    NormalRoughness = 1,

    /// <summary>GBufferC（R16F）：线性深度，单位为世界空间米</summary>
    LinearDepth = 2,
}
```

## 内联注释规范

```csharp
// ---- 正确示范 ----

// rsqrt 近似归一化，比 Vector3.Normalize 快约 2x，精度足够（< 0.01% 误差）
float invLen = math.rsqrt(math.dot(n, n));

// 跳过天空盒像素：Stencil = 0 表示未写入 GBuffer 的背景区域
if (stencilValue == 0) return;

// HACK(leiMH): Unity 2022.3 在 Metal 后端下 MRT 第 4 个 Slot 写入顺序错乱，
// 手动调换 Slot 3/4 绕过（已向 Unity 提 Bug Report，Build 2022.3.15 后可移除）
SwapSlots(3, 4);

// ---- 禁止示范 ----
count++;          // count 加 1     ← 废话
return value;     // 返回 value     ← 废话
```

## 异步方法注释

```csharp
/// <summary>
/// 异步加载纹理资产并上传到 GPU，返回可用的纹理句柄。
/// </summary>
/// <param name="path">资产路径，相对于 StreamingAssets 根目录。</param>
/// <param name="cancellationToken">
///   用于取消操作。取消后 GPU 资源会在下一帧 GC 时释放。
/// </param>
/// <returns>
///   成功时返回已上传的 <see cref="TextureHandle"/>；
///   路径不存在时返回 <see langword="null"/>。
/// </returns>
/// <exception cref="OperationCanceledException">当 cancellationToken 触发时抛出。</exception>
/// <remarks>
/// 本方法内部使用 <c>await UniTask.SwitchToThreadPool()</c> 执行磁盘 I/O，
/// 返回后自动切回主线程。调用方无需手动切换线程上下文。
/// </remarks>
public async UniTask<TextureHandle?> LoadTextureAsync(
    string path,
    CancellationToken cancellationToken = default)
```

## 接口注释

```csharp
/// <summary>
/// 渲染 Pass 的统一接口，所有自定义 Pass 必须实现此接口以接入渲染图调度。
/// </summary>
/// <remarks>
/// 实现类须保证幂等性：相同输入状态下多次调用 <see cref="Execute"/> 结果一致。
/// </remarks>
public interface IRenderPass
{
    /// <summary>获取 Pass 的唯一标识名，用于调试和 Frame Debugger 显示。</summary>
    string Name { get; }

    /// <summary>
    /// 声明本 Pass 所需的输入/输出资源，供调度器推导依赖关系。
    /// </summary>
    /// <param name="builder">资源声明构建器，调用其 Read/Write 方法注册依赖。</param>
    void Setup(IRenderGraphBuilder builder);

    /// <summary>执行 Pass 的实际渲染逻辑，由渲染图在正确时序下调用。</summary>
    /// <param name="context">当前帧的渲染上下文，包含 CommandBuffer 和帧参数。</param>
    void Execute(RenderContext context);
}
```
