from manim import *


class ThreeDVgp(VGroup):
    """
    Examples
    --------
    class PictureShow(ThreeDScene):
        def construct(self):
            self.camera.background_color = color_dict["bg"]
            t2d = Text("rainbow鱼")
            layer_depth = 20
            t3d = ThreeDVgp(t2d,layer_depth = layer_depth)
            self.set_camera_orientation(0.25*PI,-0.25*PI,0.25*PI)
            color_list = [WHITE,BLUE_D]
            t3d.set_depth_gradient_opacity([0,1])
            t3d.set_depth_gradient_color(*color_list)
            self.add(t3d)
    """

    def __init__(
            self,
            mobject,
            layer_depth: int,
    ):
        super().__init__()
        self.layer_depth = layer_depth
        for i in range(layer_depth):
            self.add(mobject.copy().shift(OUT * 0.01 * i))

    def animate_together(
            self,
            animation_func,
            **kwargs
    ):
        animations = [animation_func(v, **kwargs) for v in self]
        return AnimationGroup(*animations)

    def set_shade(
            self,
            shade_color="#7F7F7F",
            shift=DOWN * 0.01 + RIGHT * 0.01,
            scale=1
    ):
        self[0].set_color(shade_color).shift(shift).scale(scale)

    def set_depth_gradient_opacity(
            self,
            opacity_range: list,
    ):
        for i in range(self.layer_depth):
            self[i].set_opacity(opacity_range[0]+i*(opacity_range[1]-opacity_range[0])/self.layer_depth)

    def set_depth_gradient_color(
            self,
            *color_range,
    ):
        color_start = ManimColor(color_range[0]).to_rgb()
        color_end = ManimColor(color_range[-1]).to_rgb()
        for i in range(self.layer_depth):
            self[i].set_color(ManimColor([
                color_start[0] + (color_end[0] - color_start[0]) / self.layer_depth * i,
                color_start[1] + (color_end[1] - color_start[1]) / self.layer_depth * i,
                color_start[2] + (color_end[2] - color_start[2]) / self.layer_depth * i,
            ]))
        self.set_depth_gradient_opacity([0.5, 0.8])
