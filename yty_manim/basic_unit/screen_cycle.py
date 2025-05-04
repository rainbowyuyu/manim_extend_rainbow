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
    >>>         self.play(s.animate.step_forward())
    >>>         self.play(s.animate.step_forward())
    >>>         self.play(s.animate.set_to_edge(UL))
    >>>         self.play(s.animate.set_back())
    >>>         self.play(s.animate.step_forward())
    >>>         self.play(s.animate.step_forward())
    >>>         self.play(s.animate.step_forward())

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
    目录半成品，后期完善
    """
    def __init__(
            self,
            title: list,
            **kwargs,
    ):
        super().__init__()
        self.current = -1

        text = VGroup()
        dot = VGroup()
        lines = VGroup()
        for i in range(len(title)):
            t = Text(title[i], **kwargs).scale(0.8).set_color(GRAY)
            text.add(t)
            d = Dot().scale(2)
            dot.add(d)
        text.arrange(DOWN, buff=0.8, aligned_edge=LEFT).to_edge(LEFT, buff=1.5)
        for i in range(len(dot)):
            dot[i].next_to(text[i], LEFT, buff=0.5).set_color(gradient_dict['rainbow_color'][i%7])

        for i in range(len(title)-1):
            l = Line(dot[i].get_center(), dot[i+1].get_center())
            l.set_color_by_gradient(
                [gradient_dict['rainbow_color'][i % 7+1],gradient_dict['rainbow_color'][i%7]]
            )
            lines.add(l)

        dot.set_z_index(1)
        self.add(text,dot,lines)

    def step_forward(self):
        if self.current != -1:
            self[0][self.current].scale(0.8).set_color(GRAY)