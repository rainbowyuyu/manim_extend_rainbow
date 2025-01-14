# rainbow_yu manim_extend.basic_unit.stack 🐋✨
# 栈结构动画

from .squ_tex import *


class Stack(SquTex):
    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

    def push(
            self,
            squ_tex: SquTex,
            index: int = None,
    ):
        if index is None:
            index = len(self) - 1
        if len(self) == 0:
            self.add(squ_tex)
        else:
            center = self.get_center()
            self.insert(index, squ_tex)
            self.arrange(direction=self.arrange_direction, buff=self.buff)
            self.move_to(center)
        return self



