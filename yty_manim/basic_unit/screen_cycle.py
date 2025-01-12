# rainbow_yu manim_extend.basic_unit.screen_cycle 🐋✨
# 画面屏幕轮播
from typing_extensions import Self

from manim import *
from manim.typing import Vector3

from yty_manim.disposition.fonts_and_colors import *


class ScreenCycle(VGroup):
    def __init__(
            self,
            title_list,
            font=text_font[0],
            gradient_color=gradient_dict["favourite"],
            buff_distance=1
    ):
        super().__init__()

        self.buff_distance = buff_distance
        self.gradient_color = gradient_color
        self.now_screen = -1

        for title in title_list:
            self.add(
                Text(title, font=font)
            )
        self.set_color_by_gradient(gradient_color)
        self.arrange(DOWN, buff=buff_distance)

    def _init(self):
        self.to_corner()
        self.set_color_by_gradient(self.gradient_color)

    def step_forward(self):
        self.now_screen += 1
        self.shift(-self[self.now_screen].get_center())
        return self

    def step_back(self):
        self.now_screen -= 1
        if self.now_screen == -1:
            self._init()
        else:
            self.shift(-self[self.now_screen].get_center())
        return self

    def set_to_edge(
        self, edge: Vector3 = LEFT, buff: float = DEFAULT_MOBJECT_TO_EDGE_BUFFER
    ) -> Self:
        self[self.now_screen].to_edge(edge, buff=buff)
        return self

    def set_back(self):
        self[self.now_screen].center()
        return self
