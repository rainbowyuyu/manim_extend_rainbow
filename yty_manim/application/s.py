# rainbow_yu manim_extend.basic_unit.calculus_step 🐋✨
# 微积分分步可视化演示

from manim import *
import numpy as np
from typing import Callable, List, Tuple, Union


class CalculusStep(VGroup):
    """
    微积分分步可视化演示，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 常用于微积分概念的教学演示，包括导数、积分的分步展示
    - 支持函数图像绘制、切线展示、黎曼和可视化等
    - 使用 :method:`show_derivative_steps` 展示导数计算过程
    - 使用 :method:`show_integral_steps` 展示积分计算过程
    - 使用 :method:`animate_riemann_sum` 演示黎曼和的收敛过程

    Examples
    --------

    导数分步演示:

    >>> class DerivativeDemo(Scene):
    >>>     def construct(self):
    >>>         func = lambda x: x**2
    >>>         calc_demo = CalculusStep(func, x_range=[-3, 3])
    >>>         self.add(calc_demo)
    >>>         for step in calc_demo.show_derivative_steps(x_point=1):
    >>>             self.play(*step)
    >>>             self.wait(1)

    积分分步演示:

    >>> class IntegralDemo(Scene):
    >>>     def construct(self):
    >>>         func = lambda x: x**2
    >>>         calc_demo = CalculusStep(func, x_range=[0, 2])
    >>>         self.add(calc_demo)
    >>>         for step in calc_demo.show_integral_steps(n_rectangles=8):
    >>>             self.play(*step)
    >>>             self.wait(1)

    """

    __version__: str = "1.0.0"

    def __init__(
            self,
            function: Callable[[float], float],
            x_range: List[float] = [-3, 3],
            y_range: List[float] = [-2, 4],
            axes_config: dict = None,
            function_color: str = BLUE,
            derivative_color: str = RED,
            integral_color: str = GREEN,
            **kwargs
    ):
        super().__init__()

        self.function = function
        self.x_range = x_range
        self.y_range = y_range
        self.function_color = function_color
        self.derivative_color = derivative_color
        self.integral_color = integral_color

        # 默认坐标轴配置
        if axes_config is None:
            axes_config = {
                "x_range": [x_range[0], x_range[1], 0.5],
                "y_range": [y_range[0], y_range[1], 0.5],
                "x_length": 10,
                "y_length": 6,
                "axis_config": {"color": WHITE},
                "x_axis_config": {"numbers_to_include": np.arange(x_range[0], x_range[1] + 1, 1)},
                "y_axis_config": {"numbers_to_include": np.arange(y_range[0], y_range[1] + 1, 1)},
            }

        self.axes = Axes(**axes_config)
        self.function_graph = self.axes.plot(self.function, color=self.function_color)

        # 步骤标题和公式展示区域
        self.step_title = Text("", font_size=24).to_edge(UP)
        self.formula_display = MathTex("").to_edge(DOWN)

        self.add(self.axes, self.function_graph, self.step_title, self.formula_display)

        # 动画元素存储
        self.current_elements = VGroup()
        self.step_counter = 0

    def _numerical_derivative(self, x: float, h: float = 0.001) -> float:
        """数值计算导数"""
        return (self.function(x + h) - self.function(x - h)) / (2 * h)

    def _update_step_info(self, title: str, formula: str):
        """更新步骤信息"""
        self.step_title.become(Text(title, font_size=24).to_edge(UP))
        self.formula_display.become(MathTex(formula).to_edge(DOWN))

    def show_derivative_steps(
            self,
            x_point: float = 1,
            h_values: List[float] = [1.0, 0.5, 0.1, 0.01]
    ) -> List[List]:
        """
        展示导数计算的分步过程
        :param x_point: 求导点
        :param h_values: h值的序列，展示极限过程
        :return: 动画步骤列表
        """
        steps = []

        # 步骤1: 显示原函数和求导点
        point_dot = Dot(self.axes.coords_to_point(x_point, self.function(x_point)),
                        color=YELLOW, radius=0.08)
        self.current_elements.add(point_dot)

        steps.append([
            self._create_step_animation(
                "步骤1: 选择求导点",
                f"f(x) = x^2, \\text{{at }} x = {x_point} \\text{{ dx}}",
                [Create(point_dot)]
            )
        ])

        # 步骤2-5: 展示不同h值下的割线
        for i, h in enumerate(h_values):
            x1, x2 = x_point, x_point + h
            y1, y2 = self.function(x1), self.function(x2)

            # 创建割线
            secant_line = self.axes.plot(
                lambda x: y1 + (y2 - y1) * (x - x1) / (x2 - x1),
                x_range=[x1 - 0.5, x2 + 0.5],
                color=self.derivative_color
            )

            # 创建h区间标记
            h_bracket = self._create_h_bracket(x_point, h)

            slope = (y2 - y1) / h

            if i > 0:
                # 移除上一个割线
                steps.append([
                    self._create_step_animation(
                        f"步骤{i + 2}: h = {h}",
                        f"\\text{{rate}} = \\frac{{f({x_point}+{h}) - f({x_point})}}{{{h}}} = {slope:.3f}",
                        [FadeOut(self.current_elements[-2:]),
                         Create(secant_line), Create(h_bracket)]
                    )
                ])
            else:
                steps.append([
                    self._create_step_animation(
                        f"步骤{i + 2}: h = {h}",
                        f"\\text{{rate}} = \\frac{{f({x_point}+{h}) - f({x_point})}}{{{h}}} = {slope:.3f}",
                        [Create(secant_line), Create(h_bracket)]
                    )
                ])

            self.current_elements.add(secant_line, h_bracket)

        # 最终步骤: 显示切线
        derivative_value = self._numerical_derivative(x_point)
        tangent_line = self.axes.plot(
            lambda x: self.function(x_point) + derivative_value * (x - x_point),
            x_range=[x_point - 1, x_point + 1],
            color=GOLD,
            stroke_width=4
        )

        steps.append([
            self._create_step_animation(
                "最终结果: 切线",
                f"f'({x_point}) = \\lim_{{h \\to 0}} \\frac{{f({x_point}+h) - f({x_point})}}{{h}} = {derivative_value:.3f}",
                [FadeOut(self.current_elements[-2:]), Create(tangent_line)]
            )
        ])

        self.current_elements.add(tangent_line)
        return steps

    def show_integral_steps(
            self,
            a: float = None,
            b: float = None,
            n_rectangles: int = 4,
            method: str = "riemann"
    ) -> List[List]:
        """
        展示积分计算的分步过程
        :param a: 积分下限
        :param b: 积分上限
        :param n_rectangles: 矩形数量
        :param method: 积分方法 ("riemann", "trapezoid")
        :return: 动画步骤列表
        """
        if a is None:
            a = self.x_range[0]
        if b is None:
            b = self.x_range[1]

        steps = []

        # 步骤1: 显示积分区域
        area = self.axes.get_area(self.function_graph, x_range=[a, b], color=self.integral_color, opacity=0.3)

        steps.append([
            self._create_step_animation(
                "步骤1: 确定积分区域",
                f"\\int_{{{a}}}^{{{b}}} f(x) dx",
                [Create(area)]
            )
        ])

        self.current_elements.add(area)

        # 步骤2: 分割区间
        dx = (b - a) / n_rectangles
        rectangles = VGroup()

        for i in range(n_rectangles):
            x_left = a + i * dx
            x_right = a + (i + 1) * dx
            height = self.function(x_left) if method == "riemann" else self.function((x_left + x_right) / 2)

            if height > 0:
                rect = Rectangle(
                    width=self.axes.x_axis.unit_size * dx,
                    height=self.axes.y_axis.unit_size * abs(height),
                    fill_color=self.integral_color,
                    fill_opacity=0.6,
                    stroke_color=WHITE,
                    stroke_width=2
                )
                rect.align_to(self.axes.coords_to_point(x_left, 0), DOWN + LEFT)
            else:
                rect = Rectangle(
                    width=self.axes.x_axis.unit_size * dx,
                    height=self.axes.y_axis.unit_size * abs(height),
                    fill_color=RED,
                    fill_opacity=0.6,
                    stroke_color=WHITE,
                    stroke_width=2
                )
                rect.align_to(self.axes.coords_to_point(x_left, 0), UP + LEFT)

            rectangles.add(rect)

        riemann_sum = sum(self.function(a + i * dx) * dx for i in range(n_rectangles))

        steps.append([
            self._create_step_animation(
                f"步骤2: 分割为{n_rectangles}个矩形",
                f"\\text{{sum}} \\approx {riemann_sum:.3f}",
                [FadeOut(area), Create(rectangles)]
            )
        ])

        self.current_elements.add(rectangles)

        # 步骤3: 逐步增加矩形数量
        for n in [8, 16, 32]:
            new_rectangles = self._create_rectangles(a, b, n, method)
            new_sum = sum(self.function(a + i * (b - a) / n) * (b - a) / n for i in range(n))

            steps.append([
                self._create_step_animation(
                    f"步骤3: 增加到{n}个矩形",
                    f"\\text{{sum}} \\approx {new_sum:.3f}",
                    [Transform(self.current_elements[-1], new_rectangles)]
                )
            ])

        return steps

    def animate_riemann_sum(
            self,
            scene,
            a: float = 0,
            b: float = 2,
            max_rectangles: int = 100,
            animation_time: float = 3
    ):
        """
        动画展示黎曼和收敛过程
        :param scene: 场景对象
        :param a: 积分下限
        :param b: 积分上限
        :param max_rectangles: 最大矩形数
        :param animation_time: 动画时间
        """
        rectangle_counts = [2 ** i for i in range(1, int(np.log2(max_rectangles)) + 1)]

        current_rectangles = self._create_rectangles(a, b, rectangle_counts[0], "riemann")
        scene.add(current_rectangles)

        for n in rectangle_counts[1:]:
            new_rectangles = self._create_rectangles(a, b, n, "riemann")
            scene.play(
                Transform(current_rectangles, new_rectangles),
                run_time=animation_time / len(rectangle_counts)
            )

    def _create_rectangles(self, a: float, b: float, n: int, method: str) -> VGroup:
        """创建矩形组"""
        rectangles = VGroup()
        dx = (b - a) / n

        for i in range(n):
            x_left = a + i * dx
            x_right = a + (i + 1) * dx

            if method == "riemann":
                height = self.function(x_left)
            elif method == "midpoint":
                height = self.function((x_left + x_right) / 2)
            else:
                height = self.function(x_left)

            if abs(height) > 0.001:  # 避免太小的矩形
                rect = Rectangle(
                    width=self.axes.x_axis.unit_size * dx,
                    height=self.axes.y_axis.unit_size * abs(height),
                    fill_color=self.integral_color if height > 0 else RED,
                    fill_opacity=0.6,
                    stroke_color=WHITE,
                    stroke_width=1
                )

                if height > 0:
                    rect.align_to(self.axes.coords_to_point(x_left, 0), DOWN + LEFT)
                else:
                    rect.align_to(self.axes.coords_to_point(x_left, 0), UP + LEFT)

                rectangles.add(rect)

        return rectangles

    def _create_h_bracket(self, x_point: float, h: float) -> VGroup:
        """创建h区间标记"""
        bracket = VGroup()

        # 水平线
        h_line = Line(
            self.axes.coords_to_point(x_point, -0.2),
            self.axes.coords_to_point(x_point + h, -0.2),
            color=YELLOW
        )

        # 左右竖线
        left_tick = Line(
            self.axes.coords_to_point(x_point, -0.15),
            self.axes.coords_to_point(x_point, -0.25),
            color=YELLOW
        )

        right_tick = Line(
            self.axes.coords_to_point(x_point + h, -0.15),
            self.axes.coords_to_point(x_point + h, -0.25),
            color=YELLOW
        )

        # h标签
        h_label = MathTex(f"h={h}", font_size=20, color=YELLOW)
        h_label.next_to(h_line, DOWN, buff=0.1)

        bracket.add(h_line, left_tick, right_tick, h_label)
        return bracket

    def _create_step_animation(self, title: str, formula: str, animations: List) -> List:
        """创建步骤动画"""
        self._update_step_info(title, formula)
        return animations

    def clear_current_elements(self):
        """清除当前动画元素"""
        self.current_elements.clear()
        self.step_counter = 0

    def reset_view(self):
        """重置视图"""
        self.clear_current_elements()
        self._update_step_info("", "")


class DerivativeVisualizer(CalculusStep):
    """
    导数可视化专用类，
    继承于 :class:`~.CalculusStep` ，

    Notes
    -----

    - 专门用于导数概念的可视化演示
    - 支持多种导数展示方式：切线、法线、导数图像等

    Examples
    --------

    >>> class DerivativeExample(Scene):
    >>>     def construct(self):
    >>>         func = lambda x: 0.5 * x**3 - x**2 + 1
    >>>         deriv_viz = DerivativeVisualizer(func)
    >>>         self.add(deriv_viz)
    >>>         animations = deriv_viz.show_moving_tangent(x_range=[-2, 2])
    >>>         for anim in animations:
    >>>             self.play(*anim)

    """

    def show_moving_tangent(self, x_range: List[float], n_points: int = 20) -> List[List]:
        """展示移动的切线"""
        steps = []
        x_values = np.linspace(x_range[0], x_range[1], n_points)

        for i, x in enumerate(x_values):
            point = Dot(self.axes.coords_to_point(x, self.function(x)), color=YELLOW)
            derivative_val = self._numerical_derivative(x)

            tangent = self.axes.plot(
                lambda t: self.function(x) + derivative_val * (t - x),
                x_range=[x - 0.5, x + 0.5],
                color=self.derivative_color
            )

            if i == 0:
                steps.append([Create(point), Create(tangent)])
                self.current_elements.add(point, tangent)
            else:
                new_point = Dot(self.axes.coords_to_point(x, self.function(x)), color=YELLOW)
                steps.append([
                    Transform(self.current_elements[0], new_point),
                    Transform(self.current_elements[1], tangent)
                ])

        return steps


class IntegralVisualizer(CalculusStep):
    """
    积分可视化专用类，
    继承于 :class:`~.CalculusStep` ，

    Notes
    -----

    - 专门用于积分概念的可视化演示
    - 支持多种积分方法的比较：左黎曼和、右黎曼和、梯形法则等

    Examples
    --------

    >>> class IntegralExample(Scene):
    >>>     def construct(self):
    >>>         func = lambda x: x**2
    >>>         int_viz = IntegralVisualizer(func)
    >>>         self.add(int_viz)
    >>>         animations = int_viz.compare_methods(0, 2, 8)
    >>>         for anim in animations:
    >>>             self.play(*anim)

    """

    def compare_methods(
            self,
            a: float,
            b: float,
            n: int
    ) -> List[List]:
        """比较不同积分方法"""
        steps = []
        methods = ["left_riemann", "right_riemann", "midpoint", "trapezoid"]
        colors = [BLUE, RED, GREEN, YELLOW]

        for method, color in zip(methods, colors):
            rectangles = self._create_method_shapes(a, b, n, method, color)
            integral_approx = self._calculate_integral_approximation(a, b, n, method)

            steps.append([
                self._create_step_animation(
                    f"方法: {method.replace('_', ' ').title()}",
                    f"\\text{{近似值}} \\approx {integral_approx:.4f}",
                    [Create(rectangles)]
                )
            ])

            if len(self.current_elements) > 0:
                steps[-1][0].insert(0, FadeOut(self.current_elements))

            self.current_elements = rectangles

        return steps

    def _create_method_shapes(self, a: float, b: float, n: int, method: str, color: str) -> VGroup:
        """根据方法创建形状"""
        shapes = VGroup()
        dx = (b - a) / n

        for i in range(n):
            x_left = a + i * dx
            x_right = a + (i + 1) * dx

            if method == "left_riemann":
                height = self.function(x_left)
            elif method == "right_riemann":
                height = self.function(x_right)
            elif method == "midpoint":
                height = self.function((x_left + x_right) / 2)
            elif method == "trapezoid":
                # 创建梯形
                points = [
                    self.axes.coords_to_point(x_left, 0),
                    self.axes.coords_to_point(x_left, self.function(x_left)),
                    self.axes.coords_to_point(x_right, self.function(x_right)),
                    self.axes.coords_to_point(x_right, 0)
                ]
                shape = Polygon(*points, fill_color=color, fill_opacity=0.6, stroke_color=WHITE)
                shapes.add(shape)
                continue

            # 矩形方法
            if abs(height) > 0.001:
                rect = Rectangle(
                    width=self.axes.x_axis.unit_size * dx,
                    height=self.axes.y_axis.unit_size * abs(height),
                    fill_color=color,
                    fill_opacity=0.6,
                    stroke_color=WHITE,
                    stroke_width=1
                )

                if height > 0:
                    rect.align_to(self.axes.coords_to_point(x_left, 0), DOWN + LEFT)
                else:
                    rect.align_to(self.axes.coords_to_point(x_left, 0), UP + LEFT)

                shapes.add(rect)

        return shapes

    def _calculate_integral_approximation(self, a: float, b: float, n: int, method: str) -> float:
        """计算积分近似值"""
        dx = (b - a) / n
        total = 0

        for i in range(n):
            x_left = a + i * dx
            x_right = a + (i + 1) * dx

            if method == "left_riemann":
                total += self.function(x_left) * dx
            elif method == "right_riemann":
                total += self.function(x_right) * dx
            elif method == "midpoint":
                total += self.function((x_left + x_right) / 2) * dx
            elif method == "trapezoid":
                total += (self.function(x_left) + self.function(x_right)) * dx / 2

        return total


# 使用示例
if __name__ == "__main__":
    # 创建导数演示
    def example_function(x):
        return 0.5 * x ** 2 + 1


    calc_demo = CalculusStep(example_function)
    print("微积分可视化演示类创建成功！")
    print(f"版本: {CalculusStep.__version__}")