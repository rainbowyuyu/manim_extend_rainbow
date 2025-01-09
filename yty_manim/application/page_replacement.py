# rainbow_yu manim_extend.application.page_replacement 🐋✨
# 为操作系统中的页面置换算法动画服务的类

from yty_manim.basic_unit.squ_tex import *
from yty_manim.disposition.fonts_and_colors import *
from manim import *

__all__ = (
    "Page",
    "PageReplacement",
    "step_on",
    "OptPageReplacement",
    "LruPageReplacement",
    "FifoPageReplacement",
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
    ):
        super().__init__()

        self.page_lst = page_lst
        self.one_step = one_step

        if color_lst is None:
            color_lst = [RED, ORANGE, GREEN, TEAL, BLUE, PURPLE]
        self.color_lst = color_lst

        if page_frame_num <= len(self.color_lst):
            self.page_frame_num = page_frame_num
        else:
            raise ValueError("页框数必须小于颜色数")

        self._construct()
        self._add_to_page()

    def _construct(self):
        self.pages = SquTex(self.page_lst, stroke_opacity=0, side_length=self.one_step[0]).scale(self.one_step[1])
        self.page_frame = SquTex(
            ["" for i in range(self.page_frame_num)],
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

        t = Text("缺页率",font=text_font[0]).scale(0.75)
        self.missing_rate = Variable(0, t).set_color_by_gradient(gradient_dict["favourite"])
        self.missing_rate.scale(0.75).to_edge(RIGHT,buff=1).shift(UP*0.5)
        self.missing_tracker = self.missing_rate.tracker

    def _add_to_page(self):
        self.add(
            self.pages,
            self.page_frame,
            # self.opt_frame,
            self.page_highlight,
            self.missing_rate
        )
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
    >>>             step_on(self,p,i)

    """

    def __init__(
            self,
            page_lst: list,
            **kwargs,
    ):
        super().__init__(page_lst, **kwargs)
        self.page_frame_lst = []
        self.frame_expect = 0
        self.page_expect = 0

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
        所有算法需按顺序返回选择的页框和选择的页面两个值
        :param step: 当前步骤
        :returns: 选择的页框，选择的页面
        """
        pass

    def update_expect(self, step):
        """
        步进更新参数
        :param step: 当前步骤
        :return: None
        """
        self.frame_expect, self.page_expect = self.cal_func(step)


def step_on(
        scene: Scene,
        page: PageReplacement,
        step,
        run_time=1,
):
    """
    步进函数
    :param scene: 场景接口，一般为self
    :param page: 页面
    :param step: 当前步骤
    :param run_time: 运行时间
    :return: None
    """
    page.update_expect(step)
    scene.play(
        page.page_frame.animate.shift(RIGHT * page.one_step[0] * page.one_step[1]),
        page.page_highlight.animate.move_to(page.pages[step]),
        run_time=run_time,
    )
    scene.wait(run_time)
    scene.play(page.page_highlight.animate.move_to(page.page_frame[page.frame_expect]),run_time=run_time)
    scene.play(Indicate(page.opt_frame[page.frame_expect]),run_time=run_time)
    scene.play(page.page_frame.animate.change_word_in_text(page.frame_expect, page.page_lst[step], 0.5),run_time=run_time)
    scene.play(page.opt_frame[page.frame_expect].animate.move_to(page.pages[page.page_expect]))
    scene.wait(run_time)


class OptPageReplacement(PageReplacement):
    """
    OPT页面置换算法
    """

    def cal_func(self, step):
        def get_opt(step):
            for i in range(step + 1, len(self.page_lst)):
                if self.page_lst[step] == self.page_lst[i]:
                    return i
            return len(self.page_lst) - 1

        if len(self.page_frame_lst) < self.page_frame_num:
            self.page_frame_lst.append(get_opt(step))
            return step, get_opt(step)
        else:
            for j in range(self.page_frame_num):
                if self.page_lst[step] == self.page_lst[self.page_frame_lst[j]]:
                    self.page_frame_lst[j] = get_opt(step)
                    return j, get_opt(step)

        max_opt_id = self.page_frame_lst.index(max(self.page_frame_lst))
        new_exp = get_opt(step)
        self.page_frame_lst[max_opt_id] = new_exp

        return max_opt_id, new_exp


class LruPageReplacement(PageReplacement):
    """
    LRU页面置换算法
    """

    def cal_func(self, step):
        def get_lru(step):
            for i in range(step, -1, -1):
                if self.page_lst[step] == self.page_lst[i]:
                    return i
            return 0

        if len(self.page_frame_lst) < self.page_frame_num:
            self.page_frame_lst.append(get_lru(step))
            return step, get_lru(step)
        else:
            for j in range(self.page_frame_num):
                if self.page_lst[step] == self.page_lst[self.page_frame_lst[j]]:
                    self.page_frame_lst[j] = get_lru(step)
                    return j, get_lru(step)

        min_opt_id = self.page_frame_lst.index(min(self.page_frame_lst))
        new_exp = get_lru(step)
        self.page_frame_lst[min_opt_id] = new_exp

        return min_opt_id, new_exp


class FifoPageReplacement(PageReplacement):
    """
    FIFO页面置换算法
    """
    def cal_func(self, step):
        pass
