# rainbow_yu manim_extend.basic_unit.dec_bin 🐋✨
# 二进制基本的类

from yty_manim.disposition.fonts_and_colors import *
from yty_manim.basic_unit.squ_tex import *

__all__ = (
    "BinNumber",
    "Bin4SquTex",
)


class BinNumber:
    """
    数据块中二进制数

    Notes
    -----

    通过记录二进制数的符号位，整数部分，小数部分，

    将十进制数转换为理想的二进制数格式，
    并且能对二进制数进行一些处理，

    Method
    ------

    - 先用空值对类对象进行赋值，输入 bin_num 后使用 :method:`bin2dec` 将二进制数类对象转化为一个十进制数，
    - 使用 :method:`standardize` 将二进制数类对象进行格式标准化，
    - 使用 :method:`ex_one` 将二进制数类对象转化为其反码，
    - 使用 :method:`ex_two` 将二进制数类对象转化为其补码，
    - 使用 :method:`information` 显示该二进制数的所有参数信息，
    - 使用 :method:`cal_check` 检验在算法运算时是否会超出精度，
    - 使用计算方法重载时，格式跟随第一目继承。

    Parameters
    ------
    dec_num
        十进制数
    precision
        二进制数位数或小数精度
    symbolic_bit
        符号位位数，0表示使用正负号表示符号位
    is_split
        是否将符号位分开（仅对整数有效）

    Examples
    --------

    二进制转换:

    >>> from yty_manim.basic_unit.dec_bin import BinNumber

    #定义十进制数转换二进制数
    >>> test_bin = BinNumber(-0.2, 8, 1, True)
    >>> print(test_bin)
    >>> print(test_bin.ex_one())
    >>> print(test_bin.ex_two())

    #更新二进制数
    >>> test_bin.dec_num = -32
    >>> test_bin.precision = 10
    >>> test_bin.update_binary()
    >>> print(test_bin)
    >>> print(test_bin.ex_one())
    >>> print(test_bin.ex_two())

    #二进制转换十进制并标准化
    >>> bin_num = BinNumber(10, 8, 1, True)
    >>> print(bin_num)
    >>> bin_num.bin_num = '11111'
    >>> print(bin_num)
    >>> bin_num.bin2dec()
    >>> print(bin_num.dec_num)
    >>> bin_num.standardize()
    >>> print(bin_num)

    #计算符号重载
    >>> bin1 = BinNumber(8, 5, 1, True)
    >>> bin2 = BinNumber(2, 5, 1, True)
    >>> bin3 = bin1 + bin2
    >>> print(bin3)

    """

    __version__: str = "2.0.1"

    # 保留文字
    _sign = ""
    _split = ""
    _binary_int = ""
    _binary_float = ""

    def __init__(
            self,
            dec_num: int | float | str | None = None,
            precision: int | None = None,
            symbolic_bit: int = 1,
            is_split: bool = False,
    ):
        if dec_num is None:
            self.dec_num = 0
        else:
            self.dec_num = dec_num
        self.precision = precision
        self.symbolic_bit = symbolic_bit
        self.is_split = is_split
        self.update_binary()

    def information(self):
        """展示当前二进制数的信息"""
        print("dec_num:", self.dec_num)
        print("precision:", self.precision)
        print("symbolic_bit:", self.symbolic_bit)
        print("is_split:", self.is_split)
        return self.bin_num

    def __repr__(
            self,
            information: bool = False,
    ):
        if information:
            return self.information()
        else:
            return self.bin_num

    def _set_sign(self) -> str:
        """ 符号处理 """
        if self.symbolic_bit == 0:
            return '-' if self.dec_num < 0 else ''
        return '0' * self.symbolic_bit if self.dec_num >= 0 else '1' * self.symbolic_bit

    def _set_split(self) -> str:
        """ 分隔符和位数补齐 """
        dec_num = float(self.dec_num)
        if dec_num.is_integer() and self.is_split and self.symbolic_bit != 0:
            return '|'
        return ''

    def _set_precision(self) -> str:
        """精度补齐"""
        dec_num = float(self.dec_num)
        int_dec = abs(int(self.dec_num))
        if dec_num.is_integer() is True and len(self._sign) <= self.precision:
            binary_int = ""
            binary_int += '0' * (self.precision - self.symbolic_bit - len(bin(int_dec)[2:]))
            return binary_int
        return ''

    def _set_binary_int(self) -> str:
        """ 整数部分二进制转换 """
        dec_num = float(self.dec_num)
        int_dec = abs(int(self.dec_num))
        binary_int = bin(int_dec)[2:] if int_dec != 0 else ''
        if dec_num.is_integer() and self.precision and len(self._sign) <= self.precision:
            binary_int = '0' * (self.precision - self.symbolic_bit - len(binary_int)) + binary_int
        return binary_int

    def _set_binary_float(self) -> str:
        """ 小数部分二进制转换 """
        dec_num = float(self.dec_num)
        if dec_num.is_integer():
            return ''
        binary_float = '.'
        float_dec = abs(self.dec_num - int(self.dec_num))
        for _ in range(self.precision or 0):
            float_dec *= 2
            if float_dec >= 1:
                float_dec -= 1
                binary_float += '1'
            else:
                binary_float += '0'
            if float_dec == 0:
                break
        return binary_float

    def update_binary(self):
        """更新二进制数"""
        self._sign = self._set_sign()
        self._split = self._set_split()
        # 整数位补齐只在 _set_binary_int 中完成，避免与 _set_precision 重复补零
        self._binary_int = self._set_binary_int()
        self._binary_float = self._set_binary_float()
        self.bin_num = self._sign + self._split + self._binary_int + self._binary_float

    def bin2dec(self):
        """二进制转换回十进制"""
        int_part, float_part = self.bin_num.split('.') if '.' in self.bin_num else (self.bin_num, '0')

        int_part = int_part.replace('|', '')
        dec_int = int(int_part[self.symbolic_bit:], 2) if len(int_part) > self.symbolic_bit else 0
        dec_float = sum(int(bit) * (2 ** -i) for i, bit in enumerate(float_part, start=1)) if float_part != '0' else 0

        self.dec_num = dec_int + dec_float
        if '1' in int_part[0:self.symbolic_bit + 1]:
            self.dec_num *= -1

        return self.dec_num

    def standardize(self):
        """将输入的二进制数以定义的格式进行标准化"""
        self.bin2dec()
        self.update_binary()

    def cal_check(self):
        """加法校验是否超出精度"""
        pass

    def ex_one(self):
        """反码转换"""
        if self._sign[0] in ('-', '1'):
            binary_number = self._binary_int + self._binary_float
            ones = ''.join('1' if bit == '0' else '0' if bit == '1' else '.' for bit in binary_number)
            return self._sign + self._split + ones
        else:
            return self._sign + self._split + self._binary_int + self._binary_float

    def ex_two(self):
        """补码转换"""
        if self._sign[0] in ('-', '1'):
            binary_number = self._binary_int + self._binary_float
            ones = ''.join('1' if bit == '0' else '0' if bit == '1' else '.' for bit in binary_number)
            carry = 1
            twos = ''
            for bit in reversed(ones):
                if bit == '.':
                    twos = '.' + twos
                    continue
                sum_bit = int(bit) + carry
                twos = str(sum_bit % 2) + twos
                carry = sum_bit // 2
            return self._sign + self._split + twos
        else:
            return self._sign + self._split + self._binary_int + self._binary_float

    def __add__(self, other):
        """加法重载，返回两个二进制数的和"""
        if isinstance(other, BinNumber):
            result_dec = self.dec_num + other.dec_num
            return BinNumber(result_dec, self.precision, self.symbolic_bit, self.is_split)
        raise TypeError("Unsupported operand type(s) for +: 'BinNumber' and '{}'".format(type(other).__name__))

    def __sub__(self, other):
        """减法重载"""
        if isinstance(other, BinNumber):
            result_dec = self.dec_num - other.dec_num
            return BinNumber(result_dec, self.precision, self.symbolic_bit, self.is_split)
        raise TypeError(f"Unsupported operand type(s) for -: 'BinNumber' and '{type(other).__name__}'")

    def __mul__(self, other):
        """乘法重载"""
        if isinstance(other, BinNumber):
            result_dec = self.dec_num * other.dec_num
            return BinNumber(result_dec, self.precision, self.symbolic_bit, self.is_split)
        raise TypeError(f"Unsupported operand type(s) for *: 'BinNumber' and '{type(other).__name__}'")

    def __truediv__(self, other):
        """除法重载"""
        if isinstance(other, BinNumber):
            if other.dec_num == 0:
                raise ZeroDivisionError("division by zero")
            result_dec = self.dec_num / other.dec_num
            return BinNumber(result_dec, self.precision, self.symbolic_bit, self.is_split)
        raise TypeError(f"Unsupported operand type(s) for /: 'BinNumber' and '{type(other).__name__}'")


class Bin4SquTex(SquTex, BinNumber):
    """
    二进制的 manim 接口，
    继承于 :class:`~.SquTex` 与 :class:`~.BinNumber` ，

    Notes
    -----

    - 常用于数据结构与二进制转换的演示，
    - 以 :class:`~.BinNumber` 计算 ``bin_num``，再用 :class:`~.SquTex` 逐位成块显示，
    - 构造时把方块样式 kwargs 赋给 :class:`~.Square`（与 :class:`~.SquTex` 相同），
    - 使用 :method:`color_logic` 按符号位 / 分隔符 / 整数位 / 小数点 / 小数位上色，
    - 使用 :method:`update_binary` 在改十进制参数后同步刷新画面，
    - 使用 :method:`show_encoding` 切换原码 / 反码 / 补码显示，
    - 使用 :method:`highlight_bits` 高亮指定下标的位，
    - 单个动画可沿用 :method:`animate_one_by_one`、:method:`change_square`、:method:`change_text`。

    Examples
    --------

    创建并按逻辑上色:

    >>> class Bin4SquTexCreate(Scene):
    >>>     def construct(self):
    >>>         b = Bin4SquTex(-5, 8, 1, True, **typedict["default_type"])
    >>>         self.play(b.animate_one_by_one(FadeIn, scale=1.5))
    >>>         self.wait()

    更新数值并切换补码:

    >>> class Bin4SquTexEncoding(Scene):
    >>>     def construct(self):
    >>>         b = Bin4SquTex(-5, 8, 1, True, **typedict["default_type"])
    >>>         self.add(b)
    >>>         self.wait()
    >>>         self.play(FadeTransform(b.copy(), b.show_encoding("two")))
    >>>         self.wait()
    >>>         self.play(FadeTransform(b.copy(), b.show_encoding("original")))
    >>>         self.wait()

    高亮符号位:

    >>> class Bin4SquTexHighlight(Scene):
    >>>     def construct(self):
    >>>         b = Bin4SquTex(13, 8, 1, True, **typedict["default_type"])
    >>>         self.add(b)
    >>>         self.play(*[Indicate(b[i]) for i in b.sign_indices()])
    >>>         self.wait()

    """

    __version__: str = "1.0.0"

    def __init__(
            self,
            dec_num: int | float | str | None = None,
            precision: int | None = None,
            symbolic_bit: int = 1,
            is_split: bool = False,
            font="",
            buff=0,
            arrange_direction=RIGHT,
            text_type=Text,
            str_need_split=True,
            apply_color_logic=True,
            **kwargs,
    ):
        self._squ_ready = False
        self.apply_color_logic_flag = apply_color_logic

        if dec_num is None:
            self.dec_num = 0
        else:
            self.dec_num = dec_num
        self.precision = precision
        self.symbolic_bit = symbolic_bit
        self.is_split = is_split
        BinNumber.update_binary(self)

        SquTex.__init__(
            self,
            tex=self.bin_num,
            font=font,
            buff=buff,
            arrange_direction=arrange_direction,
            text_type=text_type,
            str_need_split=str_need_split,
            **kwargs,
        )
        self._squ_ready = True
        if self.apply_color_logic_flag:
            self.color_logic()

    def _spawn_same_style(self, dec_num: int | float) -> "Bin4SquTex":
        """用当前样式生成新的 :class:`Bin4SquTex`。"""
        return Bin4SquTex(
            dec_num,
            self.precision,
            self.symbolic_bit,
            self.is_split,
            font=self.font,
            buff=self.buff,
            arrange_direction=self.arrange_direction,
            text_type=self.text_type,
            str_need_split=self.str_need_split,
            apply_color_logic=self.apply_color_logic_flag,
            **self.kwargs,
        )

    def _part_spans(self) -> dict[str, range]:
        """各逻辑段在 ``bin_num`` / SquTex 下标中的区间。"""
        i = 0
        spans: dict[str, range] = {}
        spans["sign"] = range(i, i + len(self._sign))
        i += len(self._sign)
        spans["split"] = range(i, i + len(self._split))
        i += len(self._split)
        spans["int"] = range(i, i + len(self._binary_int))
        i += len(self._binary_int)
        float_bits = self._binary_float
        if float_bits.startswith("."):
            spans["point"] = range(i, i + 1)
            spans["float"] = range(i + 1, i + len(float_bits))
        else:
            spans["point"] = range(i, i)
            spans["float"] = range(i, i + len(float_bits))
        return spans

    def sign_indices(self) -> list[int]:
        return list(self._part_spans()["sign"])

    def split_indices(self) -> list[int]:
        return list(self._part_spans()["split"])

    def int_indices(self) -> list[int]:
        return list(self._part_spans()["int"])

    def point_indices(self) -> list[int]:
        return list(self._part_spans()["point"])

    def float_indices(self) -> list[int]:
        return list(self._part_spans()["float"])

    def color_logic(
            self,
            sign_color=RED,
            int_color=BLUE,
            float_color=GREEN,
            point_color=YELLOW,
            split_color=GREY,
            fill_opacity=None,
            **kwargs,
    ):
        """
        按符号位 / 分隔符 / 整数位 / 小数点 / 小数位上色。
        :return: self
        """
        spans = self._part_spans()
        style = dict(kwargs)
        if fill_opacity is not None:
            style["fill_opacity"] = fill_opacity

        def _paint(indices, color):
            for idx in indices:
                if idx >= len(self):
                    continue
                squ_kw = {"color": color, **style}
                self.change_square(idx, **squ_kw)
                self.change_text(idx, color=color)

        _paint(spans["sign"], sign_color)
        _paint(spans["split"], split_color)
        _paint(spans["int"], int_color)
        _paint(spans["point"], point_color)
        _paint(spans["float"], float_color)
        return self

    def _rebuild_squ(self):
        """按当前 ``bin_num`` 重建方块序列。"""
        self.remove(*list(self.submobjects))
        self.tex = self.bin_num
        if self.str_need_split:
            try:
                self._default_type()
            except IndexError:
                self._without_split_type()
        else:
            self._without_split_type()
        self._construct()
        if self.apply_color_logic_flag:
            self.color_logic()
        return self

    def _sync_text_only(self, text: str):
        """长度不变时只改每位文字；长度变化则整块重建。"""
        if len(text) != len(self):
            self.bin_num = text
            return self._rebuild_squ()
        for i, ch in enumerate(text):
            self.change_word_in_text(i, ch)
        self.tex = text
        self.bin_num = text
        if self.apply_color_logic_flag:
            self.color_logic()
        return self

    def update_binary(self):
        """更新二进制数，并在已构造画面时同步 SquTex。"""
        BinNumber.update_binary(self)
        if self._squ_ready:
            self._rebuild_squ()
        return self

    def standardize(self):
        """将输入的二进制数标准化，并刷新画面。"""
        BinNumber.standardize(self)
        if self._squ_ready:
            self._rebuild_squ()
        return self

    def show_encoding(self, kind: str = "original"):
        """
        切换显示编码。
        :param kind: ``original`` 原码 / ``one`` 反码 / ``two`` 补码
        :return: self
        """
        if kind in ("original", "ori", "raw"):
            BinNumber.update_binary(self)
            text = self.bin_num
        elif kind in ("one", "ones", "ex_one"):
            text = self.ex_one()
        elif kind in ("two", "twos", "ex_two"):
            text = self.ex_two()
        else:
            raise ValueError("kind 须为 original / one / two")
        return self._sync_text_only(text)

    def highlight_bits(
            self,
            *indices: int,
            color=GOLD,
            **kwargs,
    ):
        """
        高亮指定下标的位（方块 + 文字）。
        :return: self
        """
        for i in indices:
            self.change_square(i, color=color, **kwargs)
            self.change_text(i, color=color)
        return self

    def __add__(self, other):
        if isinstance(other, BinNumber):
            return self._spawn_same_style(self.dec_num + other.dec_num)
        raise TypeError(
            "Unsupported operand type(s) for +: 'Bin4SquTex' and '{}'".format(type(other).__name__)
        )

    def __sub__(self, other):
        if isinstance(other, BinNumber):
            return self._spawn_same_style(self.dec_num - other.dec_num)
        raise TypeError(
            f"Unsupported operand type(s) for -: 'Bin4SquTex' and '{type(other).__name__}'"
        )

    def __mul__(self, other):
        if isinstance(other, BinNumber):
            return self._spawn_same_style(self.dec_num * other.dec_num)
        raise TypeError(
            f"Unsupported operand type(s) for *: 'Bin4SquTex' and '{type(other).__name__}'"
        )

    def __truediv__(self, other):
        if isinstance(other, BinNumber):
            if other.dec_num == 0:
                raise ZeroDivisionError("division by zero")
            return self._spawn_same_style(self.dec_num / other.dec_num)
        raise TypeError(
            f"Unsupported operand type(s) for /: 'Bin4SquTex' and '{type(other).__name__}'"
        )


if __name__ == "__main__":
    bin1 = BinNumber(-1, 8, 2, True)
    bin2 = BinNumber(16, 5, 1, True)
    bin3 = bin1 + bin2
    print(bin3)

    b4 = Bin4SquTex(-5, 8, 1, True)
    print(b4.bin_num, len(b4), b4.sign_indices(), b4.int_indices())
    b4.show_encoding("two")
    print("two:", b4.bin_num)
    b4.show_encoding("original")
    print("ori:", b4.bin_num)
