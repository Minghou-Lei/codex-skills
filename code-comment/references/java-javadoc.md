# Java Javadoc 注释规范

适用：`.java` 文件，兼容 javadoc 工具、IntelliJ IDEA、Checkstyle。

---

## 类注释

```java
/**
 * 渲染 Pass 调度器，根据输入/输出资源依赖关系对 Pass 进行拓扑排序并顺序执行。
 *
 * <p>典型使用方式：
 * <pre>{@code
 * RenderPassScheduler scheduler = new RenderPassScheduler();
 * scheduler.registerPass(gbufferPass);
 * scheduler.registerPass(lightingPass);
 * scheduler.compile();
 * scheduler.execute(context);
 * }</pre>
 *
 * <p><b>线程安全：</b>非线程安全，所有方法须在渲染线程调用。<br>
 * <b>生命周期：</b>单次使用，执行完成后不可复用。
 *
 * @author MinghouLei
 * @since 2.0.0
 * @see IRenderPass
 * @see RenderContext
 */
public class RenderPassScheduler {
```

## 方法注释

```java
/**
 * 将世界空间单位法线编码为 Octahedral 格式，压缩至 [0,1]² 的 UV 空间。
 *
 * <p>Octahedral 编码相比球坐标编码在极点附近精度更高，
 * 且解码计算量更低，适合写入 GBuffer 的 RG 通道。
 *
 * @param worldNormal 世界空间单位法线 {@code [x, y, z]}。
 *                    调用前必须已归一化（{@code length ≈ 1.0f}）。
 *                    传入零向量时行为未定义（不抛出异常，直接返回 {@code [0.5f, 0.5f]}）。
 * @return 编码后的 UV 坐标 {@code [u, v]}，值域 {@code [0f, 1f]}，
 *         对应 GBufferA 的 RG 通道。永不返回 {@code null}。
 * @throws IllegalArgumentException 当 {@code worldNormal} 包含 NaN 或 Infinity 时抛出。
 *
 * @see #decodeNormalFromGBuffer(float[]) 对应的解码函数
 */
public static float[] encodeNormalOctahedral(float[] worldNormal) {
```

## 字段注释

```java
/**
 * 已注册的 Pass 列表，按注册顺序排列。
 * {@link #compile()} 执行后此列表锁定，不允许继续添加。
 */
private final List<IRenderPass> registeredPasses = new ArrayList<>();

/**
 * 平台支持的最大 MRT 绑定数量，从驱动查询，初始化后不可修改。
 *
 * <p>DX11 / DX12 / Vulkan = 8，Metal（iOS）= 4。
 * 超出此值的 RT Slot 会被静默忽略并输出 WARN 日志。
 */
private static final int MAX_MRT_COUNT;
```

## 枚举注释

```java
/**
 * GBuffer RT Slot 的逻辑分配，与 Shader 中的颜色输出绑定点对应。
 *
 * <p>修改此枚举时，须同步更新 {@code DeferredLighting.hlsl} 中的 Slot 宏定义。
 */
public enum GBufferSlot {
    /** GBufferA（RGBA8）：Base Color（RGB）+ 材质掩码（A，0=不透明，1=次表面） */
    BASE_COLOR(0),

    /** GBufferB（RGBA8）：Octahedral 法线（RG）+ 粗糙度（B）+ 金属度（A） */
    NORMAL_ROUGHNESS(1),

    /** GBufferC（R16F）：线性深度，单位为世界空间米，由深度 RT 反推 */
    LINEAR_DEPTH(2);

    /** 对应的 SV_Target 序号（从 0 开始），与 Shader 绑定点严格对应 */
    public final int slotIndex;

    GBufferSlot(int slotIndex) {
        this.slotIndex = slotIndex;
    }
}
```

## 内联注释规范

```java
// ---- 正确示范 ----

// rsqrt 近似归一化比 Math.sqrt 快约 2x，精度差异 < 0.01%，可接受
float invLen = (float) (1.0 / Math.sqrt(dot(n, n)));

// Stencil = 0 表示天空盒像素，GBuffer 中无有效表面数据，跳过光照计算
if (stencilValue == 0) continue;

// FIXME(leiMH): Android Adreno 6xx 驱动在 MRT 超过 4 个 Slot 时写入顺序错乱，
// 强制降级为单 RT 模式绕过（复现机型：小米 12，MIUI 14，驱动版本 512.503）
if (isAdreno6xx()) {
    fallbackToSingleRT();
}

// ---- 禁止示范 ----
i++;              // 自增 i          ← 废话
return result;    // 返回结果        ← 废话
```

## 接口注释

```java
/**
 * 渲染 Pass 的统一接口，所有自定义 Pass 须实现此接口以接入调度器。
 *
 * <p><b>实现约束：</b>
 * <ul>
 *   <li>{@link #execute(RenderContext)} 须保证幂等性</li>
 *   <li>禁止在 {@link #execute} 中调用 {@link #setup}（会破坏调度器的依赖图）</li>
 *   <li>实现类须为无状态设计，或将可变状态封装在 {@link RenderContext} 中</li>
 * </ul>
 */
public interface IRenderPass {

    /**
     * 返回 Pass 的唯一标识名，用于 Frame Debugger 和日志显示。
     *
     * @return 非空、非空白字符串，在同一调度器内须全局唯一。
     */
    @Nonnull
    String getName();

    /**
     * 声明本 Pass 所需的输入/输出资源，供调度器推导执行顺序。
     * 在 {@link #execute} 之前由调度器调用恰好一次。
     *
     * @param builder 资源依赖声明构建器，调用其 read/write 方法注册依赖。
     */
    void setup(@Nonnull IRenderGraphBuilder builder);
}
```
