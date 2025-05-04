# rainbow_yu manim_extend.application.title_animate 🐋✨
# title and logo animate

from manim import *
from yty_manim.basic_unit.squ_tex import *
from yty_manim.disposition.fonts_and_colors import *
import random

class TitleAnimate(SquTexSlide):
    """
    animate for title

    Examples:
    ------

    >>> class TitleIntroduction(Scene):
    >>>     def construct(self):
    >>>
    >>>         ta = TitleAnimate(
    >>>             "rainbow鱼",
    >>>             font=text_font[0],
    >>>             side_length=1.5,
    >>>             fill_opacity=0.5,
    >>>             stroke_opacity=0.8
    >>>         )
    >>>         self.wait()
    >>>         ta.generate(self,run_time=0.5)
    >>>         self.wait(3)
    >>>         ta.disappear(self,run_time=0.2,force_center=False)
    >>>         self.wait(2)


    """
    def __init__(
            self,
            tex: str | list,
            **kwargs
    ):
        super().__init__(tex[0], **kwargs)
        self.tex = tex
        self.squ_kwargs = kwargs
        self.set_color(RED)


    def generate(
            self,
            scene: Scene,
            force_center=True,
            force_color=True,
            **kwargs
    ):
        scene.play(FadeIn(self,direction=DOWN), **kwargs)
        if len(self.tex) > 1:
            for i in range(len(self.tex)-1):
                st = SquTexSlide(self.tex[i+1],**self.squ_kwargs)
                st.set_color(gradient_dict['rainbow_color'][(i+1)%7])
                scene.play(
                    *self.push(st,force_center=force_center,force_color=force_color),
                    **kwargs
                )

    def disappear(
            self,
            scene: Scene,
            force_center=True,
            **kwargs
    ):
        for i in range(len(self.tex)-1):
            length = len(self)
            scene.play(
                *self.pop(random.randint(0,length-1),force_center=force_center),
                **kwargs
            )

        scene.play(FadeOut(self,direction=DOWN), **kwargs)
