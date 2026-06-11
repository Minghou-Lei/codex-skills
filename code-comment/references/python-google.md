# Python Google Style Docstring 注释规范

适用：`.py` 文件，兼容 Sphinx 自动文档生成与 pylint 检查。

覆盖底线与档位定义见 `../SKILL.md`：每个新增/修改函数至少档位 A（单行 docstring），
触发任一非平凡条件即档位 S（完整 Google Style）。本文件只规定格式与示例。

---

## 模块头注释

```python
"""渲染资源管理模块，负责 GPU 缓冲区的分配、复用与销毁。

本模块不直接调用图形 API，所有底层操作委托给 RHIBackend 抽象层。
线程模型：所有公开方法均须在主线程调用，内部使用锁保护共享状态。

典型用法::

    manager = BufferManager(backend=dx12_backend)
    vb = manager.allocate(size=4096, usage=BufferUsage.VERTEX)
    manager.release(vb)
"""
```

## 函数/方法注释（按档位）

### 档位 S：有非显然参数、约束或副作用 → 完整 Google Style

```python
def encode_normal_octahedron(normal: np.ndarray) -> np.ndarray:
    """将世界空间单位法线编码为 Octahedral 格式（压缩到 [0,1]² UV 空间）。

    使用 Octahedral 映射将球面法线压缩为二维向量，相比球坐标编码
    在极点附近精度更高。适合写入 GBuffer 的 RG 通道。

    Args:
        normal: 形状为 (3,) 或 (N, 3) 的 float32 数组，表示世界空间单位法线。
            必须已归一化（np.linalg.norm 约等于 1.0）。
            传入零向量时行为未定义。

    Returns:
        形状与输入匹配的 float32 数组，值域 [0.0, 1.0]，对应 GBuffer RG 通道。

    Raises:
        ValueError: 当输入形状不是 (3,) 或 (N, 3) 时抛出。

    Note:
        此函数是向量化实现，N > 10000 时比循环快约 40x。
        解码配套函数见 :func:`decode_normal_octahedron`。

    Example::

        n = np.array([0.0, 1.0, 0.0])  # 朝上法线
        uv = encode_normal_octahedron(n)
        # uv ≈ [0.5, 0.5]，映射到 UV 中心
    """
```

### 档位 A：平凡函数 → 单行 docstring（不允许裸函数）

```python
# ❌ 不允许：新增/修改的函数没有 docstring
def get_name(self) -> str:
    return self._name

# ✅ 字面职责之上能补的上下文（来源、稳定性、空值语义、调用时机）必须补上
def get_name(self) -> str:
    """材质名称，取自资产路径末段；资产热重载后保持稳定，可作缓存 key。"""
    return self._name
```

### 档位 A 升 S 的边界：签名简单但有单一关键约束 → 约束写进单行

```python
def set_max_retries(self, count: int) -> None:
    """设置最大重试次数；0 表示无限重试，必须在首次 connect() 前调用。"""
```

## 类注释

```python
class RenderPassScheduler:
    """渲染 Pass 调度器，管理 Pass 之间的依赖关系和执行顺序。

    根据 Pass 注册的输入/输出资源自动推导 DAG 拓扑，
    并按拓扑序执行，确保资源读写不发生冲突。

    Attributes:
        pass_registry: 已注册的 Pass 字典，key 为 Pass 名称。
        resource_graph: 资源依赖有向图，用于拓扑排序。
        _execution_order: 缓存的执行顺序列表，在 compile() 后有效。

    Note:
        非线程安全。compile() 之前调用 execute() 会抛出 RuntimeError。
        同一 Scheduler 实例不支持复用：执行完成后请创建新实例。
    """

    def __init__(self, max_passes: int = 256):
        """初始化调度器。

        Args:
            max_passes: 允许注册的最大 Pass 数量。超出时 register_pass() 抛出异常。
                默认值 256 是针对主渲染管线的经验值，离屏渲染可适当调低。
        """
```

## 属性和常量注释

```python
class GBufferLayout:
    #: GBufferA（RGBA8）：RGB 存 Base Color，A 存材质类型掩码（0=不透明，1=次表面）
    CHANNEL_BASE_COLOR = 0

    #: GBufferB（RGBA8）：RG 存 Octahedral 法线，B 存粗糙度，A 存金属度
    CHANNEL_NORMAL_ROUGHNESS = 1

    #: 最大支持的 MRT 数量，超出时降级为单 Pass 多次绘制
    MAX_MRT_COUNT: int = 8
```

## 内联注释规范

```python
# ---- 正确示范 ----

# rsqrt 替代 1/sqrt，在 AVX2 指令集下快约 3x，精度损失可忽略（< 1e-5）
inv_len = 1.0 / np.sqrt(np.sum(n * n, axis=-1, keepdims=True))

# 跳过 Stencil 为 0 的像素（天空区域无 GBuffer 数据，用默认环境光代替）
mask = stencil_buffer != 0

# FIXME(leiMH): np.einsum 在 batch_size > 4096 时内存峰值超 2GB，
# 已提 Issue #301，临时改用分块处理
for chunk in chunks(data, size=1024):
    process(chunk)

# ---- 禁止示范 ----
result = a + b  # 将 a 和 b 相加   ← 废话
return output   # 返回输出         ← 废话
```

### 行级锚点：短注释贴行尾，长解释放行上

```python
chunk_size = 1024  # 1024 行/块：实测内存峰值与吞吐的平衡点（讨论见 Issue #301）
type_id = flags & 0x0F  # 低 4 位 = 材质类型 ID，与 C++ 侧枚举严格同步

# 复合条件的领域含义放行上：仅重试"可恢复且未超时间预算"的请求
if err.retryable and elapsed < BUDGET_SECONDS:
    retry()
```

行尾复述语法是废话；行尾写值语义、出处、改动影响是规范要求的锚点。区别在信息增量。

## TODO 格式

```python
# TODO(username): 事项描述（Issue 编号）
# TODO(leiMH): 当输入包含 NaN 时未做保护，添加 np.nan_to_num 前置处理（#Issue-402）

# FIXME(username): Bug 描述 + 复现条件
# FIXME(leiMH): 在 Python 3.12 上 weakref 回调顺序变化导致此处偶现崩溃
```

## 类型标注与注释的配合

```python
def load_texture(
    path: str,                        # 绝对路径或相对于资产根目录的路径
    srgb: bool = True,                # True 表示 sRGB 输入，解码时做 gamma 矫正
    generate_mips: bool = False,      # 是否自动生成 mipmap（开销较高，离线 Cook 时使用）
    max_mip_levels: int = 0,          # 0 表示自动计算最大 mip 层数
) -> Optional["TextureHandle"]:
    """加载纹理并返回 GPU 资源句柄。

    ...（docstring 正文）
    """
```

## 脚本/工具文件的 `__main__` 注释

```python
if __name__ == "__main__":
    # 仅在直接执行时运行，import 时不执行。
    # 用途：快速验证编码函数的正确性，不应作为生产入口。
    test_normal = np.array([0.0, 0.0, 1.0])
    print(encode_normal_octahedron(test_normal))  # 期望输出: [0.5, 0.5]
```
