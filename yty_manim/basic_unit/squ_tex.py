# rainbow_yu manim_extend.basic_unit.squ_tex 🐋✨
# 数据块等动画基本的类

from ..disposition.fonts_and_colors import *

__all__ = (
    "typedict",
    "SquTex",
    "SquTexSlide",
)


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

    >>> class SquTexCreate(Scene):
    >>>     def construct(self):
    >>>         t = SquTex("rainbow")
    >>>         self.play(t.animate_one_by_one(FadeIn , scale=1.5))
    >>>         self.wait()

    数据块样式改变:

    >>> class SquTexChangeStyle(Scene):
    >>>     def construct(self):
    >>>         t = SquTex("rainbow",**typedict["default_type"])
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
            text_type=Text,
            str_need_split=True,
            **kwargs
    ):
        self.tex = tex
        self.buff = buff
        self.arrange_direction = arrange_direction
        self.distance = np.array((0.0, 0.0, 0.0))
        self.font = font
        self.settings = kwargs
        self.text_type = text_type
        self.str_need_split = str_need_split
        self.kwargs = kwargs

        super().__init__()
        if self.str_need_split:
            try:
                self._default_type()
            except IndexError:
                self._without_split_type()
        else:
            self._without_split_type()
        self._construct()

    def _default_type(self):
        """
        基础款的默认构造
        :return: self
        """
        if self.text_type is MathTex:
            for i in range(len(self.tex)):
                v = VGroup(
                    Square(**self.kwargs),
                    MathTex(f"{self.tex[i]}"),
                )
                self.add(v)
        else:
            for i in range(len(self.tex)):
                v = VGroup(
                    Square(**self.kwargs),
                    Text(f"{self.tex[i]}", font=self.font),
                )
                self.add(v)
        return self

    def _without_split_type(self):
        """
        不分隔的构造方式
        :return: self
        """
        v = VGroup(
            Square(**self.kwargs),
        )
        if self.text_type is MathTex:
            v.add(self.text_type(self.tex))
        else:
            v.add(self.text_type(self.tex, font=self.font))
        self.add(v)
        return self

    def _construct(self):
        """
        位置的构造
        :return: self
        """
        self.arrange(buff=self.buff, direction=self.arrange_direction)
        self.update_distance()
        return self

    def update_distance(self):
        """
        更新每个块之间的距离
        :return: self
        """
        cp = self[0].copy()
        cp.next_to(self[0], self.arrange_direction, buff=self.buff)
        self.distance = np.array((
            cp.get_center()[0] - self[0].get_center()[0],
            cp.get_center()[1] - self[0].get_center()[1],
            cp.get_center()[2] - self[0].get_center()[2],
        ))
        return self

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
        self[index][1] = Text(f"{text}", font=self.font, **kwargs).scale(scale_factor)
        self[index][1].move_to(self[index][0])
        return self

    def get_tex_lst(
            self,
            return_type=str,
    ):
        """
        获取SquTex中的文字列表
        :param return_type:返回格式：包含 `int` 和 `str`
        :return: 更新在self.tex中的文字列表
        """
        self.tex = []
        for i in range(len(self)):
            if return_type is str:
                self.tex.extend(self[i][1].original_text)
            elif return_type is int:
                self.tex.append(int(self[i][1].original_text))
            else:
                raise TypeError("return_type must be `str` or `int`")
        return self.tex

    def get_color_lst(self):
        """
        获取SquTex中的颜色列表
        :return: 颜色列表
        """
        color_lst = []
        for i in range(len(self)):
            color_lst.append(self[i][1].color)
        return color_lst


class SquTexSlide(SquTex):
    """
    演示滑动的数据块，
    继承于 :class:`~.SquTex` ，

    Notes
    -----

    - 在数据块的基础上添加滑动的动画，
    - 使用 :method:`pop` 和 :method:`push` 完成基本栈和队列的压入和弹出
    - 使用 :method:`slide` 做基本的位置变化滑动
    - 使用 :method:`slide_fade` 做数据块内部或外部添加的循环滑动，并且头尾缓入缓出

    Examples
    --------

    栈和队列的压入弹出 :method:`pop` 和 :method:`push`:

    >>> class StackTest(Scene):
    >>>     def construct(self):
    >>>         s = SquTexSlide("ra")
    >>>         p1 = SquTexSlide("i")
    >>>         p2 = SquTexSlide("n")
    >>>         self.add(s)
    >>>         self.play(*s.push(p1,2,force_center=True))
    >>>         self.play(*s.push(p2,3,force_center=True))
    >>>         for i in range(3):
    >>>             self.play(*s.pop(0,force_center=True))
    >>>         self.wait()

    基础滑动 :method:`slide`:

    >>> class SquTexSlideBasic(Scene):
    >>>     def construct(self):
    >>>         s = SquTexSlide("rainbow")
    >>>         self.add(s)
    >>>         self.wait()
    >>>         for i in range(len(s)):
    >>>             self.play(*s.slide(-1))
    >>>         self.wait()

    循环滑动头尾缓入缓出 :method:`slide_fade`:

    >>> class SquTexSlideFadeRotate(Scene):
    >>>     def construct(self):
    >>>         a = SquTexSlide("rainbow")
    >>>         self.add(a)
    >>>         self.play(*a.slide_fade(2))

    外部添加滑动头尾缓入缓出结合应用 :method:`slide_fade`:

    >>> class SquTexSlideFadeAddition(Scene):
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
        super().__init__(tex, **kwargs)

    def pop(
            self,
            index: int = -1,
            force_center=False
    ):
        """
        弹出动画
        :param index: 位置
        :param force_center: 强制居中
        :return: all_the_animate
        """
        all_the_animate = []
        center = self.get_center()
        cp = self.copy()

        popped = self[index]
        self.remove(popped)
        all_the_animate.append(
            FadeOut(popped, shift=np.array((self.distance[1], -self.distance[0], 0))),
        )
        for i in range(index, len(self)):
            all_the_animate.append(self[i].animate.move_to(cp[i]))
        if force_center:
            all_the_animate.append(self.animate.move_to(center))
        return all_the_animate

    def push(
            self,
            st_input: SquTex | str | int,
            index=None,
            force_center=False,
    ):
        """
        推入动画
        :param index: 位置
        :param st_input: 加入的数据块
        :param force_center: 强制居中
        :return: all_the_animate
        """
        cp = self.copy()
        all_the_animate = []

        st_color = self.get_color()

        if isinstance(st_input, SquTex):
            st_color = st_input.get_color()
            st_input = st_input.tex

        st_input = SquTexSlide(f"{st_input}", font=self.font, **self.settings).set_color(st_color)

        if index is None or index == len(self):
            st_input.next_to(self, direction=self.arrange_direction, buff=self.buff)
            self.add(st_input)
            all_the_animate.append(
                FadeIn(st_input, shift=np.array((self.distance[1], -self.distance[0], 0))),
            )
        else:
            st_input.move_to(cp[index])
            for i in range(index, len(self)):
                all_the_animate.append(self[i].animate.shift(self.distance))
            all_the_animate.append(
                FadeIn(st_input, shift=np.array((self.distance[1], -self.distance[0], 0))),
            )
            self.insert(index, st_input)

        if force_center:
            all_the_animate.append(self.animate.arrange(direction=self.arrange_direction, buff=self.buff))

        return all_the_animate

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
            buff=self.buff,
        )
        all_the_animate.append(FadeIn(out_vgp, shift=direction * self.distance))

        self._slide_order(direction, st_input)
        return all_the_animate


class Stack(SquTexSlide):
    """
    展示栈结构的数据库
    继承于 :class:`~.SquTexSlide` ，

    Notes
    -----

    - 在滑动数据块的基础上添加数据结构的变换特性，
    - 使用 :method:`swap` 完成两数据块的交换
    - 使用 :method:`reverse` 完成某个数据位置后的翻转
    - 使用 :method:`add_pointer` 添加特定位置的指针

    Examples
    --------

    """
    def __init__(
            self,
            tex: str | list,
            **kwargs,
    ):
        super().__init__(tex, **kwargs)
