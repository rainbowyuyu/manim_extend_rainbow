# rainbow_yu manim_extend.basic_unit.screen_cycle 🐋✨
# 画面屏幕轮播

from typing_extensions import Self
from manim.typing import Vector3
from yty_manim.disposition.fonts_and_colors import *


class ScreenCycle(VGroup):
    """
    画面屏幕轮播
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

    def _init(self):
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
        self.now_screen -= 1
        if self.now_screen == -1:
            self._init()
        else:
            self.shift(-self[self.now_screen].get_center())
        return self

    def set_to_edge(
        self, edge: Vector3 = LEFT, buff: float = DEFAULT_MOBJECT_TO_EDGE_BUFFER
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
                item.to_edge(edge, buff=buff)
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
