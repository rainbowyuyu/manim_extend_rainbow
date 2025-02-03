# rainbow_yu manim_extend.application.page_replacement 🐋✨
# 为操作系统中的页面置换算法动画服务的类

from yty_manim.basic_unit.squ_tex import *
from yty_manim.disposition.fonts_and_colors import *
from manim import *

__all__ = (
    "Page",
    "PageReplacement",
    "OptPageReplacement",
    "LruPageReplacement",
    "FifoPageReplacement",
    "ClockPageReplacement",
    # 保留的接口，可以写入其他页面置换算法
)


class Page(VGroup):
    """
    页面，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    - 常用于操作系统中页面置换算法的演示

    Examples
    --------

    创建页面:

    >>> class PageTest(Scene):
    >>>     def construct(self):
    >>>         p = Page([7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1," "],6)
    >>>         self.add(p)

    """

    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 3,
            one_step=(1.5, 0.45),
            color_lst: list = None,
            need_stack: bool = True,
    ):
        super().__init__()

        self.page_lst = page_lst
        self.one_step = one_step
        self.loss_page = 0
        self.stack = None
        self.need_stack = need_stack

        if color_lst is None:
            color_lst = [RED, ORANGE, GREEN, TEAL, BLUE, PURPLE]
        self.color_lst = color_lst

        if page_frame_num <= len(self.color_lst):
            self.page_frame_num = page_frame_num
        else:
            raise ValueError("页框数必须小于颜色数")

        self.DEFAULT_STACK_SHIFT = UP * 2 + self.page_frame_num / 2 * LEFT

        self._construct()
        self._add_to_page()

    def _construct(self):
        self.pages = SquTex(self.page_lst, font=text_font[0], stroke_opacity=0, side_length=self.one_step[0]).scale(self.one_step[1])
        self.page_frame = SquTex(
            [" " for i in range(self.page_frame_num)],
            font=text_font[0],
            arrange_direction=DOWN,
            side_length=1,
            fill_color=BLUE,
            fill_opacity=0.5,
            stroke_opacity=0.8,
            color=BLUE
        ).scale(0.45).next_to(self.pages, DOWN, buff=0)
        self.page_frame.shift(LEFT * self.one_step[0] * self.one_step[1] * (len(self.page_lst) / 2))

        self.opt_frame = VGroup()
        for i in range(self.page_frame_num):
            self.page_frame.change_square(i, color=self.color_lst[i])
            opt_squ = Square(side_length=1).set_color(self.color_lst[i]).move_to(self.pages[i]).scale(self.one_step[1])
            self.opt_frame.add(opt_squ)

        self.page_highlight = Square(side_length=1).set_color(YELLOW).move_to(self.pages[0]).scale(self.one_step[1])

        t = Text("缺页率", font=text_font[0]).scale(0.75)
        self.missing_rate = Variable(0, t).set_color_by_gradient(gradient_dict["favourite"])
        self.missing_rate.scale(0.75).to_edge(RIGHT, buff=1).shift(UP*0.5)
        self.missing_tracker = self.missing_rate.tracker

        self.stack = SquTexSlide(
            " ",
            font=text_font[0],
            arrange_direction=RIGHT,
            side_length=1,
            fill_color=BLUE,
            fill_opacity=0.5,
            stroke_opacity=0.8,
            color=BLUE
        ).shift(self.DEFAULT_STACK_SHIFT)

    def _add_to_page(self):
        self.add(
            self.pages,
            self.page_frame,
            # self.opt_frame,
            self.page_highlight,
            self.missing_rate,
        )
        if self.need_stack:
            self.add(self.stack)
        # 至于顶层
        self.page_highlight.z_index = 5


class PageReplacement(Page):
    """
    页面置换，
    继承于 :class:`~.Page` ，

    Notes
    -----

    - 通过保留接口完成页面置换算法每步演示

    Examples
    --------

    OPT页面置换步进:

    >>> class PageOPT(Scene):
    >>>     def construct(self):
    >>>         input_lst = [7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1," "]
    >>>         p = OptPageReplacement(input_lst,page_frame_num=3)
    >>>         self.add(p)
    >>>         self.wait()
    >>>         for i in range(len(input_lst)-1):
    >>>            p.step_on(self,i)

    """

    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 3,
            **kwargs,
    ):
        super().__init__(page_lst, page_frame_num, **kwargs)
        self.page_frame_lst = []
        self.frame_expect = 0
        self.page_expect = 0
        self.stack_lst = []
        self.pop_index = None
        self.push_val = 0
        self.stepped = False

    def cal_func(self, step):
        """
        页面置换算法接口，继承后重写课改变页面置换搜索逻辑，
        下面给出几种经典的页面置换算法继承：
         - OPT
         - LRU
         - FIFO
         - CLOCK
         - 改进型CLOCK
         - ……
        所有算法需按顺序返回选择的页框和选择的页面两个值，
        并且做出相应的缺页数改变，
        详细看经典算法的示例。
        :param step: 当前步骤
        :returns: 需要替换的页框，标注指向的页面
        """
        pass

    def init_stack(self):
        """
        创建栈接口
        :return: 构造栈的SquTex
        """
        pass

    def cal_stack(self, step):
        """
        维护栈接口
        :param step: 当前步骤
        :return: 弹出的index，压入的值
        """
        pass

    def update_expect(self, step):
        """
        步进更新参数
        :param step: 当前步骤
        :return: None
        """
        self.frame_expect, self.page_expect = self.cal_func(step)
        if self.stack:
            self.pop_index, self.push_val = self.cal_stack(step)

    def stack_step_check(self):
        """
        检查是否推近来改变栈首是变换函数做压入弹出操作
        :return: self
        """
        if len(self.stack_lst) > 0:
            self.stepped = True
        return self

    def step_on(
            self,
            scene: Scene,
            step,
            run_time=1,
    ):
        """
        OPT,LRU,FIFO等基础页面置换算法的步进函数
        CLOCK和改进型CLOCK需要使用保留的接口进行重写
        :param scene: 场景接口，一般为self
        :param step: 当前步骤
        :param run_time: 运行时间
        :return: None
        """
        self.update_expect(step)
        scene.play(
            self.page_frame.animate.shift(RIGHT * self.one_step[0] * self.one_step[1]),
            self.page_highlight.animate.move_to(self.pages[step]),
            run_time=run_time,
        )
        scene.wait(run_time)
        scene.play(self.page_highlight.animate.move_to(self.page_frame[self.frame_expect]), run_time=run_time)
        scene.play(Indicate(self.opt_frame[self.frame_expect]), run_time=run_time)
        pop_animate = [self.page_frame.animate.change_word_in_text(self.frame_expect, self.page_lst[step], 0.5)]
        if self.stack is not None and self.pop_index != "pass":
            pop_animate.extend(self.stack.pop(self.pop_index))

        scene.play(
            *pop_animate,
            run_time=run_time,
        )

        push_animate = [
            self.opt_frame[self.frame_expect].animate.move_to(self.pages[self.page_expect]),
            self.missing_tracker.animate.set_value(self.loss_page / (step + 1)),
        ]
        if self.stack is not None and self.stepped is False:
            push_animate.append(self.stack.animate.change_word_in_text(0, self.push_val))
        if self.stack is not None and self.stepped and self.push_val != "pass":
            push_animate.extend(self.stack.push(self.push_val))
        scene.play(
            *push_animate,
            run_time=run_time,
        )
        scene.wait(run_time)


class OptPageReplacement(PageReplacement):
    """
    OPT页面置换算法
    """
    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 3,
            **kwargs
    ):
        super().__init__(page_lst, page_frame_num, need_stack=False, **kwargs)

    def cal_func(self, step):
        # 获取opt
        def get_opt(step):
            for i in range(step + 1, len(self.page_lst)):
                if self.page_lst[step] == self.page_lst[i]:
                    return i
            return len(self.page_lst) - 1

        # 已有页面
        if len(self.page_frame_lst) != 0:
            for j in range(len(self.page_frame_lst)):
                if self.page_lst[step] == self.page_lst[self.page_frame_lst[j]]:
                    self.page_frame_lst[j] = get_opt(step)
                    return j, get_opt(step)

        # 页面未填满
        if len(self.page_frame_lst) < self.page_frame_num:
            self.page_frame_lst.append(get_opt(step))
            self.loss_page += 1
            return self.loss_page - 1, get_opt(step)

        # 缺页中断
        else:
            max_opt_id = self.page_frame_lst.index(max(self.page_frame_lst))
            new_exp = get_opt(step)
            self.page_frame_lst[max_opt_id] = new_exp
            self.loss_page += 1
            return max_opt_id, new_exp


class LruPageReplacement(PageReplacement):
    """
    LRU页面置换算法
    """
    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 3,
            **kwargs
    ):
        super().__init__(page_lst, page_frame_num, need_stack=True, **kwargs)

    def cal_func(self, step):
        def get_lru(step):
            for i in range(step, -1, -1):
                if self.page_lst[step] == self.page_lst[i]:
                    return i
            return 0

        if len(self.page_frame_lst) != 0:
            for j in range(len(self.page_frame_lst)):
                if self.page_lst[step] == self.page_lst[self.page_frame_lst[j]]:
                    self.page_frame_lst[j] = get_lru(step)
                    return j, get_lru(step)

        if len(self.page_frame_lst) < self.page_frame_num:
            self.page_frame_lst.append(get_lru(step))
            self.loss_page += 1
            return self.loss_page - 1, get_lru(step)

        else:
            min_opt_id = self.page_frame_lst.index(min(self.page_frame_lst))
            new_exp = get_lru(step)
            self.page_frame_lst[min_opt_id] = new_exp
            self.loss_page += 1
            return min_opt_id, new_exp

    def cal_stack(self, step):
        # 不缺页
        for j in range(len(self.stack_lst)):
            self.stack_step_check()
            if self.stack_lst[j] == self.page_lst[step]:
                popped = self.stack_lst.pop(j)
                self.stack_lst.append(popped)
                return j, self.stack_lst[-1]

        # 新增页面
        if len(self.stack_lst) < self.page_frame_num:
            self.stack_lst.append(self.page_lst[step])
            return "pass", self.page_lst[step]
        # 缺页
        else:
            self.stack_lst.pop(0)
            self.stack_lst.append(self.page_lst[step])
            return 0, self.page_lst[step]


class FifoPageReplacement(PageReplacement):
    """
    FIFO页面置换算法
    """
    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 3,
            **kwargs
    ):
        super().__init__(page_lst, page_frame_num, need_stack=True, **kwargs)

    def cal_func(self, step):
        if len(self.page_frame_lst) != 0:
            for j in range(len(self.page_frame_lst)):
                if self.page_lst[step] == self.page_lst[self.page_frame_lst[j]]:
                    return j, step

        if len(self.page_frame_lst) < self.page_frame_num:
            self.page_frame_lst.append(step)
            self.loss_page += 1
            return step, step
        else:
            self.page_frame_lst[self.loss_page % self.page_frame_num] = step
            self.loss_page += 1
            return (self.loss_page - 1) % self.page_frame_num, step

    def cal_stack(self, step):
        # 不缺页
        for j in range(len(self.stack_lst)):
            self.stack_step_check()
            if self.stack_lst[j] == self.page_lst[step]:
                return "pass", "pass"

        # 新增页面
        if len(self.stack_lst) < self.page_frame_num:
            self.stack_lst.append(self.page_lst[step])
            return "pass", self.page_lst[step]
        # 缺页
        else:
            self.stack_lst.pop(0)
            self.stack_lst.append(self.page_lst[step])
            return 0, self.page_lst[step]


class ClockPageReplacement(PageReplacement):
    """
    CLOCK页面置换算法

    这里将cal_stack,cal_func,step_on的接口函数全部进行逻辑的重写，
    传递的关系为先判断栈的滑动，再计算页框的内容再进行步进
    """
    def __init__(
            self,
            page_lst: list,
            page_frame_num: int = 5,
            **kwargs
    ):
        super().__init__(page_lst, page_frame_num, need_stack=True, **kwargs)

    def cal_stack(self, step):
        pass

    def cal_func(self, step):
        pass

    def step_on(
            self,
            scene: Scene,
            step,
            run_time=1,
    ):
        pass
