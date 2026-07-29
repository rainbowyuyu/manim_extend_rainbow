# speed_rate_fuc — 缓动曲线说明

`yty_manim.disposition.speed_rate_fuc` 提供可直接传给 Manim `rate_func=` 的缓动函数：  
输入时间进度 \(t \in [0,1]\)，输出动画进度 \(f(t)\)。

源码：[speed_rate_fuc.py](speed_rate_fuc.py)  
示例场景：[examples/speed_rate_demo.py](../../examples/speed_rate_demo.py)  
批量渲染：`python examples/render_speed_rate_gifs.py`  
示例 GIF 目录：[yty_manim/examples/speed_rate/](../examples/speed_rate/)

## 用法

```python
from yty_manim.disposition.speed_rate_fuc import (
    ease_in_out_cubic,
    slow_then_fast,
    rate_presets,
)

self.play(mob.animate.shift(RIGHT), rate_func=ease_in_out_cubic)
self.play(tracker.animate.set_value(1), rate_func=slow_then_fast)
self.play(..., rate_func=rate_presets["ease_out_back"])
```

每个 GIF：上方为 \(f(t)\) 曲线，下方橙点沿轨道按进度移动（动画时间轴为线性，便于观察曲线本身）。

---

## 基础 / 平滑

### `linear` — 匀速

![linear](../examples/speed_rate/linear.gif)

### `smoothstep` — Hermite 三次平滑

![smoothstep](../examples/speed_rate/smoothstep.gif)

### `smootherstep` — Perlin 五次平滑

![smootherstep](../examples/speed_rate/smootherstep.gif)

### `smooth` — smootherstep 别名（常用默认）

![smooth](../examples/speed_rate/smooth.gif)

### `double_smooth` — 两次 smootherstep，更「黏」

![double_smooth](../examples/speed_rate/double_smooth.gif)

### `lingering` — 两端慢、中间相对快

![lingering](../examples/speed_rate/lingering.gif)

---

## 镜头常用别名

### `slow_then_fast` — 先慢后快（= ease-in cubic）

![slow_then_fast](../examples/speed_rate/slow_then_fast.gif)

### `fast_then_slow` — 先快后慢（= ease-out cubic）

![fast_then_slow](../examples/speed_rate/fast_then_slow.gif)

### `rush_into` — 后段加速冲入

![rush_into](../examples/speed_rate/rush_into.gif)

### `rush_from` — 前段冲出再减速

![rush_from](../examples/speed_rate/rush_from.gif)

---

## 往返 / 抖动

### `there_and_back` — 去再回 \(0\to1\to0\)

![there_and_back](../examples/speed_rate/there_and_back.gif)

### `there_and_back_with_pause` — 去—停—回

![there_and_back_with_pause](../examples/speed_rate/there_and_back_with_pause.gif)

### `wiggle` — 来回晃动后落定

![wiggle](../examples/speed_rate/wiggle.gif)

工厂函数（返回新的 `rate_func`）：`make_reverse`、`make_there_and_back`、`make_there_and_back_with_pause`、`make_squish`、`make_compose`、`make_wiggle`。

---

## 多项式：Quad / Cubic / Quart / Quint

### Quad

#### `ease_in_quad`

![ease_in_quad](../examples/speed_rate/ease_in_quad.gif)

#### `ease_out_quad`

![ease_out_quad](../examples/speed_rate/ease_out_quad.gif)

#### `ease_in_out_quad`

![ease_in_out_quad](../examples/speed_rate/ease_in_out_quad.gif)

### Cubic

#### `ease_in_cubic`

![ease_in_cubic](../examples/speed_rate/ease_in_cubic.gif)

#### `ease_out_cubic`

![ease_out_cubic](../examples/speed_rate/ease_out_cubic.gif)

#### `ease_in_out_cubic`

![ease_in_out_cubic](../examples/speed_rate/ease_in_out_cubic.gif)

### Quart

#### `ease_in_quart`

![ease_in_quart](../examples/speed_rate/ease_in_quart.gif)

#### `ease_out_quart`

![ease_out_quart](../examples/speed_rate/ease_out_quart.gif)

#### `ease_in_out_quart`

![ease_in_out_quart](../examples/speed_rate/ease_in_out_quart.gif)

### Quint

#### `ease_in_quint`

![ease_in_quint](../examples/speed_rate/ease_in_quint.gif)

#### `ease_out_quint`

![ease_out_quint](../examples/speed_rate/ease_out_quint.gif)

#### `ease_in_out_quint`

![ease_in_out_quint](../examples/speed_rate/ease_in_out_quint.gif)

可调幂次：`power_ease(t, p=2.0, mode="in_out")`。

---

## Sine / Expo / Circ

### Sine

#### `ease_in_sine`

![ease_in_sine](../examples/speed_rate/ease_in_sine.gif)

#### `ease_out_sine`

![ease_out_sine](../examples/speed_rate/ease_out_sine.gif)

#### `ease_in_out_sine`

![ease_in_out_sine](../examples/speed_rate/ease_in_out_sine.gif)

### Expo

#### `ease_in_expo`

![ease_in_expo](../examples/speed_rate/ease_in_expo.gif)

#### `ease_out_expo`

![ease_out_expo](../examples/speed_rate/ease_out_expo.gif)

#### `ease_in_out_expo`

![ease_in_out_expo](../examples/speed_rate/ease_in_out_expo.gif)

### Circ

#### `ease_in_circ`

![ease_in_circ](../examples/speed_rate/ease_in_circ.gif)

#### `ease_out_circ`

![ease_out_circ](../examples/speed_rate/ease_out_circ.gif)

#### `ease_in_out_circ`

![ease_in_out_circ](../examples/speed_rate/ease_in_out_circ.gif)

额外：`sigmoid(t, k=10)`、`exponential_decay(t, k=4)`（可带参数，直接作 `rate_func` 时用默认值）。

---

## Back / Elastic / Bounce

带过冲或弹跳，\(f(t)\) 可能短暂超出 \([0,1]\)。

### Back

#### `ease_in_back`

![ease_in_back](../examples/speed_rate/ease_in_back.gif)

#### `ease_out_back`

![ease_out_back](../examples/speed_rate/ease_out_back.gif)

#### `ease_in_out_back`

![ease_in_out_back](../examples/speed_rate/ease_in_out_back.gif)

### Elastic

#### `ease_in_elastic`

![ease_in_elastic](../examples/speed_rate/ease_in_elastic.gif)

#### `ease_out_elastic`

![ease_out_elastic](../examples/speed_rate/ease_out_elastic.gif)

#### `ease_in_out_elastic`

![ease_in_out_elastic](../examples/speed_rate/ease_in_out_elastic.gif)

### Bounce

#### `ease_in_bounce`

![ease_in_bounce](../examples/speed_rate/ease_in_bounce.gif)

#### `ease_out_bounce`

![ease_out_bounce](../examples/speed_rate/ease_out_bounce.gif)

#### `ease_in_out_bounce`

![ease_in_out_bounce](../examples/speed_rate/ease_in_out_bounce.gif)

---

## 其它工具

- `split_ease(t, lower, upper, split_line)`：两段缓动拼接  
- `split_speed(i, lower_speed, upper_speed, split_line)`：按位置选标量速度（**不是** `rate_func`）  
- `rate_presets`：`dict[str, Callable]`，按名取全部预设  

---

## 选用建议

| 场景 | 推荐 |
|------|------|
| 标题 / UI 入场 | `ease_out_cubic`、`fast_then_slow`、`smooth` |
| 冲击波 / 数值爬升 | `slow_then_fast`、`ease_in_cubic`、`ease_in_expo` |
| 强调闪一下 | `there_and_back`、`there_and_back_with_pause` |
| 落地弹跳感 | `ease_out_bounce`、`ease_out_back` |
| 弹性回弹 | `ease_out_elastic` |
| 匀速对照 | `linear` |
