# rainbow_yu manim_extend.disposition.speed_rate_func 🐋✨
# Manim rate_func：t ∈ [0, 1] → 进度 ∈ [0, 1]

from __future__ import annotations

import math
from typing import Callable

RateFunc = Callable[[float], float]


# ── 基础 / 工具 ──────────────────────────────────────────────


def clamp01(t: float) -> float:
    return 0.0 if t < 0.0 else 1.0 if t > 1.0 else float(t)


def identity(t: float) -> float:
    """线性：匀速。"""
    return clamp01(t)


linear = identity


def make_reverse(rf: RateFunc) -> RateFunc:
    """时间反向工厂：先快后慢 ↔ 先慢后快。"""

    def _rev(t: float) -> float:
        return 1.0 - rf(1.0 - clamp01(t))

    return _rev


def there_and_back(t: float) -> float:
    """去再回：0→1→0，适合强调闪一下。可直接作 rate_func。"""
    t = clamp01(t)
    if t < 0.5:
        return 2.0 * t
    return 2.0 * (1.0 - t)


def make_there_and_back(rf: RateFunc = identity) -> RateFunc:
    """带内层缓动的去再回。"""

    def _tab(t: float) -> float:
        t = clamp01(t)
        if t < 0.5:
            return rf(2.0 * t)
        return rf(2.0 * (1.0 - t))

    return _tab


def there_and_back_with_pause(t: float) -> float:
    """去—停—回（中间停约 1/3）。可直接作 rate_func。"""
    return make_there_and_back_with_pause()(t)


def make_there_and_back_with_pause(
    rf: RateFunc = identity,
    pause: float = 1 / 3,
) -> RateFunc:
    """去—停—回工厂；pause 为中间停留占比。"""
    pause = max(0.0, min(0.9, float(pause)))
    go = (1.0 - pause) / 2.0

    def _tabp(t: float) -> float:
        t = clamp01(t)
        if t < go:
            return rf(t / go)
        if t < go + pause:
            return 1.0
        return rf((1.0 - t) / go)

    return _tabp


def make_squish(rf: RateFunc, a: float = 0.0, b: float = 1.0) -> RateFunc:
    """把缓动压缩到区间 [a, b]；区间外钳制。"""
    a, b = float(a), float(b)
    span = max(b - a, 1e-9)

    def _sq(t: float) -> float:
        t = clamp01(t)
        if t <= a:
            return 0.0
        if t >= b:
            return 1.0
        return rf((t - a) / span)

    return _sq


def make_compose(first: RateFunc, second: RateFunc, split: float = 0.5) -> RateFunc:
    """两段拼接工厂：前半用 first，后半用 second。"""
    split = clamp01(split)
    split = 0.5 if split <= 0.0 or split >= 1.0 else split

    def _cmp(t: float) -> float:
        t = clamp01(t)
        if t < split:
            return first(t / split) * split
        return split + second((t - split) / (1.0 - split)) * (1.0 - split)

    return _cmp


def wiggle(t: float) -> float:
    """来回晃 2 次后落定。可直接作 rate_func。"""
    return make_wiggle(2)(t)


def make_wiggle(n: int = 2, rf: RateFunc = identity) -> RateFunc:
    """来回晃 n 次工厂。"""
    n = max(1, int(n))

    def _wg(t: float) -> float:
        t = clamp01(t)
        return rf(t) * math.sin(n * math.pi * t)

    return _wg


# ── 多项式 ───────────────────────────────────────────────────


def ease_in_quad(t: float) -> float:
    t = clamp01(t)
    return t * t


def ease_out_quad(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in_out_quad(t: float) -> float:
    t = clamp01(t)
    return 2.0 * t * t if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def ease_in_cubic(t: float) -> float:
    t = clamp01(t)
    return t ** 3


def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 4.0 * t ** 3 if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_in_quart(t: float) -> float:
    t = clamp01(t)
    return t ** 4


def ease_out_quart(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 4


def ease_in_out_quart(t: float) -> float:
    t = clamp01(t)
    return 8.0 * t ** 4 if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 4 / 2.0


def ease_in_quint(t: float) -> float:
    t = clamp01(t)
    return t ** 5


def ease_out_quint(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 5


def ease_in_out_quint(t: float) -> float:
    t = clamp01(t)
    return 16.0 * t ** 5 if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 5 / 2.0


# ── 三角 / 指数 / 圆形 ───────────────────────────────────────


def ease_in_sine(t: float) -> float:
    t = clamp01(t)
    return 1.0 - math.cos(t * math.pi / 2.0)


def ease_out_sine(t: float) -> float:
    t = clamp01(t)
    return math.sin(t * math.pi / 2.0)


def ease_in_out_sine(t: float) -> float:
    t = clamp01(t)
    return -(math.cos(math.pi * t) - 1.0) / 2.0


def ease_in_expo(t: float) -> float:
    t = clamp01(t)
    return 0.0 if t == 0.0 else 2.0 ** (10.0 * t - 10.0)


def ease_out_expo(t: float) -> float:
    t = clamp01(t)
    return 1.0 if t == 1.0 else 1.0 - 2.0 ** (-10.0 * t)


def ease_in_out_expo(t: float) -> float:
    t = clamp01(t)
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return 2.0 ** (20.0 * t - 10.0) / 2.0
    return (2.0 - 2.0 ** (-20.0 * t + 10.0)) / 2.0


def ease_in_circ(t: float) -> float:
    t = clamp01(t)
    return 1.0 - math.sqrt(1.0 - t * t)


def ease_out_circ(t: float) -> float:
    t = clamp01(t)
    return math.sqrt(1.0 - (t - 1.0) ** 2)


def ease_in_out_circ(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return (1.0 - math.sqrt(1.0 - (2.0 * t) ** 2)) / 2.0
    return (math.sqrt(1.0 - (-2.0 * t + 2.0) ** 2) + 1.0) / 2.0


# ── Smoothstep 族 ────────────────────────────────────────────


def smoothstep(t: float) -> float:
    """Hermite 平滑步进（比 sine 略硬）。"""
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    """Ken Perlin 五次平滑步进。"""
    t = clamp01(t)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


smooth = smootherstep  # 常用别名，接近 manim.smooth


# ── Back / Elastic / Bounce ──────────────────────────────────


def ease_in_back(t: float, s: float = 1.70158) -> float:
    t = clamp01(t)
    return (s + 1.0) * t ** 3 - s * t * t


def ease_out_back(t: float, s: float = 1.70158) -> float:
    t = clamp01(t)
    u = t - 1.0
    return 1.0 + (s + 1.0) * u ** 3 + s * u * u


def ease_in_out_back(t: float, s: float = 1.70158) -> float:
    t = clamp01(t)
    c = s * 1.525
    if t < 0.5:
        return ((2.0 * t) ** 2 * ((c + 1.0) * 2.0 * t - c)) / 2.0
    return ((2.0 * t - 2.0) ** 2 * ((c + 1.0) * (2.0 * t - 2.0) + c) + 2.0) / 2.0


def ease_in_elastic(t: float) -> float:
    t = clamp01(t)
    if t == 0.0 or t == 1.0:
        return t
    return -(2.0 ** (10.0 * t - 10.0)) * math.sin((t * 10.0 - 10.75) * (2.0 * math.pi) / 3.0)


def ease_out_elastic(t: float) -> float:
    t = clamp01(t)
    if t == 0.0 or t == 1.0:
        return t
    return 2.0 ** (-10.0 * t) * math.sin((t * 10.0 - 0.75) * (2.0 * math.pi) / 3.0) + 1.0


def ease_in_out_elastic(t: float) -> float:
    t = clamp01(t)
    if t == 0.0 or t == 1.0:
        return t
    if t < 0.5:
        return -(
            2.0 ** (20.0 * t - 10.0)
            * math.sin((20.0 * t - 11.125) * (2.0 * math.pi) / 4.5)
        ) / 2.0
    return (
        2.0 ** (-20.0 * t + 10.0)
        * math.sin((20.0 * t - 11.125) * (2.0 * math.pi) / 4.5)
    ) / 2.0 + 1.0


def _bounce_out(t: float) -> float:
    n1, d1 = 7.5625, 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    if t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def ease_out_bounce(t: float) -> float:
    return _bounce_out(clamp01(t))


def ease_in_bounce(t: float) -> float:
    return 1.0 - _bounce_out(1.0 - clamp01(t))


def ease_in_out_bounce(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return (1.0 - _bounce_out(1.0 - 2.0 * t)) / 2.0
    return (1.0 + _bounce_out(2.0 * t - 1.0)) / 2.0


# ── 教学 / 镜头常用 ──────────────────────────────────────────


def slow_then_fast(t: float) -> float:
    """先慢后快（ease-in cubic）。适合冲击波起步、数值爬升。"""
    return ease_in_cubic(t)


def fast_then_slow(t: float) -> float:
    """先快后慢（ease-out cubic）。适合落地、标题入场。"""
    return ease_out_cubic(t)


def rush_into(t: float) -> float:
    """后段加速冲入（二次）。"""
    return ease_in_quad(t)


def rush_from(t: float) -> float:
    """前段冲出再减速。"""
    return ease_out_quad(t)


def lingering(t: float) -> float:
    """两端徘徊、中段较快。"""
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def double_smooth(t: float) -> float:
    """两次 smootherstep，更「黏」。"""
    return smootherstep(smootherstep(t))


def exponential_decay(t: float, k: float = 4.0) -> float:
    """指数衰减趋近 1：适合余震、淡出尾巴。"""
    t = clamp01(t)
    k = max(1e-6, float(k))
    return 1.0 - math.exp(-k * t)


def sigmoid(t: float, k: float = 10.0) -> float:
    """S 形：中段陡、两端平。k 越大越陡。"""
    t = clamp01(t)
    k = float(k)

    def _sig(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-k * (x - 0.5)))

    s0, s1 = _sig(0.0), _sig(1.0)
    return (_sig(t) - s0) / (s1 - s0)


def power_ease(t: float, p: float = 2.0, mode: str = "in_out") -> float:
    """可调幂次缓动。mode: in / out / in_out。"""
    t = clamp01(t)
    p = max(1e-6, float(p))
    mode = mode.lower()
    if mode == "in":
        return t ** p
    if mode == "out":
        return 1.0 - (1.0 - t) ** p
    if t < 0.5:
        return 0.5 * (2.0 * t) ** p
    return 1.0 - 0.5 * (2.0 * (1.0 - t)) ** p


def split_ease(
    t: float,
    lower: RateFunc = ease_in_cubic,
    upper: RateFunc = ease_out_cubic,
    split_line: float = 0.5,
) -> float:
    """分界缓动：前半用 lower，后半用 upper，在 split_line 处连续拼进度。"""
    return make_compose(lower, upper, split_line)(t)


def split_speed(
    i,
    lower_speed,
    upper_speed,
    split_line,
):
    """
    分界线速度（非 rate_func；按位置选标量速度）。

    :param i: 位置
    :param lower_speed: 较慢的速度
    :param upper_speed: 较快的速度
    :param split_line: 分界线
    :return: speed
    """
    return lower_speed if i <= split_line else upper_speed


# ── 预设字典（便于 Scene 里按名取用）──────────────────────────

rate_presets: dict[str, RateFunc] = {
    "linear": linear,
    "smooth": smooth,
    "smoothstep": smoothstep,
    "smootherstep": smootherstep,
    "slow_then_fast": slow_then_fast,
    "fast_then_slow": fast_then_slow,
    "rush_into": rush_into,
    "rush_from": rush_from,
    "lingering": lingering,
    "double_smooth": double_smooth,
    "there_and_back": there_and_back,
    "there_and_back_with_pause": there_and_back_with_pause,
    "wiggle": wiggle,
    "ease_in_quad": ease_in_quad,
    "ease_out_quad": ease_out_quad,
    "ease_in_out_quad": ease_in_out_quad,
    "ease_in_cubic": ease_in_cubic,
    "ease_out_cubic": ease_out_cubic,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_in_quart": ease_in_quart,
    "ease_out_quart": ease_out_quart,
    "ease_in_out_quart": ease_in_out_quart,
    "ease_in_quint": ease_in_quint,
    "ease_out_quint": ease_out_quint,
    "ease_in_out_quint": ease_in_out_quint,
    "ease_in_sine": ease_in_sine,
    "ease_out_sine": ease_out_sine,
    "ease_in_out_sine": ease_in_out_sine,
    "ease_in_expo": ease_in_expo,
    "ease_out_expo": ease_out_expo,
    "ease_in_out_expo": ease_in_out_expo,
    "ease_in_circ": ease_in_circ,
    "ease_out_circ": ease_out_circ,
    "ease_in_out_circ": ease_in_out_circ,
    "ease_in_back": ease_in_back,
    "ease_out_back": ease_out_back,
    "ease_in_out_back": ease_in_out_back,
    "ease_in_elastic": ease_in_elastic,
    "ease_out_elastic": ease_out_elastic,
    "ease_in_out_elastic": ease_in_out_elastic,
    "ease_in_bounce": ease_in_bounce,
    "ease_out_bounce": ease_out_bounce,
    "ease_in_out_bounce": ease_in_out_bounce,
}
