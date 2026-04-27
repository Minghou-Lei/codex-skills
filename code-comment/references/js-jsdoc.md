# JavaScript / TypeScript JSDoc 注释规范

适用：`.js` `.ts` `.jsx` `.tsx`，兼容 VS Code IntelliSense、TypeDoc、ESLint jsdoc 插件。

---

## 文件头注释

```typescript
/**
 * @file    renderGraph.ts
 * @description 渲染图调度器的 TypeScript 实现，负责 Pass 依赖解析与执行排序。
 *
 * @module  RenderGraph
 * @author  MinghouLei
 *
 * @remarks
 * 本模块不依赖任何 WebGL/WebGPU 的具体实现，通过 IRHIBackend 接口抽象底层 API。
 * 仅在主线程使用，不支持 Web Worker 调用。
 */
```

## 函数注释

```typescript
/**
 * 将世界空间单位法线编码为 Octahedral 格式（压缩至 [0,1]² UV 空间）。
 *
 * 使用 Octahedral 映射代替传统球坐标，在极点附近精度更高，
 * 解码开销更低，适合写入 GBuffer 的 RG 通道。
 *
 * @param normal - 世界空间单位法线 [x, y, z]，调用前必须已归一化（length ≈ 1.0）。
 *                 传入零向量时返回 [0.5, 0.5] 并输出警告。
 * @returns 编码后的 [u, v]，值域 [0, 1]，对应 GBufferA 的 RG 通道。
 *
 * @example
 * ```typescript
 * const n = [0, 1, 0]; // 朝上法线
 * const uv = encodeNormalOctahedral(n); // ≈ [0.5, 0.5]
 * ```
 *
 * @see {@link decodeNormalOctahedral} — 对应的解码函数
 */
function encodeNormalOctahedral(normal: [number, number, number]): [number, number]
```

## 类注释

```typescript
/**
 * 渲染 Pass 调度器，负责根据资源依赖关系对 Pass 进行拓扑排序并顺序执行。
 *
 * @remarks
 * - 调用 {@link compile} 后才能调用 {@link execute}，否则抛出 Error
 * - 单个 Scheduler 实例仅支持执行一次，执行后请创建新实例
 * - 非线程安全，不支持并发注册 Pass
 *
 * @example
 * ```typescript
 * const scheduler = new RenderPassScheduler();
 * scheduler.registerPass(gbufferPass);
 * scheduler.registerPass(lightingPass);
 * scheduler.compile();
 * await scheduler.execute(renderContext);
 * ```
 */
class RenderPassScheduler {
    /**
     * 已注册的 Pass 映射表，key 为 Pass 名称。
     * compile() 执行后此 Map 不允许修改。
     */
    private passRegistry: Map<string, IRenderPass> = new Map();

    /**
     * 注册一个渲染 Pass，声明其输入/输出资源依赖。
     *
     * @param pass - 要注册的 Pass 实例，name 属性必须全局唯一。
     * @throws {Error} 当同名 Pass 已存在，或 compile() 已调用后再注册时抛出。
     */
    registerPass(pass: IRenderPass): void { ... }
}
```

## 接口 / 类型注释

```typescript
/**
 * 渲染 Pass 的统一接口，所有自定义 Pass 须实现此接口接入调度器。
 *
 * @remarks
 * 实现类须保证 {@link execute} 的幂等性：相同上下文下多次调用结果一致。
 */
interface IRenderPass {
    /** Pass 的唯一标识名，用于 Frame Debugger 和日志显示 */
    readonly name: string;

    /**
     * 声明本 Pass 的输入/输出资源依赖，供调度器推导执行顺序。
     * @param builder - 资源依赖声明构建器
     */
    setup(builder: IRenderGraphBuilder): void;

    /**
     * 执行 Pass 的实际渲染逻辑，由调度器在正确时序下调用。
     * @param context - 当前帧渲染上下文（含 CommandEncoder 和帧参数）
     */
    execute(context: RenderContext): Promise<void>;
}

/**
 * GBuffer RT Slot 的逻辑分配，与 Shader 中的颜色输出绑定点对应。
 */
type GBufferSlot = {
    /** GBufferA：Base Color（RGB）+ 材质掩码（A） */
    baseColor: GPUTexture;
    /** GBufferB：Octahedral 法线（RG）+ 粗糙度（B）+ 金属度（A） */
    normalRoughness: GPUTexture;
    /** GBufferC：线性深度（R16F），单位为世界空间米 */
    linearDepth: GPUTexture;
};
```

## 枚举注释（TypeScript enum）

```typescript
/**
 * GPU 缓冲区的用途标志，影响内存分配策略和 API 访问权限。
 * 可按位组合：`BufferUsage.VERTEX | BufferUsage.COPY_DST`
 */
const enum BufferUsage {
    /** 顶点缓冲区，绑定为 vertex buffer slot */
    VERTEX = 0x1,
    /** 索引缓冲区，绑定为 index buffer */
    INDEX = 0x2,
    /** Uniform/Constant 缓冲区，CPU 每帧写入，GPU 只读 */
    UNIFORM = 0x4,
    /** UAV / Storage Buffer，GPU 可读写 */
    STORAGE = 0x8,
    /** 允许 CPU → GPU 数据上传（staging buffer 的目标端） */
    COPY_DST = 0x10,
}
```

## 内联注释规范

```typescript
// ---- 正确示范 ----

// Stencil = 0 表示天空盒像素，GBuffer 无有效数据，跳过光照计算
if (stencil === 0) continue;

// 使用位移代替乘法：slot * 4 → slot << 2，编译器通常会自动优化，
// 此处显式写出是为了传达"每个 slot 占 4 字节对齐"的设计约定
const offset = slot << 2;

// FIXME(leiMH): Safari 16 的 WebGPU 实现对 storage buffer 的 binding offset
// 要求 256 字节对齐（非标准），手动补齐绕过（Issue #512）
const alignedOffset = Math.ceil(rawOffset / 256) * 256;

// ---- 禁止示范 ----
i++;                  // i 加 1        ← 废话
return result;        // 返回结果      ← 废话
```

## 废弃 API 标注

```typescript
/**
 * @deprecated 自 v2.3.0 起废弃，请使用 {@link encodeNormalOctahedral} 代替。
 *   旧版实现使用球坐标编码，在极点附近存在精度问题（见 Issue #234）。
 *   计划在 v3.0.0 中移除。
 */
function encodeNormalSpherical(normal: Vec3): Vec2 { ... }
```
