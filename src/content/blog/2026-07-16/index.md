---
title: "线性代数可视化教学工具"
author: "王思成"
date: "Jul 16, 2026"
description: "从黑板到浏览器：用 Three.js 把线性代数「看见」"
latex: true
pdf: true
---

## 前端渲染引擎的选型

当我们决定把抽象的矩阵运算映射为可交互的三维几何时，渲染引擎的选择直接决定了最终的性能上限与开发体验。Three.js 作为 WebGL 的高层封装，提供了对几何体、材质、光照以及动画循环的统一抽象，同时保留了对着色器程序的细粒度控制。相比之下，MathBox2 虽然在数学可视化领域拥有更强的声明式语法，但其生态相对封闭且对自定义变换的扩展成本较高；p5.js 的 Canvas 2D 后端在三维场景下容易遇到性能瓶颈；而原生 SVG 则因 DOM 节点数量的线性增长而难以承载高密度的向量场可视化。综合考量后，我们最终选用 Three.js 配合 React 与 TypeScript 构建界面层，通过声明式组件管理场景对象，再由 Three.js 负责底层的 WebGL 指令提交。

## 数学库的精度与性能权衡

在浏览器环境中进行实时矩阵运算，需要同时兼顾数值稳定性和计算吞吐量。gl-matrix 以其零依赖、纯 TypedArray 实现而在性能测试中表现出色，尤其适合处理大量顶点数据的仿射变换；numeric.js 提供了更完备的特征值分解与奇异值分解算法，但其内部使用了大量普通 JavaScript 数组，导致内存分配与垃圾回收压力较大；ml-matrix 则在接口设计上更贴近 NumPy 风格，适合需要频繁进行矩阵分块与拼接的场景。我们最终采用混合策略：对动画循环中高频调用的平移、旋转、缩放使用 gl-matrix 进行 SIMD 友好的向量化计算，而在需要精确特征分解的模块中临时调用 ml-matrix，并将结果缓存为 Float32Array 以供 Three.js 直接消费。

## 轻量状态管理与 URL 同步

为了让用户能够通过链接直接分享特定的矩阵配置，我们将核心数学状态集中存储在 Zustand 创建的单一 store 中。store 的结构包含当前矩阵 `A`、基向量集合 `basis` 以及动画播放进度 `t`，所有交互组件均通过选择器订阅这些字段的变化。关键在于将 store 的序列化结果与浏览器 URL 的 `search` 参数双向绑定：当用户拖拽向量端点时，`setState` 触发 `history.replaceState`，把矩阵内容编码为形如 `?A=[[1,2],[3,4]]` 的字符串；反之，组件挂载时解析 URL 并初始化 store，从而实现无需后端即可持久化的分享机制。

## 线性组合动画的实现细节

线性组合的可视化核心在于对两个或多个向量按标量系数进行加权求和，并以平滑插值的方式呈现中间状态。代码层面，我们在每一帧的 `requestAnimationFrame` 回调中读取当前系数 `alpha` 与 `beta`，利用 gl-matrix 的 `vec3.scaleAndAdd` 计算目标位置，再通过球面线性插值 `slerp` 让箭头方向自然过渡。关键的代码片段如下：

```typescript
function animateLinearCombination(alpha: number, beta: number) {
  const v1 = vec3.fromValues(2, 0, 0);
  const v2 = vec3.fromValues(0, 3, 0);
  const result = vec3.create();
  vec3.scaleAndAdd(result, vec3.scale(vec3.create(), v1, alpha), v2, beta);
  arrowMesh.position.copy(result as any);
  arrowMesh.quaternion.slerp(targetQuat, 0.1);
  renderer.render(scene, camera);
}
```

这段代码首先把两个基向量硬编码为 `v1` 与 `v2`，随后通过 `scaleAndAdd` 在单次调用中完成加权求和，避免了中间临时对象的频繁分配。`slerp` 调用则保证箭头在方向变化时不会出现突兀的旋转跳变，从而让用户在拖动系数滑块时获得连续的视觉反馈。

## 矩阵作用过程的分步可视化

矩阵乘法在几何上的意义是对空间进行线性变换。为了让学生「看见」这一过程，我们把矩阵的每一列视为新基向量，并在动画中依次展示原基向量如何被映射到新位置。实现时，将矩阵 `A` 的列向量分别存入 `col0` 与 `col1`，再用两个独立的箭头对象分别执行从原基到新基的插值。代码片段如下：

```typescript
function animateMatrixAction(A: mat2d) {
  const col0 = vec2.fromValues(A[0], A[1]);
  const col1 = vec2.fromValues(A[2], A[3]);
  // 分别对两个列向量做插值并更新箭头
  interpolateArrow(arrow0, col0);
  interpolateArrow(arrow1, col1);
}
```

`interpolateArrow` 函数内部使用 `vec2.lerp` 逐步更新箭头的位置与方向，同时触发 `requestAnimationFrame` 形成连续动画。用户可以通过「分步播放」按钮逐列触发插值，从而在时间维度上拆解矩阵乘法的几何意义。

## 特征值轨迹的动态映射

当矩阵作用于平面时，特征向量方向上的伸缩由特征值 ` λ ` 控制。我们将 ` λ ` 的变化映射为椭圆的长短轴缩放，并通过滑块控件实时更新。核心逻辑是将当前 ` λ ` 作为缩放因子作用于单位圆，再利用 Three.js 的 `EllipseCurve` 生成新的几何体顶点。代码片段如下：

```typescript
function updateEigenEllipse(lambda: number) {
  const curve = new THREE.EllipseCurve(0, 0, lambda, 1, 0, 2 * Math.PI);
  const points = curve.getPoints(64);
  ellipseGeometry.setFromPoints(points);
  ellipseMesh.geometry = ellipseGeometry;
}
```

这里 `EllipseCurve` 的两个半轴参数分别对应 ` λ ` 与 `1`，当用户拖动滑块改变 ` λ ` 时，椭圆会立即重绘，从而直观展示特征值对几何形变的影响。

## 性能优化策略

在高帧率动画与大量几何体并存的场景中，性能瓶颈主要来自 CPU 到 GPU 的数据传输与 JavaScript 垃圾回收。我们的优化措施包括：将所有可复用的几何体（如箭头、坐标轴）创建一次后通过 `InstancedMesh` 批量绘制，避免重复构造 BufferGeometry；对矩阵乘法等重计算任务使用 `OffscreenCanvas` 配合 Web Worker 在后台线程完成，主线程仅负责把结果写回 Three.js 顶点缓冲；移动端交互则通过 `throttle` 函数限制 `pointermove` 事件的触发频率，防止因高频状态更新导致的界面卡顿。这些手段共同保证了在主流移动设备上仍能维持 60 FPS 的流畅体验。

## 状态与渲染的解耦

在 React 组件树中，我们通过自定义 Hook `useLinearAlgebraStore` 将数学状态与 Three.js 渲染循环彻底解耦。Hook 内部订阅 Zustand store 的变化，并把最新矩阵与向量数据注入到一个全局的 `sceneContext`，Three.js 的 `useFrame` 回调再从该上下文中读取数据进行渲染。这样的架构使得即使在热更新或组件重渲染时，Three.js 场景也不会丢失已有对象，动画循环也能持续运行。

通过以上技术选型与实现细节，我们在浏览器中构建了一个既数学严谨又交互流畅的线性代数可视化平台，为后续教学案例的落地提供了坚实的技术基础。
