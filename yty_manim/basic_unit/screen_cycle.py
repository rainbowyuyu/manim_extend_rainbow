# rainbow_yu manim_extend.basic_unit.screen_cycle 🐋✨
# 画面屏幕轮播

from manim import *
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
        self.now_screen = 0

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
        pass

    def step_back(self):
        self.now_screen -= 1
        if self.now_screen == 0:
            self._init()
        pass
