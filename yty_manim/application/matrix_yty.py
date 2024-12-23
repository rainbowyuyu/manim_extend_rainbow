from manim import *
from yty_manim.basic_unit.squ_tex import SquTex
import math

# 矩阵预设
matrix_3 = np.array([
    [1, 2, 3],
    [-4, -5, -6],
    [7, 8, 9]
])
matrix_4 = np.array([
    [1, -2, 3, -4],
    [-5, 6, -7, 8],
    [9, -10, 11, -12],
    [-13, 14, -15, 16],
])
matrix_5 = np.array([
    [-1, 2, 3, 4, -5],
    [6, -7, 8, -9, 10],
    [11, 12, -13, 14, 15],
    [16, -17, 18, -19, 20],
    [-21, 22, 23, 24, -25],
])
matrix_2t3 = np.array([
    [-1, 2],
    [3, -4],
    [-5, 6],
])
matrix_3t2 = np.array([
    [-7, 8, 9],
    [10, 11, -12],
])

# 由于继承squ_tex，初始化squ
square_kwargs = {
    "fill_opacity": 0,
    "stroke_opacity": 0,
}

# 文本预设
times_txt = Text("×")
equal_txt = Text("=")
add_txt = Text("+")
sub_txt = Text("-")
left_bracket_txt = Text("(")
right_bracket_txt = Text(")")


# 方阵判断
def matrix_is_square(matrix):
    """
    判断矩阵是否是方阵
    """
    return matrix.shape[0] == matrix.shape[1]


def matrices_are_same_shape(matrix1, matrix2):
    """
    判断矩阵形状是否相同
    """
    return matrix1.shape == matrix2.shape


def matrices_are_trans_shape(matrix1, matrix2):
    """
    判断矩阵形状是否满足乘法
    """
    return matrix1.shape[1] == matrix2.shape[0] and matrix1.shape[0] == matrix2.shape[1]


# ----------------------------------------------------------


class MatrixCal(VGroup):
    """
    可绝对控制元素的矩阵类，
    继承于 :class:`~.VGroup` ，

    Notes
    -----

    常用于矩阵计算的演示
    支持生成负数带括号的矩阵 :method:`neg_with_brackets`
    矩阵加法计算 :method:`addition_mat`

    Examples
    --------

    >>> from yty_manim.matrix_yty import *

    """

    def __init__(self, matrix, buff=1.2, brackets_pair=None):
        if not isinstance(matrix, list | np.ndarray) or not all(isinstance(row, list | np.ndarray) for row in matrix):
            raise ValueError("矩阵必须是二维数组格式")

        self.matrix = matrix
        self.buff = buff
        self.brackets_pair = brackets_pair if brackets_pair else ['[', ']']

        super().__init__()
        self._construct_matrix()
        self._add_brackets(*self.brackets_pair)

    def _construct_matrix(self):
        """
        使用给定的 `matrix` 数据初始化矩阵内容。
        """
        for i in range(len(self.matrix)):
            self.add(SquTex(self.matrix[i], **square_kwargs, side_length=self.buff))
        self.arrange(DOWN, buff=0)

    def _add_brackets(self, left: str = "   [", right: str = "]", **kwargs):
        """
        为矩阵添加括号。
        """
        BRACKET_HEIGHT = 0.5977
        n = int(self.height / BRACKET_HEIGHT) + 1
        empty_tex_array = "".join(
            [r"\begin{array}{c}", *n * [r"\quad \\"], r"\end{array}"]
        )
        tex_left = f"\\left{left}{empty_tex_array}\\right."
        tex_right = f"\\left.{empty_tex_array}\\right{right}"

        l_bracket = MathTex(tex_left, **kwargs)
        r_bracket = MathTex(tex_right, **kwargs)

        bracket_pair = VGroup(l_bracket, r_bracket)
        bracket_pair.stretch_to_fit_height(self.height - 0.3)
        l_bracket.next_to(self, LEFT, 0)
        r_bracket.next_to(self, RIGHT, 0)
        self.brackets = bracket_pair
        self.add(l_bracket, r_bracket)
        return self

    def neg_with_brackets(self):
        """
        给矩阵中的负数项添加括号形成新的矩阵
        :return: 新矩阵
        """
        mat = self.copy()
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                if self.matrix[i][j] < 0:
                    mat[i].add_bracket(j)
        return mat

    def get_row(self, index):
        """
        获得行
        :param index: 行号
        :return: 整行的VGroup
        """
        return self[index]

    def get_column(self, index):
        """
        获得列
        :param index: 列号
        :return: 整列的VGroup
        """
        column = VGroup()
        for i in range(len(self.matrix)):
            column.add(self[i][index])
        return column


# ----------------------------------------------------------


class MatrixDet(MatrixCal):
    """
    行列式计算，
    继承于 :class:`~.MatrixCal` ，

    Notes
    -----

    常用于行列式计算的演示，
    支持扩展成计算演示的行列式 :method:`det_mat`，
    自适应大小 :method:`set_scale_fitness`，
    获取计算过程信息 :method:`get_process_inform`，
    获取结果信息 :method:`get_result_inform`，
    计算过程组 :method:`cal_progress_times`，
    计算结果组 :method:`cal_result_addition`，

    Examples
    --------

    >>> from yty_manim.matrix_yty import *

    创建行列式计算:

    >>> class MatrixDetCreate(Scene):
    >>>     def construct(self):
    >>>         mat_mob = MatrixDet(matrix_4)
    >>>         mat_mob_det = mat_mob.det_mat()
    >>>         vgp , _ , _ = mat_mob_det.get_process_inform(-1)
    >>>         vgp.set_color(RED)
    >>>         self.add(vgp)

    计算行列式结果:

    >>> class MatrixDetCal(Scene):
    >>>     def construct(self):
    >>>         mat_mob = MatrixDet(matrix_3)
    >>>         mat_mob_det = mat_mob.det_mat()
    >>>         vgp , vgp_brackets , num_lst = mat_mob_det.get_process_inform(1)
    >>>         mat_mob_det.set_scale_fitness()
    >>>         self.add(mat_mob_det)
    >>>         vgp.set_color(TEAL)
    >>>         vgp = cal_progress_times(TEAL,vgp,num_lst)
    >>>         self.add(vgp)
    >>>         res_vgp = mat_mob_det.cal_result_addition().shift(DOWN*2)
    >>>         self.add(res_vgp)
    """

    def __init__(self, matrix):
        super().__init__(matrix, brackets_pair=['|', '|'])
        if not matrix_is_square(matrix):
            raise ValueError(f"矩阵{matrix}不是方阵,无法进行行列式运算")
        self.res = 0
        self.res_lst = []

    def det_mat(
            self,
    ):
        """
        生成行列式矩阵
        :return: 一个行列式非方阵
        """
        mat = self.copy()
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix) - 1):
                mat[i].add(self[i][j].copy())
            mat[i].arrange(buff=0)
        mat[0:-2].arrange(DOWN, buff=0)
        mat[-2:].shift(LEFT * len(self.matrix) / 2 + 0.2)
        return mat

    def set_scale_fitness(self):
        """
        行列式计算中自适应大小
        :return: None
        """
        self.scale(1.3 - len(self.matrix) / 8)
        self.shift(UP * 1.7)

    def get_process_inform(self, start, neg_mat=None):
        """
        获得计算过程中的结果
        :param start: 开始项
        :param neg_mat: 带负数的矩阵
        :return: 斜线组，带负数的斜线组，结果列表
        """
        vgp = VGroup()
        vgp_brackets = VGroup()
        num_lst = []
        for i in range(len(self.matrix)):
            vgp.add(self[i][i + start if start >= 0 else -i + start - 1 + 2 * len(self.matrix)])
            if neg_mat is not None:
                vgp_brackets.add(
                    neg_mat[i][i + start if start >= 0 else -i + start - 1 + 2 * len(self.matrix)])
            num_lst.append(
                self.matrix[i][(i + start if start >= 0 else -i + start - 1 + 2 * len(self.matrix)) % len(self.matrix)])
        return vgp, vgp_brackets, num_lst

    def get_result_inform(self):
        """
        获得最终结果
        :return: 结果列表，结果
        """
        res_lst = []
        res = 0
        for i in range(len(self.matrix)):
            _, _, num_lst = self.get_process_inform(i)
            res_lst.append(math.prod(num_lst))
        res += sum(res_lst)
        for i in range(len(self.matrix)):
            _, _, num_lst = self.get_process_inform(-1 - i)
            res_lst.append(math.prod(num_lst))
        res -= sum(res_lst[len(self.matrix):])
        self.res_lst = res_lst
        self.res = res
        return res_lst, res

    def cal_result_addition(self):
        self.get_result_inform()
        res_vgp = VGroup()
        for i in range(len(self.matrix) * 2):
            res_txt = Text(f"{self.res_lst[i]}" if self.res_lst[i] >= 0 else f"({self.res_lst[i]})")
            res_vgp.add(res_txt)
        for i in range(len(self.matrix) - 1):
            res_vgp.insert(2 * i + 1, add_txt.copy())
        for i in range(len(self.matrix)):
            res_vgp.insert(2 * len(self.matrix) - 1 + 2 * i, sub_txt.copy())
        res_vgp.add(equal_txt.copy(), Text(f"{self.res}"))
        res_vgp.arrange()
        return res_vgp


def cal_progress_times(color_pre_cal, vgp, num_lst):
    vgp = vgp.copy()
    res_txt = Text(f"{math.prod(num_lst)}")
    for i in range(len(vgp) - 1):
        vgp.insert(2 * i + 1, times_txt.copy())
    vgp.add(equal_txt.copy(), res_txt)
    vgp.arrange().shift(LEFT * 0.5).set_color(color_pre_cal)
    return vgp


# ----------------------------------------------------------


class MatrixMath(MatrixCal):
    """
    行列式计算，
    继承于 :class:`~.MatrixCal` ，

    Notes
    -----

    常用于行列式加法的演示，
    自适应一般大小 :method:`fit_screen`，
    创建加法矩阵 :method:`addition_mat`，

    Examples
    --------

    >>> from yty_manim.matrix_yty import *

    添加基本加法:

    >>> class MatrixAdditionShow(Scene):
    >>>     def construct(self):
    >>>         i = 0
    >>>         j = 0
    >>>         m1_input = matrix_3
    >>>         m2_input = matrix_3
    >>>         color_add = [RED,BLUE]
    >>>
    >>>         t = add_txt.copy().shift(UP*2)
    >>>         e = equal_txt.copy()
    >>>         m1 = MatrixMath(m1_input)
    >>>         m1.fit_screen(t,LEFT)
    >>>         m2 = MatrixMath(m2_input)
    >>>         m2.fit_screen(t,RIGHT)
    >>>         m3 = m1.addition_mat(m2)
    >>>         m3.fit_screen(edge=DR)
    >>>         e.next_to(m3,LEFT)
    >>>
    >>>         s1 = Square().scale_to_fit_height(m1[0][0].height/1.2).move_to(m1[i][j]).set_color(color_add[0])
    >>>         s2 = Square().scale_to_fit_height(m2[0][0].height/1.2).move_to(m2[i][j]).set_color(color_add[1])
    >>>         first_txt = Text(f"{m1_input[i][j]}" if m1_input[i][j] >= 0 else f"({m1_input[i][j]})").set_color(color_add[0])
    >>>         second_txt = Text(f"{m2_input[i][j]}" if m2_input[i][j] >= 0 else f"({m2_input[i][j]})").set_color(color_add[1])
    >>>         res_txt = Tex(f"{m1_input[i][j] + m2_input[i][j]}").scale(1.2)
    >>>         txt_vgp = VGroup(first_txt,add_txt.copy(),second_txt,equal_txt.copy(),res_txt).arrange().shift(DOWN*1.75+LEFT*3.5)
    >>>         if txt_vgp.width > 5.5:
    >>>             txt_vgp.scale_to_fit_width(5.5)
    >>>
    >>>         self.add(t,e,m1,m2,m3[0][0],m3[-2:],s1,s2,txt_vgp)

    添加基本乘法：

    >>> color_mul = [RED_A,BLUE_A,RED,BLUE]
    >>>
    >>> class MatrixMulShow(Scene):
    >>>     def construct(self):
    >>>         mat_a_input = matrix_2t3
    >>>         mat_b_input = matrix_3t2
    >>>
    >>>         t = times_txt.copy().shift(UP*2)
    >>>         a = MatrixMath(mat_a_input)
    >>>         a.fit_screen(t,LEFT)
    >>>         b = MatrixMath(mat_b_input)
    >>>         b.fit_screen(t,RIGHT)
    >>>         c = a.dot_multiplication_mat(b)
    >>>         c.fit_screen(edge=DR)
    >>>         total = VGroup(a,b,t,equal_txt.copy().next_to(c,LEFT),c[-2:])
    >>>
    >>>         s1 = SurroundingRectangle(a.get_row(0),buff = 0,fill_opacity=0.5,stroke_opacity=0).set_color(color_mul[0])
    >>>         sliding1 = SurroundingRectangle(a.get_row(0)[0],buff = 0).set_color(color_mul[2])
    >>>         s2 = SurroundingRectangle(b.get_column(0),buff = 0,fill_opacity=0.5,stroke_opacity=0).set_color(color_mul[1])
    >>>         sliding2 = SurroundingRectangle(b.get_column(0)[0],buff = 0).set_color(color_mul[3])
    >>>
    >>>         ori_vgp = VGroup(
    >>>             Text(f"{mat_a_input[0][0]}" if mat_a_input[0][0] >= 0 else f"({mat_a_input[0][0]})").set_color(RED),
    >>>             times_txt.copy(),
    >>>             Text(f"{mat_b_input[0][0]}" if mat_b_input[0][0] >= 0 else f"({mat_b_input[0][0]})").set_color(BLUE),
    >>>             equal_txt.copy(),
    >>>             Text(f"{mat_a_input[0][0]*mat_b_input[0][0]}"),
    >>>         ).arrange().shift(DOWN*0.75+LEFT*3.5)
    >>>
    >>>         if ori_vgp.width > 5.5:
    >>>             ori_vgp.scale_to_fit_width(5.5)
    >>>
    >>>         res_vgp = c.get_mul_progress([0,0],color_mul)
    >>>         res_vgp[0].to_edge(LEFT).shift(DOWN*2.5)
    >>>         res_vgp[1].shift(LEFT*3.2+DOWN*2.4)
    >>>         if res_vgp[1].width >= 4.5:
    >>>             res_vgp[1].scale_to_fit_width(4.5)
    >>>
    >>>         part = VGroup(s1,s2,sliding1,sliding2,ori_vgp,res_vgp)
    >>>
    >>>         self.add(part,total,c[0][0])


    """

    def __init__(self, matrix, forward_mat=None, backward_mat=None, **kwargs):
        super().__init__(matrix, **kwargs)
        self.forward_mat = forward_mat
        self.backward_mat = backward_mat

    def fit_screen(
            self,
            txt=None,
            direction=None,
            edge=None,
    ):
        """
        自适应屏幕大小，
        如果填写txt则视为临近文本，
        如果填写edge则视为对齐边缘。
        :param txt: 临近的文本
        :param direction: 临近方向
        :param edge: 对齐的边缘
        :return: None
        """
        HALF_HEIGHT = 3.5
        HALF_WIDTH = 5.5
        rate = HALF_HEIGHT / HALF_WIDTH
        self.scale_to_fit_height(3.5) if self.height / self.width >= rate else self.scale_to_fit_width(5.5)
        if txt is not None:
            self.next_to(txt, direction)
        if edge is not None:
            self.to_edge(edge)

    def addition_mat(self, other):
        """
        相加结果矩阵
        :param other:加矩阵
        :return: 结果矩阵
        """
        if not isinstance(other, MatrixCal):
            raise ValueError("输入必须为矩阵")
        if not matrices_are_same_shape(self.matrix, other.matrix):
            raise ValueError("矩阵大小必须相同")
        matrix = [[self.matrix[i][j] + other.matrix[i][j] for j in range(len(self.matrix[0]))] for i in
                  range(len(self.matrix))]

        return MatrixMath(matrix)

    def dot_multiplication_mat(self, other):
        """
        相乘结果矩阵
        :param other:加矩阵
        :return: 结果矩阵
        """
        if not isinstance(other, MatrixCal):
            raise ValueError("输入必须为矩阵")
        if not matrices_are_trans_shape(self.matrix, other.matrix):
            raise ValueError("矩阵大小必须匹配乘法")
        matrix = self.matrix @ other.matrix
        return MatrixMath(matrix, forward_mat=self.matrix, backward_mat=other.matrix)

    def get_mul_progress(self, index, color_map):
        mij_vgp = VGroup(
            Text("m"),
            Text(f"{index[0] + 1}").set_color(color_map[0]),
            Text(","),
            Text(f"{index[1] + 1}").set_color(color_map[1]),
            Text(":"),
        ).arrange(buff=0.05)
        mij_vgp[2].scale(0.8).shift(DOWN * 0.1)
        mij_vgp[1:4].scale(0.8).shift(DOWN * 0.2)

        pro_vgp = VGroup()
        for i in range(self.forward_mat.shape[1]):
            pro_num = self.forward_mat[index[0]][i] * self.backward_mat[i][index[1]]
            pro = Text(
                f"{pro_num}" if pro_num >= 0 else f"({pro_num})"
            )
            pro_vgp.add(pro)
            pro_vgp.add(add_txt.copy()) if i != self.forward_mat.shape[1] - 1 else None
        pro_vgp.add(equal_txt.copy())
        pro_vgp.add(Text(f"{self.matrix[index[0]][index[1]]}"))
        pro_vgp.arrange()
        res_vgp = VGroup(mij_vgp, pro_vgp)
        return res_vgp

# ---------------------------------------------------------
