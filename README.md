# rainbow_yu🐋✨
在manim基础上进行的动画改进

---

# basic_unit

---

## squ_tex.py
包含两个类 `SquTex` 和 `SquTexSlide`

---

### SquTex

![squ_tex](empty_url)

数据块， 继承于 :class:`~.VGroup` ，
- 常用于数据结构的演示和二进制编码的演示，
- 将方块和数字整合在一起，支持统一的动画和单个动画，
- :param:`distance` 成员记录了第一次构造数据间的间距
- 单个动画使用 :method:`animate_one_by_one` 将动画编为一个组
- 在创建数据块时，把所有的可变参数 kwargs 赋给了 :class:`~.Square` 类。
- 如果需要改变其他参数，使用 :method:`change_square` 以及 :method:`change_text`，
- 但要注意使用 :method:`change_text` 时会将原对象的层次改变。
- 使用 :method:`add_bracket` 将数据块中所有负数的数字都加上括号

使用示例：
1. 创建数据块:

```python
from manim import *
from yty_manim.basic_unit.squ_tex import SquTex

class TestSqu(Scene):
    def construct(self):
        t = SquTex("yty - rainbow鱼")
        self.play(t.animate_one_by_one(FadeIn , scale=1.5))
        self.wait()
```