# HLSL / GLSL / USF Shader 注释规范

适用：`.hlsl` `.glsl` `.usf` `.ush`（含 UE 的 Unreal Shader Format）。

---

## Shader 文件头注释（必须）

```hlsl
//=============================================================================
// DeferredLighting.hlsl
// 延迟光照 Pass —— 从 GBuffer 重建光照，输出 HDR SceneColor
//
// 输入  RT:
//   GBufferA (RGBA8)  - Base Color(RGB) + 材质掩码(A)
//   GBufferB (RGBA8)  - Octahedral法线(RG) + 粗糙度(B) + 金属度(A)
//   SceneDepth (D24S8) - 硬件深度 + Stencil
//
// 输出  RT:
//   SceneColor (R11G11B10F) - 线性空间 HDR 颜色（不含 Tonemapping）
//
// Shader Model: SM 5.0+
// 作者: MinghouLei  日期: 2025-01-15
//=============================================================================
```

## 函数注释（Doxygen 兼容格式）

```hlsl
/**
 * 从 GBufferB 的 RG 通道解码 Octahedral 编码法线，还原为世界空间单位向量。
 *
 * @param  encodedRG  GBufferB 采样得到的 RG 值，值域 [0, 1]
 * @return 世界空间单位法线（length == 1.0），指向相机方向的半球为正
 *
 * @note   配套编码函数：EncodeNormalOctahedral()（位于 GBufferEncode.hlsl）
 *         解码精度：法线方向误差 < 0.01°（10位精度等效）
 */
float3 DecodeNormalFromGBuffer(float2 encodedRG)
{
    // 从 [0,1] 映射到 [-1,1]，还原 Octahedral 空间坐标
    float2 f = encodedRG * 2.0 - 1.0;

    // 利用 L1 范数展开：z 分量由 xy 确定，无需额外存储
    float3 n = float3(f.x, f.y, 1.0 - abs(f.x) - abs(f.y));

    // 负半球修正：将折叠的角点映射回正确位置
    float t = saturate(-n.z);
    n.xy += float2(n.x >= 0 ? -t : t, n.y >= 0 ? -t : t);

    return normalize(n);
}
```

## 结构体注释

```hlsl
/**
 * GBuffer 数据包，聚合从多张 RT 采样得到的表面属性。
 * 由 UnpackGBuffer() 填充，传递给各光照模型计算函数。
 */
struct FGBufferData
{
    float3 BaseColor;       // 漫反射基础颜色，线性空间，值域 [0,1]
    float3 WorldNormal;     // 世界空间单位法线（已解码，length == 1.0）
    float  Roughness;       // 感知粗糙度，值域 [0.05, 1.0]（避免镜面奇异）
    float  Metallic;        // 金属度，0=非金属，1=全金属，通常为二值
    uint   ShadingModel;    // 着色模型 ID：0=Lit，1=Unlit，2=Subsurface
};
```

## Constant Buffer / cbuffer 注释

```hlsl
/**
 * 每帧更新一次的相机和场景参数，由 CPU 在 BeginFrame 阶段提交。
 * Slot: b0（对应 RootSignature 中的第 0 个 CBV）
 */
cbuffer FrameConstants : register(b0)
{
    float4x4 ViewMatrix;        // 世界空间 → 视图空间变换矩阵
    float4x4 ProjectionMatrix;  // 视图空间 → 裁剪空间投影矩阵（左手坐标系，DX 约定）
    float4x4 InvViewMatrix;     // ViewMatrix 的逆矩阵，用于从深度重建世界坐标
    float3   CameraWorldPos;    // 摄像机世界坐标，用于计算视线方向
    float    _Padding0;         // 对齐到 16 字节边界（HLSL cbuffer 打包规则要求）
    float    NearClipPlane;     // 近裁剪面距离（米），用于线性深度重建
    float    FarClipPlane;      // 远裁剪面距离（米）
    float2   ScreenSize;        // 渲染目标分辨率 (width, height)，像素单位
};
```

## 宏和 #define 注释

```hlsl
// GBuffer MRT Slot 索引（与 RenderTarget 绑定顺序严格对应，修改须同步更新 C++ 侧）
#define GBUFFER_SLOT_BASECOLOR      0
#define GBUFFER_SLOT_NORMAL         1
#define GBUFFER_SLOT_DEPTH          2

// 最小粗糙度钳位值：防止镜面高光出现数值奇异（GGX NDF 在 roughness→0 时趋于 Dirac delta）
#define MIN_PERCEPTUAL_ROUGHNESS    0.045f

// 光照计算中的 Epsilon：避免除零错误，值选取参考 UE4 PBR 实现
#define FLOAT_EPSILON               1e-5f
```

## 算法步骤注释（复杂 Shader 的分步说明）

```hlsl
float4 PS_DeferredLighting(VSOutput input) : SV_Target
{
    // ---------- 1. 采样 GBuffer ----------
    float4 gbufferA = GBufferA.Sample(PointSampler, input.UV);
    float4 gbufferB = GBufferB.Sample(PointSampler, input.UV);

    // ---------- 2. 从深度重建世界坐标 ----------
    // 将 NDC 坐标 + 硬件深度逆投影到世界空间，避免存储额外的 WorldPos RT
    float  hwDepth     = SceneDepth.Sample(PointSampler, input.UV).r;
    float3 worldPos    = ReconstructWorldPosition(input.UV, hwDepth, InvViewProjMatrix);

    // ---------- 3. 解包 GBuffer 数据 ----------
    FGBufferData gbuffer;
    gbuffer.BaseColor   = gbufferA.rgb;
    gbuffer.WorldNormal = DecodeNormalFromGBuffer(gbufferB.rg);
    gbuffer.Roughness   = gbufferB.b;
    gbuffer.Metallic    = gbufferB.a;

    // ---------- 4. 执行 PBR 光照计算 ----------
    // 此处仅计算直接光照；间接光照（IBL）由后续 Pass 叠加
    float3 radiance = ComputeDirectLighting(gbuffer, worldPos, CameraWorldPos);

    // ---------- 5. 输出（线性空间，不做 Tonemap）----------
    return float4(radiance, 1.0);
}
```

## WORKAROUND / 驱动兼容注释

```hlsl
// WORKAROUND(leiMH): NVIDIA 驱动 535.xx 在 UAV + SRV 同帧访问时存在 race condition。
// 强制插入 DeviceMemoryBarrier 使资源状态同步（NVIDIA 官方确认为驱动 bug，535.154 修复）。
// 待项目最低驱动要求提升至 535.154 后移除。
DeviceMemoryBarrier();

// WORKAROUND(leiMH): AMD GCN 架构（RX 5xx 系列）不支持 64位原子操作，
// 降级为两次 32位原子操拟。精度损失在可接受范围内（误差 < 1 ULP）。
#if defined(GCN_ARCHITECTURE)
    InterlockedAdd(counter_lo, 1);
#else
    InterlockedAdd64(counter, 1);
#endif
```
