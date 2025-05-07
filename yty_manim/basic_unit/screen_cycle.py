# rainbow_yu manim_extend.basic_unit.screen_cycle 🐋✨
# 标题画面屏幕轮播

from typing_extensions import Self
from manim.typing import Vector3D
from yty_manim.disposition.fonts_and_colors import *


class ScreenCycle(VGroup):
    """
    画面屏幕轮播，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 常用于开始介绍界面的标题画面轮播和标题置于边角

    Examples
    --------

    标题轮播:

    >>> class ScreenTest(Scene):
    >>>     def construct(self):
    >>>         text_list = [
    >>>             "Hello World",
    >>>             "Hell Worl",
    >>>             "Hel Wor",
    >>>             "He Wo",
    >>>         ]
    >>>         s = ScreenCycle(text_list)
    >>>         self.add(s)
    >>>         for i in range(len(text_list)):
    >>>         self.play(s.animate.step_forward())
    >>>         self.play(s.animate.set_to_edge(UL))
    >>>         self.play(s.animate.set_back())

    """
    def __init__(
            self,
            title_list,
            font=text_font[0],
            gradient_color=gradient_dict["favourite"],
            buff_distance=1,
            magnification=6/5,
    ):
        super().__init__()

        self.buff_distance = buff_distance
        self.gradient_color = gradient_color
        self.now_screen = -1
        self.total_steps = len(title_list)
        self.magnification = magnification

        for title in title_list:
            self.add(
                Text(title, font=font)
            )
        self.set_color_by_gradient(gradient_color)
        self.arrange(DOWN, buff=buff_distance)

    def _init_screen(self):
        """
        位置和颜色初始化
        :return: self
        """
        self.center()
        self.set_color_by_gradient(self.gradient_color)
        return self

    def step_forward(self):
        """
        向前轮播
        :return: self
        """
        self.now_screen += 1
        if self.now_screen == self.total_steps:
            self._init_screen()
            return self
        self.shift(-self[self.now_screen].get_center())
        if self.now_screen == 0:
            self.set_color(GRAY_B)
        else:
            self[self.now_screen - 1].set_color(GRAY_B).scale(1/self.magnification)
        self[self.now_screen].set_color_by_gradient(self.gradient_color).scale(self.magnification)
        return self

    def step_back(self):
        """
        向后轮播
        :return: self
        """
        pass

    def set_to_edge(
        self, edge: Vector3D = LEFT, buff: float = DEFAULT_MOBJECT_TO_EDGE_BUFFER
    ) -> Self:
        """
        标题前往边缘，隐藏其他
        :param edge: 边缘向量
        :param buff: 边距
        :return: self
        """
        self[self.now_screen].to_edge(edge, buff=buff)
        for item in self:
            if item != self[self.now_screen]:
                item.set_opacity(0)
        return self

    def set_back(self):
        """
        标题返回中心，恢复其他
        :return: self
        """
        self[self.now_screen].center()
        self.set_opacity(1)
        return self


class Directory(VGroup):
    """
    目录演示，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 最开始内容的目录展示

    Examples:
    ------

    >>> class DirectoryPage(Scene):
    >>>     def construct(self):
    >>>         title = [
    >>>                 "页面与页面置换",
    >>>                 "抖动与belady",
    >>>                 "页面置换算法",
    >>>                 "栈结构",
    >>>                 "编程代码"
    >>>         ]
    >>>         d = Directory(title,font = text_font[0])
    >>>         d[1].set_color(GRAY)
    >>>         self.play(Write(d[0:2]),run_time=2)
    >>>         for i in range(len(title)):
    >>>             d.step_forward(self)

    """
    def __init__(
            self,
            title: list,
            **kwargs,
    ):
        super().__init__()
        self.current = -1
        self.title = title

        text = VGroup()
        dot = VGroup()
        lines = VGroup()
        for i in range(len(self.title)):
            t = Text(self.title[i], **kwargs).scale(0.8).set_color(GRAY)
            text.add(t)
            d = Dot().scale(2)
            dot.add(d)
        text.arrange(DOWN, buff=0.8, aligned_edge=LEFT).to_edge(LEFT, buff=1.5)
        for i in range(len(dot)):
            dot[i].next_to(text[i], LEFT, buff=0.5).set_color(gradient_dict['rainbow_color'][i%7])

        for i in range(len(self.title)-1):
            l = Line(dot[i].get_center(), dot[i+1].get_center())
            l.set_color_by_gradient(
                [gradient_dict['rainbow_color'][i % 7+1],gradient_dict['rainbow_color'][i%7]]
            )
            lines.add(l)

        dot.set_z_index(1)
        self.add(text,dot,lines)

    def create_line(
            self,
            scene: Scene,
            index: int = None,
            **kwargs,
    ):
        """
        绘制连接线
        :param scene: 场景类
        :param index: 当前位置
        :param kwargs: play的可变参数
        :return: None
        """
        if index is None:
            index = self.current
        if index < 0:
            pass
        elif index >= len(self.title):
            raise IndexError
        else:
            scene.play(
                Create(self[2][index]),
                **kwargs
            )

    def change_color(
            self,
            scene: Scene,
            index: int = None,
            **kwargs,
    ):
        """
        改变文字和点的颜色
        :param scene: 场景类
        :param index: 当前位置
        :param kwargs: 可变参数
        :return: None
        """
        if index is None:
            index = self.current + 1
        scene.play(
            self[0][index].animate.set_color(gradient_dict['rainbow_color'][index%7]),
            self[1][index].animate.set_color(gradient_dict['rainbow_color'][index%7]),
            **kwargs,
        )

    def step_forward(
            self,
            scene: Scene,
            change_color_time = 1,
            create_line_time = 5
    ):
        """
        步进函数
        :param scene: 场景类
        :param change_color_time: 改变颜色时间
        :param create_line_time: 改变线长时间
        :return: None
        """
        self.change_color(scene, change_color_time)
        self.create_line(scene, create_line_time)
        self.current += 1

