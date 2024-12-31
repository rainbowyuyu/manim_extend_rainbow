# rainbow_yu manim_extend.basic_unit.dec_bin 🐋✨
# 二进制基本的类

from yty_manim.basic_unit.squ_tex import *


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

    __version__: str = "1.1.6"

    # 参数
    dec_num: float | int | str
    precision: int | None = None
    symbolic_bit: int = 1
    is_split: bool = False
    bin_num: str = ""

    # 保留文字
    _sign = ""
    _split = ""
    _binary_int = ""
    _binary_float = ""

    def __init__(
            self,
            dec_num: int | float | str | None = None,
            precision=precision,
            symbolic_bit=symbolic_bit,
            is_split=is_split,
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
        self._binary_int = self._set_precision() + self._set_binary_int()
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


class Bin4SquTex(BinNumber, SquTexSlide):
    """
    二进制的manim接口
    继承于 :class:`~.BinNumber` 和 :class:`~.SquTexSlide`，

    Notes
    -----

    - 常用于数据结构的演示和二进制转换的演示，
    -  :method:``

    Examples
    --------
"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.change_color()

    def color_logic(self):
        pass


if __name__ == '__main__':
    bin1 = BinNumber(-1, 8, 2, True)
    bin2 = BinNumber(16, 5, 1, True)
    bin3 = bin1 + bin2
    print(bin3)
