# rainbow_yu manim_extend.basic_unit.shapes 🐋✨
# some shapes use in videos

from manim import *


class Book(VGroup):
    """
    shape of book

    Examples:
    ------

    >>> class BookShape(Scene):
    >>>     def construct(self):
    >>>         b1 = Book("...",0,BLUE,BLUE_E)
    >>>         b2 = Book("CV",1,GREEN,GREEN_E)
    >>>         self.add(b1.shift(LEFT*0.5),b2)

    """
    def __init__(
            self,
            title,
            index=0,
            fill_color=GRAY,
            stroke_color=GRAY_E
    ):
        super().__init__()
        self.title = title
        self.index = index

        t = VGroup()
        for i in self.title:
            t.add(Text(i))
        t.arrange(DOWN, buff=0.1)

        depth_points = [
            np.array((0.25, -1, 0.0)),
            np.array((0.6, -0.25, 0.0)),
            np.array((0.6, -0.25, 0.0))+ 2*UP,
            np.array((0.25, -1, 0.0)) + 2*UP,
        ]

        # 创建平行四边形
        depth_pol = Polygon(
            *depth_points,
            fill_color=fill_color,
            stroke_color=stroke_color,
            fill_opacity=1,
            stroke_opacity=1,
            stroke_width=2
        )

        height_points = [
            np.array((-0.25, 1, 0.0)),
            np.array((0.1, 1.75, 0.0)),
            np.array((0.1, 1.75, 0.0))+ 0.5*RIGHT,
            np.array((-0.25, 1, 0.0)) + 0.5*RIGHT,
        ]

        height_pol = Polygon(
            *height_points,
            fill_color="#ffeebb",
            stroke_color=stroke_color,
            fill_opacity=1,
            stroke_opacity=1,
            stroke_width=2
        )

        self.add(
            depth_pol,
            height_pol,
            Rectangle(
                fill_color=fill_color,
                stroke_color=stroke_color,
                fill_opacity=1,
                stroke_opacity=1,
                height=2,
                width=0.5,
            ),
            t.shift(DOWN*0.4).scale(0.8),

        )
        self.set_z_index(self.index)
