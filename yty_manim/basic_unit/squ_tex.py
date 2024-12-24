# rainbow_yu manim_extend.basic_unit.squ_tex 🐋✨
# 数据块等动画基本的类

from manim import *

__version__ = "0.2.4"

__all__ = (
    "typedict",
    "SquTex",
    "SquTexSlide",
    "SquTexAddition",
)


# 默认数据块样式
typedict = {
    "default_type": {
        "side_length": 0.5,
        "fill_color": BLUE,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": BLUE
    }
}


class SquTex(VGroup):
    """
    数据块，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 常用于数据结构的演示和二进制编码的演示，
    - 将方块和数字整合在一起，支持统一的动画和单个动画，
    - :param:`distance` 成员记录了第一次构造数据间的间距
    - 单个动画使用 :method:`animate_one_by_one` 将动画编为一个组
    - 在创建数据块时，把所有的可变参数 kwargs 赋给了 :class:`~.Square` 类。
    - 如果需要改变其他参数，使用 :method:`change_square` 以及 :method:`change_text`，
    - 但要注意使用 :method:`change_text` 时会将原对象的层次改变。
    - 使用 :method:`add_bracket` 将数据块中所有负数的数字都加上括号

    Examples
    --------

    创建数据块:

    >>> class TestSqu(Scene):
    >>>     def construct(self):
    >>>         t = SquTex("yty - rainbow鱼")
    >>>         self.play(t.animate_one_by_one(FadeIn , scale=1.5))
    >>>         self.wait()

    数据块样式改变:

    >>> class TestSqu(Scene):
    >>>     def construct(self):
    >>>         t = SquTex("yty - rainbow鱼",**typedict["default_type"])
    >>>         arg = (1,3,4)
    >>>         self.add(t)
    >>>         self.wait()
    >>>         self.play(t.animate.change_square(*arg,color = GOLD,fill_opacity = 0),)
    >>>         self.play(t.animate.change_text(1,2,5,color = RED),)
    >>>         self.wait()

    """

    def __init__(
            self,
            tex: str | list,
            font="",
            buff=0,
            arrange_direction=RIGHT,
            **kwargs
    ):
        self.tex = tex
        self.buff = buff
        self.arrange_direction = arrange_direction
        self.distance = np.array((0.0, 0.0, 0.0))

        super().__init__()
        for i in range(len(tex)):
            v = VGroup(
                Square(**kwargs),
                Text(f"{tex[i]}", font=font),
            )
            self.add(v)
        self._construct()

    def _construct(self):
        self.arrange(buff=self.buff, direction=self.arrange_direction)
        if len(self) > 1:
            self.distance = np.array((
                self[1].get_center()[0] - self[0].get_center()[0],
                self[1].get_center()[1] - self[0].get_center()[1],
                self[1].get_center()[2] - self[0].get_center()[2],
            ))

    def add_bracket(
            self,
            index: int
    ):
        """
        单个添加括号
        :param index: 位置
        :return: self
        """
        left_bracket = Text("(").next_to(self[index], LEFT, buff=-0.2)
        right_bracket = Text(")").next_to(self[index], RIGHT, buff=-0.2)
        self[index].add(left_bracket, right_bracket)
        return self

    def animate_one_by_one(
            self,
            animation_func,
            lag=None,
            **kwargs
    ):
        """
        逐个运行动画
        :param animation_func:动画方式
        :param lag:延迟时间
        :return:动画组
        """

        if lag is None:
            lag = 0.5
        animations = [animation_func(v, **kwargs) for v in self]
        return AnimationGroup(*animations, lag_ratio=lag)

    def change_square(
            self,
            *args,
            **kwargs,
    ):
        """
        直接改变方块项的参数
        :param args: 可变参数，记录了改变样式的位置
        :param kwargs: 可变字典，记录了改变的样式
        :return: self
        """

        for i in args:
            self[i][0].set(**kwargs)
        return self

    def change_text(
            self,
            *args,
            **kwargs,
    ):
        """
        直接改变文字项的参数
        :param args: 可变参数，记录了改变样式的位置
        :param kwargs: 可变字典，记录了改变的样式
        :return: self
        """

        for i in args:
            self[i][1].set(**kwargs)
        return self

    def change_word_in_text(
            self,
            index: int,
            text=None,
            scale_factor=1,
            **kwargs
    ):
        """
        改变单个文字项的文字和参数
        :param scale_factor: 大小
        :param index: 位置
        :param text: 文字
        :param kwargs: 可变参数
        :return: self
        """
        if text is None:
            text = self.tex[index]
        self[index][1] = Text(f"{text}", **kwargs).scale(scale_factor)
        self[index][1].move_to(self[index][0])
        return self


class SquTexSlide(SquTex):
    """
    演示滑动的数据块，
    继承于 :class:`~.SquTex` ，

    Notes
    -----

    - 在数据块的基础上添加滑动的动画，
    - 使用 :method:`slide` 做基本的位置变化滑动
    - 使用 :method:`slide_fade_from_ori` 做数据块内部的循环滑动，并且头尾缓入缓出

    Examples
    --------

    基础滑动 :method:`slide`:

    >>> class TestSqu(Scene):
    >>>     def construct(self):
    >>>         s = SquTexSlide("yty123")
    >>>         self.add(s)
    >>>         self.wait()
    >>>         for i in range(len(s)):
    >>>             self.play(*s.slide(-1))
    >>>         self.wait()

    循环滑动头尾缓入缓出 :method:`slide_fade`:

    >>> class TestFade(Scene):
    >>>     def construct(self):
    >>>         a = SquTexSlide("yty123")
    >>>         self.add(a)
    >>>         self.play(*a.slide_fade(2))

    外部添加滑动头尾缓入缓出结合应用 :method:`slide_fade`:

    >>> class TestFade(Scene):
    >>>     def construct(self):
    >>>         a = SquTexSlide("yty123")
    >>>         b = SquTex("ab")
    >>>         self.add(a)
    >>>         self.play(*a.slide_fade('forward',b))
    >>>         self.play(*a.slide_fade(2))

    """

    def __init__(
            self,
            tex: str | list,
            **kwargs,
    ):
        super().__init__(tex)

    def _slide_order(
            self,
            direction: int,
            st_input: SquTex = None
    ):
        """
        内置函数，便于控制数据块滑动后返回的self位置仍然正确
        :param direction: 方向：正数为正方向，负数为负方向
        :param st_input: 外部加入的数据块
        :return: self
        """
        if direction < 0:
            for i in range(abs(direction)):
                popped = self[0]
                self.remove(popped)
                if st_input is None:
                    self.add(popped)
                else:
                    self.add(st_input[i])
        elif direction > 0:
            for i in range(direction):
                popped = self[-1]
                self.remove(popped)
                if st_input is None:
                    self.insert(0, popped)
                else:
                    self.insert(0, st_input[-i-1])
        elif direction == 0:
            pass
        return self

    def slide(
            self,
            direction: int,
    ):
        """
        - 基本数据块滑动
        - 动画组，使用play时需要进行序列解包

        :param direction: 方向：正数为正方向，负数为负方向
        :return: all_the_animate
        """
        all_the_animate = []
        cp = self.copy()
        for i in range(len(self)):
            all_the_animate.append(
                self[i].animate.move_to(cp[(len(self) + i + direction) % len(self)])
            )
        self._slide_order(direction)
        return all_the_animate

    def slide_fade(
            self,
            direction: int | str,
            st_input: SquTex = None,
    ):
        """
        - 缓入缓出滑动内部循环或外部添加数据块
        - 动画组，使用play时需要进行序列解包
        :param direction:
            方向：
            在内部循环时采用整数格式：正数为正方向，负数为负方向，数值为滑动的块数；
            当添加外部数据块时采用字符串格式：'forward'为正方向，'backward'为负方向，滑动块数自动为添加的块数
        :param st_input:  输入的数据块
        :return: all_the_animation
        """

        # 格式检测
        if isinstance(direction, int) and st_input is None:
            if 2 * direction > len(self):
                raise ValueError(f"{direction}必须小于等于{len(self) // 2}，否则无法进行渐变操作")
        elif isinstance(direction, str) and st_input and isinstance(st_input, SquTex):
            if direction == 'forward':
                direction = len(st_input)
            elif direction == 'backward':
                direction = -len(st_input)
            else:
                raise ValueError(f"输入数据块进行滑动时{direction}不匹配，使用'forward'和'backward'表示方向")
        else:
            raise ValueError(f"使用slide_fade时directrion:{direction}和st_input:{st_input}需输入正确格式")

        all_the_animate = []
        cp = self.copy()

        # 基础move动画
        for i in range(
            0 if direction > 0 else abs(direction),
            len(self) - direction if direction > 0 else len(self),
        ):
            all_the_animate.append(
                self[i].animate.move_to(cp[(len(self) + i + direction) % len(self)])
            )

        # Fade io动画
        out_vgp = self[-direction:] if direction > 0 else self[:-direction]
        out_cp = out_vgp.copy()
        all_the_animate.append(FadeOut(out_cp, shift=direction * self.distance))
        if st_input:
            out_vgp = st_input
        out_vgp.next_to(
            cp[(len(self) + direction) % len(self)]
            if direction > 0 else
            cp[(len(self) - 1 + direction) % len(self)],
            direction=(-direction) * self.distance,
            buff=0,
        )
        all_the_animate.append(FadeIn(out_vgp, shift=direction * self.distance))

        self._slide_order(direction, st_input)
        return all_the_animate


class SquTexAddition(SquTex):
    pass